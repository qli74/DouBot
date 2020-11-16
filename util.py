import requests
import time
import smtplib
import random

def if_time_in_hour(time_str):
    t = time.mktime(time.strptime(time_str, '%Y-%m-%d %H:%M:%S'))  # struct 格式转时间戳
    now = time.time()
    if now - t < 3600:
        return True
    else:
        return False

def get_headers(fileName=None):
    name = 'headers.txt'
    if (fileName is not None):
        name = fileName
    name = 'resources/' + name
    headers = {}
    with open(name, "r", encoding='utf-8') as f_headers:
        hdrs = f_headers.readlines()
    for line in hdrs:
        key, value = line.split(": ")
        headers[key] = value.strip()
    return headers

def login(url, password, usrname, session):
    # 登录功能目前无法使用，有动态拼图验证码
    loginData = {'ck': '', 'name': usrname,
                 'password': password, 'remember': 'true'}
    #loginHeaders = get_headers('login_headers.txt')
    l = session.post(url, data=loginData)

    if l.status_code == requests.codes['ok'] or l.status_code == requests.codes['found']:
        print("Login Successfully")
        return True
    else:
        print("Failed to Login")
        session.close()
        return False

def get_ck_from_cookies(session):
    # 从cookie中获取ck值（ck: post操作表单隐藏字段）
    cookies = loadCookies()
    ck = cookies.get('ck')
    if (ck is None):
        raise Exception('No ck found in cookies')
    return ck

def loadCookies():
    cookies = {}
    with open('resources/cookies.txt', "r", encoding='utf-8') as f_cookie:
        douban_cookies = f_cookie.readlines()[0].split("; ")
        for line in douban_cookies:
            key, value = line.split("=", 1)
            cookies[key] = value
        return cookies

def getCred(fileName='confidentials/pwd.txt'):
    cred = {}
    with open(fileName, 'r', encoding='utf-8') as reader:
        line = reader.readline()
        k, v = line.strip().split(':')
        cred['usr'] = k.strip()
        cred['pwd'] = v.strip()
    return cred

def getCookiesFromSession(session):
    cookies = session.cookies.get_dict()
    return cookies

def flush_cookies(session: requests.Session):
    cookies = session.cookies.get_dict()
    line = ""
    with open('resources/cookies.txt', "w", encoding='utf-8') as f_cookie:
        for k, v in cookies.items():
            line += k + '=' + v + '; '
        line = line[:len(line) - 2]
        f_cookie.write(line)

def email_notify(content='Hey, check your robot'):
    # 邮件提醒
    gmail_user = '@gmail.com'
    gmail_password = ''

    sent_from = gmail_user
    to = '@gmail.com'
    subject = 'OMG Super Important Message of Your Robot'

    email_text = '''\\
             ... From: %s
             ... Subject: %s...
             ...
             ... %s ''' % (sent_from, subject, content)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except:
        print('Something went wrong...')

def random_sleep(a,b,info):
    # 随机休眠一段时间
    sleept = random.choice(list(range(a, b)))
    print(info+', sleep', sleept)
    time.sleep(sleept)

if __name__ == '__main__':
    email_notify()

