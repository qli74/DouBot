forbidwords=[] #违禁词，不会处理含有违禁词的帖子，保护机器人账号安全。可以设定为一些脏话
collectwords=['科普','理论','安利','推荐','分享','搬运','存档']

img_path = 'captcha/' #验证码图片保存地址

# 用于识别验证码的百度开放平台key，需申请
API_KEY = ""
SECRET_KEY = ""
APP_ID = ""

#小组信息
group_id = ''
group_name = ''
mydoulist_id = '' #用于收藏帖子的豆列
comment_collect_id = '' # 用于收集用户投稿的回复内容的帖子
reviewer_topic_id = '' # 用于收集入组申请审核员报名信息的帖子
group_base_url = 'https://www.douban.com/group/'
topic_base_url='https://www.douban.com/group/topic/'

#log格式
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"

my_headers = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)"
]

#代理池，如不使用代理可忽略
proxypool_url = 'http://127.0.0.1:5555/random'