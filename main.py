import RequestWrapper
from group_get import get_group_posts, get_comment
from group_post import reply_to_post, collect_to_list, dd_post
import util
import RespGen
import doumail
from config import *
from datetime import datetime
import random
import time
import logging
logging.basicConfig(filename='main.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def initial_session():
    req_wrapper = RequestWrapper.ReqWrapper()
    s = req_wrapper.session
    s.headers.update({
        'Host': 'www.douban.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
    })
    s.cookies.update(util.loadCookies())
    return s


def main(maxcount=10000):
    Reply = RespGen.RespGen()

    with open('resources/post_history.txt', 'r') as f:
        history = f.readlines()
    history = set([h.strip('\n') for h in history])
    with open('resources/doulist_history.txt', 'r') as f:
        doulist_history = f.readlines()
    doulist_history = set([h.strip('\n') for h in doulist_history])

    count = 0
    not_found_count = -1
    force_reply = False
    use_api = True
    read_post_failed = 0

    while (count < maxcount):
        found = 0
        count += 1
        # initial session every 200 iterations
        if count % 200 == 1:
            s = initial_session()

        # get new posts in this group
        try:
            posts = get_group_posts(group_id, api=use_api)
        except:
            # if failed, change the way of getting posts
            # if failed 10 times, send an email notification and raise an error
            read_post_failed += 1
            if read_post_failed == 10:
                util.email_notify()
                raise RuntimeError
            use_api = not use_api
            print('read post failed')
            # time.sleep(300)
            continue

        # dd post, make certain posts to the top
        dd_post(s, count)

        # collect user's comments every 60 iteration
        if count % 60 == 1:
            Reply = RespGen.RespGen()
            collect_comments = True
        else:
            collect_comments = False
        if collect_comments:
            reply_list = get_comment(comment_collect_id)
            for content in reply_list:
                for splitter in ['[投稿]', '［投稿］', '【投稿】']:
                    if splitter in content:
                        content = content.split(splitter)
                        for c in content:
                            c = c.replace('\n', ' ').strip(' ')
                            if not c:
                                continue
                            # check if content already exists
                            new = True
                            for p in ['', '{no}', '{less}']:  # prefix=['','{no}','{less}']
                                if p + c in Reply.random:
                                    new = False
                                    break
                            # if not existing, save
                            if new:
                                c = c.replace('：', ':')
                                print('new content: ', c)
                                if ':' in c:
                                    with open('resources/reply_keywords.txt', 'a') as f:
                                        f.write('\n' + c)
                                else:
                                    Reply.random.append(c)
                                    with open('resources/reply_random.txt', 'a') as f:
                                        f.write('\n' + c)
                        break

        # reply to new posts
        post_failed = 0
        for i in range(len(posts)):
            up_post, title, username = posts[i]['link'], posts[i]['title'], posts[i]['username']
            
            # if this post contains forbidden words, ignore it
            if any(x in title for x in forbidwords):
                continue

            for c in collectwords:
                if c in title:
                    topic_id = up_post.split('/')[-2]
                    if topic_id not in doulist_history:
                        doulist_history.add(topic_id)
                        with open('resources/doulist_history.txt', 'a') as f:
                            f.write('\n' + topic_id)
                        collect_to_list(s, mydoulist_id, topic_id)
                        util.flush_cookies(s)
                        sleept = random.choice(list(range(5, 25)))
                        print('collected topic id=', topic_id, '｜ sleep', sleept)
                        time.sleep(sleept)
                        break

            if force_reply or up_post not in history:
                if force_reply: # currently not used
                    i = random.choice(list(range(10, len(posts))))
                    up_post, title, username = posts[i]['link'], posts[i]['title'], posts[i]['username']
                    force_reply = False
                found += 1
                print('\nget new post: ', up_post)
                # up_post='https://www.douban.com/group/topic/198309101/'
                # print(title)
                reply_content = Reply.getResp(title, username=username)
                # print(reply_content)
                # reply_content += '\n -- bot试运行中'
                try:
                    reply_to_post(s, up_post, reply_content)  # + time.asctime(time.localtime()))
                    history.add(up_post)
                    with open('resources/post_history.txt', 'a') as f:
                        f.write('\n' + up_post)
                except:
                    print('post failed, reason unknown')
                    post_failed += 1
                    if post_failed > 2:
                        util.email_notify()
                        return
                    else:
                        continue
                util.flush_cookies(s)
                if random.choice(list(range(30))) == 0:
                    sleept = random.choice(list(range(300)))
                else:
                    sleept = random.choice(list(range(100, 150)))
                print('sleep', sleept)
                time.sleep(sleept)

        if found == 0:  # if no new post
            not_found_count += 1
            if not_found_count > 10: # if no new post in 10 iterations, sleep longer
                # not_found_count=0
                # force_reply=True # still reply to a random post
                sleept = random.choice(list(range(300, 600)))
            else:
                sleept = random.choice(list(range(60, 120)))
            print(count, 'no new posts, sleep', sleept, '    |', datetime.now())
            logging.info(str(count) + 'no new posts, sleep' + str(sleept))
        else:
            not_found_count = 0
            sleept = random.choice(list(range(60, 120)))
            print(count, 'found new posts, sleep', sleept, '    |', datetime.now())
            logging.info(str(count) + 'found new posts, sleep' + str(sleept))
        time.sleep(sleept)

        # process doumails every 10 iterations
        if count % 10 == 0:
            doumail.process_new_doumail(s, group_id)
            util.flush_cookies(s)

    util.email_notify('Execution completed')


if __name__ == '__main__':
    main(maxcount=10000)
