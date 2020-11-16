from pyquery import PyQuery as pq
import time
import json
import random
import requests
import util
from config import *


def get_group_members(group_id):
    # 记录小组所有成员id
    member_dict = {}
    start_count = 0
    total_count = float('inf')
    while start_count <= total_count:
        group_member_url = group_base_url + group_id + '/members?start=%d' % start_count
        hearder = {
            'User-Agent': random.choice(my_headers)}
        doc = pq(group_member_url, headers=hearder)
        if total_count == float('inf'):
            total_count = int(doc('.count').text().strip('(共').strip('人)'))
            print('total:', total_count)
        start_count += 35
        for i in doc('.name').items():
            name = i('a').text()
            id = i('a').attr("href").split('/')[-2]
            member_dict[id] = name
        print('done', start_count, 'sleep 5')
        time.sleep(5)
    with open('applications/member-%s.json' % group_id, 'w') as f:
        json.dump(member_dict, f)


def check_member_in_group(group_id, user_id):
    # 检查用户是否为组员
    url = 'https://www.douban.com/group/' + group_id + '/member_search?q=' + user_id
    hearder = {
        'User-Agent': random.choice(my_headers)}
    doc = pq(url, headers=hearder)
    util.random_sleep(0, 5, 'checked if %s in group' % user_id)
    if '没有包含' in doc('.sbjtd').text():
        return False
    else:
        return True


def get_random_proxy():
    """
    get random proxy from proxypool
    :return: proxy
    """
    # 获取一个随机proxy，不必须使用
    selected = requests.get(proxypool_url).text.strip()
    proxies = {protocol: 'http://' + selected for protocol in ('http', 'https')}
    print(proxies)
    return proxies


def get_group_posts(group_id, api=True):
    # 获取小组帖子，可以使用豆瓣api或者直接爬取
    if api:
        post_list = []
        group_post_url = 'https://api.douban.com/v2/group/' + group_id + '/topics'
        resp = requests.get(url=group_post_url)  # ,proxies=get_random_proxy())
        data = resp.json()
        for topic in data['topics']:
            post_list += [{
                'title': topic['title'],
                'link': topic['alt'],
                'username': topic['author']['name'],
                'userid': topic['author']['id'],
                'author_link': topic['author']['alt'],
                'reply_count': topic['comments_count'],
                'time': topic['created'],
                'content': topic['content']
            }]
        print('finish:' + group_post_url)
        return post_list
    else:
        post_list = []
        start = 0
        while start < 20:
            group_post_url = group_base_url + group_id + '/discussion?start=%d' % start
            hearder = {'user-agent': random.choice(my_headers)}
            doc = pq(group_post_url, headers=hearder)
            start += 25
            post_list += [{
                'title': i('a').text(),
                'link': i('a').attr('href'),
                'username': i.siblings().eq(0)('a').text(),
                'author_link': i.siblings().eq(0)('a').attr('href'),
                'reply_count': '0' + i.siblings().eq(1).text(),
                'time': i.siblings().eq(2).text()
            } for i in doc('td.title').items()]
            print('finish:' + group_post_url)
            time.sleep(2)
        return post_list


def get_comment(topic_id, attr='text', page=1):
    # 获取帖子评论内容
    # post_url = group_base_url + 'topic/%s/' % post_id
    group_post_url = 'https://api.douban.com/v2/group/topic/' + topic_id + '/comments'
    resp = requests.get(url=group_post_url)
    print('get comment status', resp.status_code)
    while resp.status_code > 300:
        print('get comment error, retry after 10s')
        time.sleep(10)
        resp = requests.get(url=group_post_url)
        print(resp.status_code)

    data = resp.json()
    total = data['total']
    count = total
    post_list = []
    while page > 0 and total > 0:
        page -= 1
        count -= 20
        group_post_url = 'https://api.douban.com/v2/group/topic/' + topic_id + '/comments?start=' + str(count)
        resp = requests.get(url=group_post_url)
        data = resp.json()
        if attr == 'text':
            for comment in data['comments']:
                post_list.append(comment[attr])
        elif attr == 'user_id':
            for comment in data['comments']:
                post_list.append(comment['author']['id'])
    return post_list


def get_user_posts(member_group_id, search_group_id):
    # 获取某用户发帖内容
    with open('member-%s.txt' % member_group_id, 'r', encoding='utf-8') as f:
        member_list = [i.strip() for i in f.readlines()]
        posts = get_group_posts(search_group_id)
        for p in posts:
            if p['author_link'] in member_list:
                print('%s(%s): %s %s' % (p['author'], p['author_link'], p['title'], p['link']))


def get_user_comments(member_group_id, search_group_id):
    # 获取某用户评论内容
    with open('member-%s.txt' % member_group_id, 'r', encoding='utf-8') as f:
        member_list = [i.strip() for i in f.readlines()]
        posts = get_group_posts(search_group_id)
        for p in posts:
            time.sleep(1)
            print('finish post: ' + p['link'])
            comments = get_comment(p['link'])
            for c in comments:
                if c['user_link'] in member_list:
                    print('%s(%s)' % (p['title'], p['link']))
                    print('%s(%s): %s %s\n' % (c['username'], c['user_link'], c['content'], c['time']))


if __name__ == '__main__':
    # print(get_random_proxy())
    print(check_member_in_group('',''))
    # reviewer_topic_id = ''
    # a=get_comment(reviewer_topic_id, attr='user_id', page=3)
