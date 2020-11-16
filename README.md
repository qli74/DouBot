## DouBot - 豆瓣小组机器人

#### 功能
1. 顶帖，根据关键词回复/随机回复/AI回复
2. 自动接收用户投稿
3. 根据关键词收藏帖子
4. 回复私信
5. 自动处理入组申请
6. 自动发帖或搬运帖子

使用百度OCR处理验证码

#### 如何使用
在config.py中输入小组id，百度开发平台key等信息

需在resources目录中添加自己的回复语料：
* reply_keywords.txt: 有关键词的回复，格式为 关键词1/关键词2/关键词3:回复a/回复b/回复3
* reply_random.txt: 没有设定关键词的回复
* reply_positive.txt: 友善的回复
* reply_emojis: 随机在回复前后添加emoji

可以使用青云客或图灵机器人自动生成回复。如果使用图灵机器人，需要注册并获取自己的API

运行main.py开始顶帖、收藏帖子和处理私信

#### 代码说明
* config.py：参数文件
* util.py：读取cookies,邮件提醒等
* captcha_util.py：获取验证码图片，识别验证码
* group_get.py：获取小组内的成员，帖子，帖子回复等
* group_post.py：发表帖子，回复帖子等
* doumail.py：处理豆邮，回复豆邮
* review.py：获取入组申请，通过申请或拒绝申请等功能。可以随机向组员发送私信邀请帮助审核入组申请，也可以修改为根据暗号直接通过/拒绝
* RespGen.py：从回复模版中挑选或通过AI生成回复

#### 注意事项
回复私信功能比较敏感，容易被禁言，可以不运行这一功能

每次发帖/回复豆邮等动作后，随机sleep一段时间，防止操作太频繁被禁言。目前设定为回复后休眠100-150秒，如果没有新帖子需要回复，则休眠300-600秒。可以适当调整，但不要太频繁。

本机器人仅为帮助管理豆瓣小组开发，请谨慎使用，务必遵守豆瓣小组规章制度。请不要传播广告，不过于频繁发帖。风险由用户自行承担，开发者不承担任何责任。

