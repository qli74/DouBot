import os
from lxml import etree
import util
import hashlib
from config import *
from PIL import Image
from aip import AipOcr
import re
from nltk.corpus import words
wordset=set(words.words())

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def get_image_and_id(text):
    # 通过html提取验证码图片URL和id
    html = etree.HTML(text)
    pic_url = html.xpath("//img[@id='captcha_image']/@src")
    pic_id = html.xpath("//input[@name='captcha-id']/@value")
    if len(pic_url) and len(pic_id):
        pic_url = 'https://' + pic_url[0].split('//')[-1]
        pic_id=pic_id[0]
        return pic_url, pic_id
    else:
        return "", ""

def get_verify_code_pic(session, url):
    # 获取验证码的图片URL和id
    r = session.get(url, cookies=util.loadCookies())
    if r.status_code == 200:
        pic_url, pic_id = get_image_and_id(r.text)
        print(str(pic_url))
        return pic_url, pic_id
    else:
        print(str(url) + ", status_code: " + str(r.status_code))
        return "", ""

def get_verify_code_pic_doumail(session, url):
    # 获取验证码的图片URL和id
    r = session.get(url, cookies=util.loadCookies())
    if r.status_code == 200:
        pattern = "REPLY_FORM_DATA.captcha = {\n        id: \'(.*)\',\n        image: \'(.*)\'"
        searchObj = re.search(pattern, r.text, re.M | re.I)
        if searchObj:
            pic_id = searchObj.group(1)
            pic_url = searchObj.group(2)
            print(pic_id,pic_url)
            return pic_url, pic_id
    print(str(url) + ", status_code: " + str(r.status_code))
    return "", ""

    #else:
    #    print(str(url) + ", status_code: " + str(doc.status_code))
    #    return "", ""

def erase_background(img):
    # 对图片做预处理，去除背景
    # 遍历图片内的每一个像素点（坐标），设置阈值threshold，
    # 大于阈值的重置为白色，小于阈值的重置为黑色
    width, height = img.size
    threshold = 40
    for i in range(0, width):
        for j in range(0, height):
            p = img.getpixel((i, j))  # 抽取坐标（i,j）出像素点的RGB颜色值
            r, g, b = p
            if r > threshold or g > threshold or b > threshold:
                img.putpixel((i, j), WHITE)  # 设置坐标（i,j）处像素点的RGB颜色值为（255.255.255）
            else:
                img.putpixel((i, j), BLACK)
    return img

def denoise(img,window=1):
    # 对去除背景的图片做噪点处理
    if window == 1:  # 十字型滑动窗口
        window_x = [1, 0, 0, -1, 0]
        window_y = [0, 1, 0, 0, -1]
    elif window == 2:  # 矩形滑动窗口
        window_x = [-1, 0, 1, -1, 0, 1, 1, -1, 0]
        window_y = [-1, -1, -1, 1, 1, 1, 0, 0, 0]

    width, height = img.size
    for i in range(width):
        for j in range(height):
            box = []
            for k in range(len(window_x)):
                d_x = i + window_x[k]
                d_y = j + window_y[k]
                try:
                    d_point = img.getpixel((d_x, d_y))
                    if d_point == BLACK:
                        box.append(1)
                    else:
                        box.append(0)
                except IndexError:
                    img.putpixel((i, j), WHITE)
                    continue

            box.sort()
            if len(box) == len(window_x):
                mid = box[int(len(box) / 2)]
                if mid == 1:
                    img.putpixel((i, j), BLACK)
                else:
                    img.putpixel((i, j), WHITE)
    return img

def process_pic(pic_path):
    #预处理验证码图片
    img=Image.open(pic_path)
    img=erase_background(img)
    img=denoise(img,1)
    #img=denoise(img,2)
    img.save(pic_path+'_denoise.jpg')
    return pic_path+'_denoise.jpg'

def get_word_in_pic(pic_path):
    # 给定图片地址 pic_path，识别图片当中的文字
    if not pic_path:
        return ''
    # 二进制方式打开图文件
    pic_path=process_pic(pic_path)
    f = open(pic_path, 'rb')
    # 参数image：图像base64编码
    img = f.read()
    # 使用百度OCR识别
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    words=client.webImage(img)['words_result']
    if words:
        word=words[0]['words']
        word=word.strip()
        if word in wordset:
            print('captcha ',[word])
            return word
    print('captcha failed, retry after 5s')
    return ''

def save_pic_to_disk(pic_url, session):
    # 将链接中的图片保存到本地，并返回文件名
    try:
        res = session.get(pic_url)
        if res.status_code == 200:
            # 求取图片的md5值，作为文件名，以防存储重复的图片
            md5_obj = hashlib.md5()
            md5_obj.update(res.content)
            md5_code = md5_obj.hexdigest()
            file_name = img_path + str(md5_code) + ".jpg"
            # 如果图片不存在，则保存
            if not os.path.exists(file_name):
                with open(file_name, "wb") as f:
                    f.write(res.content)
            return file_name
        else:
            print("in func save_pic_to_disk(), fail to save pic. pic_url: " + pic_url +
                  ", res.status_code: " + str(res.status_code))
            raise Exception
    except Exception as e:
        print(e)

if __name__ == '__main__':
    get_word_in_pic('captcha/cd8979e9052d78881b815723746f3396.jpg')
