import requests
import random
#import re
import json
import time
from queue import Queue
import threading

from wenshu_utils.document.parse import parse_detail
from wenshu_utils.wzws.decrypt import decrypt_wzws

proxy_list = [
{"https" : "120.83.103.18"},
{"https" : "27.40.129.172"},
{"https" : "210.22.176.146"},
{"https" : "1.198.72.247"},
{"https" : "182.34.33.58"},
{"https" : "211.147.239.101"},
{"https" : "120.83.99.221"},
{"https" : "120.83.122.72"},
{"https" : "221.206.100.133"},
{"https" : "110.189.152.86"},
{"https" : "1.192.241.2"},
{"https" : "113.121.41.96"},
{"https" : "114.239.149.120"},
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
})

def get_data(s):
    error_msg = "请开启JavaScript并刷新该页"
    url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
    params = {
        "DocID": s,
    }
    #time.sleep(2)
    response = session.get(url, params=params, proxies=random.choice(proxy_list))
    text = response.content.decode()

    if error_msg in text:
        retry = 3
        for _ in range(retry):
            redirect_url = decrypt_wzws(text)
            response = session.get(redirect_url)
            text = response.content.decode()
            if error_msg not in text:
                break
        else:
            print("连续{}次获取数据失败".format(retry))

    group_dict = parse_detail(response.text)
    #pprint(group_dict)
    return  group_dict

def get_text(group_dict):
    text = ""
    html_content = group_dict['html_data']
    arr = html_content.split('FONT-SIZE')
    arr[0] = arr[0].split('\\')[3][1:]

    for i in range(1, len(arr)):
        arr[i] = arr[i].split('FONT-FAMILY')[0]
        arr[i] = arr[i].split('>')[1].rstrip('</div')

    for ele in arr:
        if ele=='<p' or ele=='<title' or ele=='</p' or ele=='':
            continue
        text = text + ele + '\n'

    head = group_dict['case_info']
    head = eval(head.replace('null', r'""'))
    head_str = "诉讼记录段原文: " + head["诉讼记录段原文"]
    text = text + head_str + "\n"

    '''
    case_tpye = "案件类型: " + j_content["案件类型"] + '\n'
    judge_date = "裁判日期: " +  j_content["裁判日期"] + '\n'
    text = text + case_tpye + judge_date
    '''

    return text







session.close()

'''
import urllib.request as urllib2
import random

proxy_list = [
    {"https" : "1.198.72.247"}
]

# 随机选择一个代理
proxy = random.choice(proxy_list)
# 使用选择的代理构建代理处理器对象
httpproxy_handler = urllib2.ProxyHandler(proxy)

opener = urllib2.build_opener(httpproxy_handler)

request = urllib2.Request("http://www.baidu.com/")
response = opener.open(request)
print(response.read())
'''