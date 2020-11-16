import random
import requests
import urllib.parse
import re
class RespGen:
    def __init__(self):
        self.bot = None
        self.map = {}

        # 设定了关键词的回复
        with open('resources/reply_keywords.txt', "r", encoding='utf-8') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                #print(lines[i],lines[i].split(':'))
                titles,resps=lines[i].split(':')
                titles = titles.strip().split('/')
                i += 1
                resps = resps.strip().split('/')
                for t in titles:
                    self.map[t] = self.map.get(t,[])+resps
        self.possibles = set(self.map.keys())

        #更随机的回复
        with open('resources/reply_random.txt', "r", encoding='utf-8') as file:
            self.random = file.readlines()
        self.random=[r.strip('\n') for r in self.random]

        #一些emoji
        with open('resources/reply_emojis.txt', "r", encoding='utf-8') as file:
            self.randomemoji = file.readline()
        self.randomemoji = self.randomemoji.split(' ')

        #友善的回复
        with open('resources/reply_positive.txt', "r", encoding='utf-8') as file:
            self.positive = file.readlines()
        self.positive=[r.strip('\n') for r in self.positive]
        self.random+=self.positive

    def getResp_AI(self, query: str, type='青云客',userid=None,username=None):
        # 获取AI回复
        #query=urllib.parse.quote(query.encode('gb2312'))
        if type == '青云客':
            url='http://api.qingyunke.com/api.php?key=free&appid=0&msg='+query
            reply=requests.get(url).json()['content']
            # 青云客机器人名字叫菲菲，将其替换为你的机器人名字
            reply=reply.replace('菲菲','机器人名字').replace('{br}','\n')
            pattern = "{face:(.*)}"
            searchObj = re.search(pattern, reply, re.M | re.I)
            if searchObj:
                reply=reply.replace(searchObj.group(),random.choice(self.randomemoji))
        elif type == '图灵':
            # 参考http://www.tuling123.com/help/h_cent_webapi.jhtml
            url='http://www.tuling123.com/openapi/api'
            data={
                "key": "APIKEY",
                "info": query,
                "userid":"123456"
            }
            reply = requests.post(url,data).json()['text']
        else:
            print('请选择青云客或图灵机器人')
            raise ValueError
        return reply

    def getResp(self, ques: str, userid=None,username=None):
        if '机器人名字' in ques or '机器人' in ques:
            reply=random.choice(self.positive)
        else:
            keywords = []
            for match in self.possibles:
                if match in ques:
                    keywords.append(match)
            choose=random.choice(list(range(5)))
            if choose==0:
                rsp=[]
                for k in keywords:
                    rsp += self.map.get(k)
            elif choose==1:
                rsp = []
            else:
                rsp = list(self.random)
            if not rsp :
                rsp = self.map.get(random.choice(tuple(self.possibles)))
            #choose from several rsps
            chosen = random.randint(0, len(rsp) - 1)
            while '{no}' in rsp[chosen]:
                chosen = random.randint(0, len(rsp) - 1)
                if '{less}' in rsp[chosen]:
                    if random.choice(list(range(4)))==0:
                        chosen = random.randint(0, len(rsp) - 1)
            reply=rsp[chosen]

        for un in ['{username}','｛username｝','｛usename｝','{usename}']:
            reply=reply.replace(un,username)
        reply=reply.replace('\\n','\n')
        for prefix in ['{no}', '{less}']:
            reply=reply.strip(prefix)
        if random.choice(list(range(3)))>0:
            reply+=random.choice(self.randomemoji)*random.choice([0,1,2,3])
        else:
            reply=random.choice(self.randomemoji)*random.choice([0,1,2,3])+reply
        return reply

if __name__ == '__main__':
    r = RespGen()
    rsp = r.getResp_AI("笑一个", 1000,'啦啦啦')
    print(rsp)