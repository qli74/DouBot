import util
import captcha_util
from config import *
import os
from pyquery import PyQuery as pq
import json
import logging
logging.basicConfig(filename='post.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def reply_to_post(session, url, content, topic_id=None):
    # 回复帖子
    if not topic_id:
        url = url + 'add_comment'
    else:
        url = topic_base_url + topic_id + '/add_comment'
    # https://www.douban.com/group/topic/198628115/
    # reply_url='https://api.douban.com/v2/group/topic/'+post_id+'/comments'
    pic_url, pic_id = captcha_util.get_verify_code_pic(session, url[:-12])
    verify_code = ""
    # pic_url, pic_id="",""
    post_retry_count = 3
    while post_retry_count > 0:
        try:
            if len(pic_url):
                retry_count = 0
                while verify_code == '' and retry_count < 2:  # 识别不出的话重试
                    pic_path = captcha_util.save_pic_to_disk(pic_url, session)
                    verify_code = captcha_util.get_word_in_pic(pic_path)
                    os.remove(pic_path)
                    retry_count = retry_count + 1
                    time.sleep(2)
            reply_dict = {
                "ck": util.get_ck_from_cookies(session),
                'rv_comment': content,
                "captcha-solution": verify_code,
                "captcha-id": pic_id,
                'start': 0,
                'submit_btn': '发送'
            }
            print(reply_dict)
            response = session.post(url, reply_dict)
            print(response)
            logging.info(str(reply_dict) + str(response))
            if response.status_code > 300:
                raise RuntimeError('post failed, status', response.status_code)
            post_retry_count = -100
        except:
            post_retry_count -= 1 # 发帖失败，重试
    if post_retry_count == 0:
        raise RuntimeError
    # print('reply: ' + url)
    # print(r.text)


def like_post(session, post_id):
    # 点赞功能，api目前无法使用
    reply_url = 'https://www.douban.com/group/topic/' + post_id + '/like'
    # reply_url='http://api.douban.com/v2/group/topic/'+post_id+'/like'
    # reply_url='http://m.douban.com/rexxar/api/v2/group/topic/'+post_id+'/react'
    # pic_url, pic_id = DouUtil.get_verify_code_pic(session, reply_url)
    verify_code = ""
    pic_url, pic_id = "", ""
    if len(pic_url):
        retry_count = 0
        while verify_code == '' and retry_count < 2:  # 识别不出的话重试
            pic_path = captcha_util.save_pic_to_disk(pic_url, session)
            verify_code = captcha_util.get_word_in_pic(pic_path)
            os.remove(pic_path)
            retry_count = retry_count + 1
            time.sleep(2)
    reply_dict = {
        # 'MIME Type': 'application/x-www-form-urlencoded',
        'reaction_type': '1',
        "ck": util.get_ck_from_cookies(session)
    }
    print(reply_dict)
    response = requests.get(reply_url, cookies=getCookiesFromSession(session))
    print(response)


def collect_to_list(session, listid, topicid, comment=''):
    # 收藏帖子到豆列
    url = 'https://www.douban.com/j/doulist/' + listid + '/additem'
    param_dict = {
        # 'MIME Type': 'application/x-www-form-urlencoded',
        'sid': topicid,
        'skind': '1013',
        "ck": util.get_ck_from_cookies(session),
        'comment': comment,
        'sync_to_mb': ''
        # "captcha-solution": verify_code,
        # "captcha-id": pic_id
    }
    response = session.post(url, param_dict)
    # print(response)


def post_in_group(session, group_id, title, content):
    # 发布新帖子
    publish_url = 'https://www.douban.com/j/group/topic/publish'
    topic_new_url = 'https://www.douban.com/group/%s/new_topic' % group_id
    pic_url, pic_id = captcha_util.get_verify_code_pic(session, topic_new_url)
    verify_code = ""
    # pic_url, pic_id="",""
    if len(pic_url):
        pic_path = captcha_util.save_pic_to_disk(pic_url)
        verify_code = captcha_util.get_word_in_pic(pic_path)
    topic_dict = {
        "ck": util.get_ck_from_cookies(session),
        "title": title,
        "content": r"{'blocks':[{'key':'893dl','text':'" + content.strip()
                   + '''','type':'unstyled','depth':0,'inlineStyleRanges':[],'entityRanges':[],data':{'page':0}}],'entityMap':{}}''',
        "captcha-solution": verify_code,
        "captcha-id": pic_id,
        "group_id": 696739
    }

    print(topic_dict)
    r = session.post(publish_url, topic_dict)
    print(r.text)


def copy_post(session, post_url, to_group_id):
    # 搬运帖子
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.117 Safari/537.36'}
    doc = pq(post_url, headers=header)
    title = doc('.article>h1').text()
    print(title)
    post_in_group(session, to_group_id, title, post_url)


def dd_post(session, current):
    # 顶帖
    with open('resources/dd_urls.json', 'r') as f:
        dd_url = json.load(f)
    count = 0
    for topic_id, interval in dd_url.items():
        if current % interval == 0:
            count += 1
            reply_to_post(session, '', 'dd', topic_id=topic_id)
            util.random_sleep(60, 120, 'dd post ' + topic_id)
    return count


if __name__ == '__main__':
    import RequestWrapper
    from util import *

    req_wrapper = RequestWrapper.ReqWrapper()
    s = req_wrapper.session
    s.headers.update({
        'Host': 'www.douban.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
    })
    s.cookies.update(loadCookies())
    reply_to_post(s, 'https://www.douban.com/group/topic/198331913/', 'test')
    # reply_to_post(s, '', 'test')
    # collect_to_list(s, '','')
    # DouUtil.flush_cookies(s)
