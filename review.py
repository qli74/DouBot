import util
import group_get
import doumail
import RequestWrapper
from config import *
from pyquery import PyQuery as pq
import json
import os
import random
import time
import logging
logging.basicConfig(filename='review.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def ask_for_review(session, review_content, application_content, group_name, n=5, testid=''):
    # 随机邀请一些组员帮助审核某用户入组申请
    with open('applications/reviewer.txt', 'r') as f:
        reviewers = f.readlines()  # ids
    reviewers = [r.strip('\n') for r in reviewers]
    user_id = review_content['user_id']
    username = review_content['username']
    userpage = review_content['userpage']
    msgs = review_content['msgs']
    invited_ids = []
    if testid:
        reviewers = [testid]
    for i in range(min(len(reviewers), n)):
        invite_id = random.choice(reviewers)
        while invite_id in invited_ids:
            invite_id = random.choice(reviewers)
        content = '🤖组员您好，邀请您帮助审核用户"%s"进入"%s"小组的申请。用户主页：%s。以下为申请资料：\n\n' % (username, group_name, userpage)
        content += '入组理由：' + application_content + '\n'
        if len(msgs) > 8:
            msgs = msgs[-8:]
        for msg in msgs:
            if msg['text']:
                content += '文字内容：' + msg['text'] + '\n'
            else:
                content += '图片内容：' + msg['img'] + '\n'
        content += '\n如果同意入组，请复制并发送"同意此用户申请:%s"' % (user_id)
        content += '\n如果拒绝入组，请复制并发送"拒绝此用户申请:%s"' % (user_id)
        content += '\n如果不想再收到此消息，请复制并发送"取消帮助审核"'
        doumail.sent_doumail(session, invite_id, content)
        invited_ids.append(invite_id)
        sleept = random.choice(list(range(40, 80)))
        print('已邀请用户%s审核%s，sleep' % (invite_id, user_id), sleept)
        time.sleep(sleept)
    with open('applications/wait_to_review.json', 'r') as f:
        wait_to_review = json.load(f)
    wait_to_review[user_id]['invited'] = True
    wait_to_review[user_id]['invited_ids'] = invited_ids
    with open('applications/wait_to_review.json', 'w') as f:
        json.dump(wait_to_review, f)
    return


def collect_review_content(session, user_id, n=6):
    # 收集待入组用户的最近豆邮作为申请内容
    contents = doumail.get_doumail_from_user(session, user_id, n=n)
    with open('applications/review_content/%s.json' % (user_id), 'w') as f:
        json.dump(contents, f)
    review_status = {'invited': False, 'invited_ids': [], 'reviews': {}, 'passed': False,
                     'username': contents['username'], 'userpage': contents['userpage']}

    if os.path.isfile('applications/wait_to_review.json'):
        with open('applications/wait_to_review.json', 'r') as f:
            wait_to_review = json.load(f)
        wait_to_review[user_id] = review_status
    else:
        wait_to_review = {user_id: review_status}

    with open('applications/wait_to_review.json', 'w') as f:
        json.dump(wait_to_review, f)

    return


def add_review(reviewer_id, user_id, approve=0):
    # 新增对该用户的入组意见，0为不同意，1为同意
    with open('applications/wait_to_review.json', 'r') as f:
        wait_to_review = json.load(f)
    wait_to_review[user_id]['reviews'][reviewer_id] = approve
    with open('applications/wait_to_review.json', 'w') as f:
        json.dump(wait_to_review, f)
    return


def accept_user(session, groupid, requestid):
    # 通过入组申请
    url = 'https://www.douban.com/j/group/' + groupid + '/requests/accept'
    reply_dict = {
        'MIME Type': 'application/x-www-form-urlencoded',
        'req_item': requestid,
        "ck": util.get_ck_from_cookies(session)
    }
    print(reply_dict)
    response = session.post(url, reply_dict, cookies=util.loadCookies())
    print(response)


def reject_user(session, groupid, requestid):
    # 拒绝入组申请
    url = 'https://www.douban.com/j/group/' + groupid + '/requests/reject'
    reply_dict = {
        'MIME Type': 'application/x-www-form-urlencoded',
        'req_item': requestid,
        "ck": util.get_ck_from_cookies(session)
    }
    print(reply_dict)
    response = session.post(url, reply_dict, cookies=util.loadCookies())
    print(response)


def get_all_applied_user(session,groupid):
    # 获取待处理的入组申请
    url = 'https://www.douban.com/group/' + groupid + '/requests/applied'
    print(url)
    doc = pq(url, headers=session.headers, cookies=util.loadCookies())
    user_request_dict = {}
    li = doc('.group-request-list')
    request_id, user_id, content = [], [], []
    for i in li('input'):
        request_id.append(pq(i).attr("value"))
    for i in li('.douban-home-page'):
        user_id.append(pq(i).attr("href").split('/')[-2])
    for i in li('.inq'):
        content.append(pq(i).text())
    for k in range(len(user_id)):
        print(user_id[k], request_id[k], content[k])
        user_request_dict[user_id[k]] = {'request_id': request_id[k], 'content': content[k]}
    with open('applications/user_request_dict.json', 'w') as f:
        json.dump(user_request_dict, f)
    return len(user_request_dict)


def get_all_reviewer(session, topic_id, self_intro=True,page=1):
    # 获取在报名帖中报名参与审核的用户id
    # 如果self_intro=True, 向新报名用户打招呼，便于以后发送私信
    user_id_list = group_get.get_comment(topic_id, 'user_id', page=page)
    with open('applications/reviewer.txt', 'r') as f:
        reviewers = f.readlines()  # ids
    reviewers = [r.strip('\n') for r in reviewers]
    with open('applications/canceled_reviewer.txt', 'r') as f:
        no_reviewers = f.readlines()  # ids
    no_reviewers = [r.strip('\n') for r in no_reviewers]
    count = 0
    for user_id in user_id_list:
        if user_id not in reviewers and user_id not in no_reviewers:
            count += 1
            if self_intro:
                doumail.self_intro(session, user_id)
                util.random_sleep(5, 15, 'self intro')
            reviewers.append(user_id)
    reviewers = list(set(reviewers))
    reviewers = [r + '\n' for r in reviewers]
    with open('applications/reviewer.txt', 'w') as f:
        f.writelines(reviewers)
    return count


def review_all(session, group_name, group_id, admin_ids, review_thre=3, verify_members=False, notify_admin=False):
    # 处理所有入组申请
    if os.path.isfile('applications/wait_to_review.json'):
        with open('applications/wait_to_review.json', 'r') as f:
            wait_to_review = json.load(f)
    else:
        return
    with open('applications/user_request_dict.json', 'r') as f:
        user_request_dict = json.load(f)
    with open('applications/wait_to_reply.json', 'r') as f:
        wait_to_reply = json.load(f)
    with open('applications/member-%s.json' % group_id, 'r') as f:
        member_dict = json.load(f)
    with open('applications/replied_nonmember.json', 'r') as f:
        replied_nonmember = json.load(f)

    if verify_members:
        #检查待处理的入组申请是否已经被（其他管理员）处理过
        #或者用户是否已经在组内
        keys = list(wait_to_review.keys())
        for user_id in keys:
            if user_id not in user_request_dict \
                    or user_id in member_dict \
                    or group_get.check_member_in_group(group_id, user_id):
                del wait_to_review[user_id]
            else:
                wait_to_review[user_id]['passed'] = False
        with open('applications/wait_to_review.json', 'w') as f:
            json.dump(wait_to_review, f)

        for user_id in wait_to_reply:
            if user_id not in user_request_dict \
                    or user_id in member_dict \
                    or group_get.check_member_in_group(group_id, user_id):
                wait_to_reply.remove(user_id)
        with open('applications/wait_to_reply.json', 'w') as f:
            json.dump(wait_to_reply, f)

    count = 0
    for user_id in user_request_dict.keys():
        if group_get.check_member_in_group(group_id, user_id):
            continue
        if user_id not in wait_to_review:
            if user_id not in replied_nonmember and user_id not in wait_to_reply:
                # if not reviewed, not replied, and not self-intro
                # self intro and put in wait_to_reply list
                # after user replied, will reply and put in 'replied_nonmember' list in process_new_doumail function
                doumail.self_intro(session, user_id)
                util.random_sleep(5, 15, 'self intro')
                wait_to_reply.append(user_id)
                with open('applications/wait_to_reply.json', 'w') as f:
                    json.dump(wait_to_reply, f)
            continue
        # check user status
        user = wait_to_review[user_id]
        if user['passed']:
            continue
        if user['invited'] == False:
            with open('applications/review_content/%s.json' % user_id, 'r') as f:
                review_content = json.load(f)
            ask_for_review(session, review_content, user_request_dict[user_id]['content'], group_name, n=6)
            count += 1
        else:
            # waiting reviewer's opinions
            reviews = list(user['reviews'].values())
            positive_count = sum([1 for r in reviews if r > 0])
            negative_count = len(reviews) - positive_count
            if positive_count >= review_thre:  # notify admin to approve this user
                content = '已有%s同意,%s拒绝此用户入组申请：\n%s \n用户主页:%s' % (
                    str(positive_count), str(negative_count), user['username'], user['userpage'])
                if notify_admin:
                    for admin in admin_ids:
                        doumail.sent_doumail(session, admin, content)
                        sleept = random.choice(list(range(40, 80)))
                        print('已通知管理员%s同意%s申请，sleep' % (admin, user_id), sleept)
                        time.sleep(sleept)
                else:
                    print(content)
                    accept_user(session, group_id, requestid=user_request_dict[user_id]['request_id'])
                    sleept = random.choice(list(range(20, 40)))
                    print('已同意%s申请，sleep' % (user_id), sleept)
                    time.sleep(sleept)
            elif negative_count >= review_thre:  # notify admin to approve this user
                content = '已有%s同意,%s拒绝此用户入组申请：\n%s \n用户主页:%s' % (
                    str(positive_count), str(negative_count), user['username'], user['userpage'])
                if notify_admin:
                    for admin in admin_ids:
                        doumail.sent_doumail(session, admin, content)
                        sleept = random.choice(list(range(40, 80)))
                        print('已通知管理员%s拒绝%s申请，sleep' % (admin, user_id), sleept)
                        time.sleep(sleept)
                else:
                    print(content)
                    reject_user(session, group_id, requestid=user_request_dict[user_id]['request_id'])
                    sleept = random.choice(list(range(20, 40)))
                    print('已拒绝%s申请，sleep' % (user_id), sleept)
                    time.sleep(sleept)
            util.flush_cookies(session)
    return count


def main_review(session):
    s = session
    for count in range(1, 100000):
        print('iteration', count)
        if count % 1000 == -1:
            group_get.get_group_members(group_id)
            util.random_sleep(120, 240, 'checked members')
        elif count % 100 == -1:
            if get_all_reviewer(s, reviewer_topic_id):
                util.random_sleep(120, 240, 'got reviewers')
        if count % 10 == -1:
            if get_all_applied_user(s,group_id):
                util.random_sleep(30, 60, 'got applications')
                if review_all(s, group_name, group_id, [], review_thre=2, verify_members=True):
                    util.random_sleep(90, 180, 'reviewed requests')
        else:
            count = doumail.process_new_doumail(s, group_id)
            util.flush_cookies(s)
            if count == 0:
                util.random_sleep(300, 600, 'no new message to process')
            else:
                util.random_sleep(180, 300, 'processed all %s new messages' % str(count))
        if random.choice(list(range(10)))==0:
            util.random_sleep(0, 3600, 'rest')
        util.flush_cookies(s)


if __name__ == '__main__':
    req_wrapper = RequestWrapper.ReqWrapper()
    s = req_wrapper.session
    s.headers.update({
        'Host': 'www.douban.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Accept': 'text/plain, */*; q=0.01,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    s.cookies.update(util.loadCookies())
    #reviewer_topic_id = ''
    #get_all_reviewer(s, reviewer_topic_id, self_intro=False,page=2)
    main_review(s)


