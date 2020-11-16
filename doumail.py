import util
import captcha_util
import group_get
import review
from RespGen import *
from config import *
from pyquery import PyQuery as pq
import os
import json
import time
import logging
logging.basicConfig(filename='doumail.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

def sent_doumail(session,user_id,content):
    # 向用户发送豆邮
    url='https://www.douban.com/j/doumail/send'
    user_url='https://www.douban.com/doumail/%s/'%user_id
    pic_url, pic_id = captcha_util.get_verify_code_pic_doumail(session, user_url)
    verify_code = ""
    # pic_url, pic_id="",""
    if len(pic_url):
        retry_count = 0
        while retry_count < 3:
            pic_path = captcha_util.save_pic_to_disk(pic_url, session)
            verify_code = captcha_util.get_word_in_pic(pic_path)
            os.remove(pic_path)
            retry_count = retry_count + 1
            time.sleep(5)
            if verify_code == '': # 识别不出的话重试
                pic_url, pic_id = captcha_util.get_verify_code_pic_doumail(session, user_url)
                verify_code = ""
            else:
                break
        if retry_count == 3:
            util.email_notify()
            raise RuntimeError('Captcha failed')

    param_dict = {
        "ck": util.get_ck_from_cookies(session),
        'to': user_id,
        "m_text": content,
        "m_image":'',
        "captcha-solution": verify_code,
        "captcha-id": pic_id
        #'m_submit': '%E5%A5%BD%E4%BA%86%EF%BC%8C%E5%AF%84%E5%87%BA%E5%8E%BB'#encoded '好了，寄出去'
    }
    print(param_dict)
    response = session.post(url, param_dict, cookies=util.loadCookies())
    print(response)
    logging.info(str(param_dict) + str(response))

def self_intro(session,user_id):
    # 给非双关用户发消息，需要先打招呼，对方回复后才能聊天
    url='https://www.douban.com/j/doumail/selfintro'
    param_dict = {
        'to_user_id': user_id,
        "ck": util.get_ck_from_cookies(session)
    }
    print(param_dict)
    response = session.post(url, param_dict)
    print(response)
    logging.info(str(param_dict) + str(response))

def get_all_doumail(session,newonly=False,n=40,ignore=0):
    # 获取豆邮界面的所有消息预览，长消息会被截断，图片会显示为 [图片]
    start=0
    result = []  # each is a dict of time,sender,preview,link
    pages=(n+19)//20
    for p in range(pages):
        url='https://www.douban.com/doumail/?start='+str(start)
        start+=20
        doc = pq(url, headers=session.headers, cookies=util.getCookiesFromSession(session))
        for i in doc('.title').items():
            preview = i('a').text()  # if img, preview will be '[图片]'
            sender = i('.from').text()  # if N new msg, will be '{username}（N）'
            possible_num = sender.split('（')[-1].strip('）')
            if newonly and not possible_num.isdigit():
                continue
            sender = sender.split('（')[0]
            if newonly and not possible_num.isdigit():
                continue
            # if newonly and'🤖' in preview:
            #   continue
            send_time = i('.time').text()
            link = i('a').attr("href")
            user_id = link.split('/')[-2]
            result.append({'time':send_time,'username':sender,'user_id':user_id,'preview':preview,'link':link})
    n=min(n,len(result))
    return result[ignore:n]

def get_doumail_from_user(session,user_id,n=5,user_only=True):
    # 获取与某用户的全部对话
    url='https://www.douban.com/doumail/'+user_id+'/'
    doc = pq(url, headers=session.headers, cookies=util.getCookiesFromSession(session))
    msgs = []  # each is a dict of time,sender,preview,link
    title=doc('h1').text()
    if title=='我的豆邮':
        return {'user_id':user_id,'username':None,'userpage':None,'msgs':None}
    username=title.strip('与').strip('的豆邮')
    userpage='https://www.douban.com/people/'+user_id+'/'
    for i in doc('.chat').items():
        senderpage=i('.sender')('a').attr("href")
        senderid=senderpage.split('/')[-2]
        if user_only==False or senderid==user_id: # else was sent by myself
            time = i('.time').text()
            content = i('.content')
            text=content('p').text()
            if not text:
                img=content('.cont-pic')('img').attr("src")
            else:
                img=''
            msgs.append({'senderid':senderid,'time': time,'text': text, 'img': img})
    n=min(n,len(msgs))
    return {'user_id':user_id,'username':username,'userpage':userpage,'msgs':msgs[-n:]}

def process_new_doumail(session,group_id,newonly=True,force_range=[]):
    # 处理用户消息
    with open('resources/member-%s.json' % group_id, 'r') as f:
        member_dict = json.load(f)
    with open('applications/wait_to_reply.json', 'r') as f:
        wait_to_reply = json.load(f)
    with open('applications/replied_nonmember.json', 'r') as f:
        replied_nonmember = json.load(f)
    Reply = RespGen()
    if not force_range:
        doumails=get_all_doumail(session,newonly=newonly)
    else:
        doumails=get_all_doumail(session, newonly=newonly, n=force_range[0], ignore=force_range[1])
    for mail in doumails:
        #{'time':time,'sender':sender,'preview':preview,'link':link}
        print(mail)
        if mail['user_id'] in member_dict or group_get.check_member_in_group(group_id, mail['user_id']) :
            # 如果用户为组员
            if '取消帮助审核' in mail['preview']:
                with open('applications/reviewer.txt', 'r') as f:
                    reviewers = f.readlines()  # ids
                reviewers.remove(mail['user_id'] + '\n')
                with open('applications/reviewer.txt', 'w') as f:
                    f.writelines(reviewers)

                with open('applications/canceled_reviewer.txt', 'r') as f:
                    no_reviewers = f.readlines()  # ids
                no_reviewers.append(mail['user_id'] + '\n')
                with open('applications/canceled_reviewer.txt', 'w') as f:
                    f.writelines(no_reviewers)

                content = '🤖取消成功'
            elif '此用户申请' in mail['preview']:
                text = mail['preview']
                text = text.replace('：', ':')
                try:
                    opinion, user_id = text.split('此用户申请:')
                except:
                    text = get_doumail_from_user(session, mail['user_id'], n=2, user_only=False)['msgs'][0]['text']
                    text = text.replace('：', ':')
                    opinion, user_id = text.split('此用户申请:')
                if opinion == '同意':
                    review.add_review(mail['user_id'], user_id, approve=1)
                else:
                    review.add_review(mail['user_id'], user_id, approve=0)
                content = '🤖审核成功'
            elif '顶帖' in mail['preview']:
                text=mail['preview']
                #print('full text:',text)
                try:
                    _,url,hours=text.split(' ')
                    hours=int(hours)
                    if hours>6:
                        iter=int(hours*60//2)
                        with open('resources/dd_urls.json', 'r') as f:
                            dd_url = json.load(f)
                        dd_url[url]=iter
                        with open('resources/dd_urls.json', 'w') as f:
                            json.dump(dd_url,f)
                        content='🤖已记录'
                    else:
                        content = '🤖间隔小时不能小于6，如有需求请私信开发者'
                except:
                    content = '🤖无法识别，请输入"顶帖 帖子id(网址最后的数字) 间隔小时数",不要有多余的空格'
            else:
                # 非特定关键词消息，随机回复
                content=''
                if '?' in mail['preview'] or '？' in mail['preview']\
                        or random.choice([0,1,2])==0:
                    content = '🤖' + Reply.getResp_AI(mail['preview'].strip('.').replace('机器人名字','菲菲'), username=mail['username'])
                if not content or '无法理解' in content:
                    content = '🤖'+Reply.getResp('机器人', username=mail['username'])  # + ' \n -- Hi,这是一条自动回复 '
            util.random_sleep(0, 15, 'wait before reply')
            sent_doumail(session, mail['user_id'], content)
            util.random_sleep(60, 90, 'processed message')
        else: # 非组员
            if '申请入组' in mail['preview']:
                content = '🤖小组自动审核方式：先发送文字、截图等能证明你符合入组要求的资料，最后发送"申请入组"四个字。如已发送好，将随机邀请多名组员审核，请耐心等待'
                sent_doumail(session, mail['user_id'], content)
                review.collect_review_content(session, mail['user_id'])
                util.random_sleep(60, 90, 'processed message')
            elif mail['user_id'] not in replied_nonmember: #尚未回复过消息
                content = '🤖小组自动审核方式：先发送文字、截图等能证明你符合入组要求的资料，最后发送"申请入组"四个字'
                sent_doumail(session, mail['user_id'], content)
                replied_nonmember.append(mail['user_id'])
                with open('applications/replied_nonmember.json', 'w') as f:
                    json.dump(replied_nonmember, f)
                util.random_sleep(60, 90, 'processed message')
            else: # 已经回复过消息
                if mail['user_id'] in wait_to_reply:
                    wait_to_reply.remove(mail['user_id'])
                    with open('resources/wait_to_reply.json', 'w') as f:
                        json.dump(wait_to_reply, f)
                content = '🤖消息已收到，记得发送"申请入组"四个字开始自动审核'
                sent_doumail(session, mail['user_id'], content)
                util.random_sleep(60, 90, 'processed message')

        logging.info(mail['preview'] +' sent by id ='+ mail['user_id'])
    return len(doumails)

if __name__ == '__main__':
    import RequestWrapper
    req_wrapper = RequestWrapper.ReqWrapper()
    s = req_wrapper.session
    s.headers.update({
        'Host': 'www.douban.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    s.cookies.update(util.loadCookies())
    #sent_doumail(s,'','testtest')
    process_new_doumail(s,group_id,newonly=False,force_range=[5,0])
