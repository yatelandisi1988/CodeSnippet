import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
from bs4 import BeautifulSoup
import re
import os
from hashlib import md5
import config
from multiprocessing import Pool

imageData=[]

#请求首页数据
def get_page_index(offset,keyword):
    mainUrl = "http://www.toutiao.com/search_content/?"
    args = {
        "offset": offset,
        "format": "json",
        "keyword":keyword,
        "autoload": "true",
        "count": "20",
        "cur_tab": "3"
    }
    header={
       "Accept":"application/json, text/javascript",
       "Accept-Encoding":"gzip, deflate, sdch",
       "Accept-Language":"zh-CN,zh;q=0.8",
       "Connection":"keep-alive",
       "Content-Type":"application/x-www-form-urlencoded",
       "Host":"www.toutiao.com",
       "Referer":"http://www.toutiao.com/search/?keyword=%E7%81%AB%E5%BD%B1%E5%BF%8D%E8%80%85",
       "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400",
       "X-Requested-With":"XMLHttpRequest"
    }
    url=mainUrl+urlencode(args)
    try:
        reponse=requests.get(url,header)
        if reponse.status_code==200:
            return reponse.text
        print(reponse.status_code)
        return None
    except RequestException:
        print("请求索引页出错")
        return None

# 解析首页获取的json数据
def parse_page_index(html):
    data=json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')

# 获取子页
def get_page_detail(url):
    try:
        reponse=requests.get(url)
        if reponse.status_code==200:
            return reponse.text
        print(reponse.status_code)
        return None
    except RequestException:
        print("请求详细页出错")
        return None

#从子页中提取出所有的链接信息
def parse_page_detail(html):
    htmlDOm=BeautifulSoup(html,"lxml")
    title=htmlDOm.select("title")[0].get_text()
    image_pattern=re.compile("var gallery =(.*?);",re.S)
    imageResult=re.search(image_pattern,html)
    if imageResult:
        detailJsonStr=imageResult.group(1)
        data=json.loads(detailJsonStr)
        if data and "sub_images" in data.keys():
            sub_images=data.get("sub_images")
            images=[item.get("url") for item in sub_images]
            return {
                'title':title,
                'images':images
            }

#下载图片
def download_image(url):
    print("正在下载:  "+url)
    try:
        reponse=requests.get(url)
        if reponse.status_code==200:
            save_image(reponse.content) #二进制是content，文本是text
        print(reponse.status_code)
        return None
    except RequestException:
        print("请求图片出错")
        return None

def save_image(content):
    file_path="{0}\{1}\{2}.{3}".format(os.getcwd(),"files",md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html=get_page_index(offset,config.KEYWORD)
    for url in parse_page_index(html):
        detail_html=get_page_detail(url)
        if detail_html:
            detailData=parse_page_detail(detail_html)
            imageData.append(detailData)
            for item in detailData.get("images"):
                download_image(item)
    
if __name__=='__main__':
    groups=[x*20 for x in range(config.GROUP_START,config.GROUP_END)]
    pool=Pool()
    pool.map(main,groups)
