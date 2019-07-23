from pprint import pprint

import json
import requests
import time
import random

from wenshu_utils.document.parse import parse_detail
from wenshu_utils.wzws.decrypt import decrypt_wzws

proxy_list = [
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
{"https" : "60.10.22.229"},
{"https" : "163.204.245.179"},
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
})

success_num = 0
times = 0

# 代理服务器
proxyHost = "http-dyn.abuyun.com"
proxyPort = "9020"

#账号密码
proxyUser = "H6F573P8H157I04D"
proxyPass = "EB795750B5FE02BC"
proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
      "host" : proxyHost,
      "port" : proxyPort,
      "user" : proxyUser,
      "pass" : proxyPass,
    }

proxiess = {
        "http"  : proxyMeta,
        "https" : proxyMeta,
    }

def get_data(s):
    error_msg = "请开启JavaScript并刷新该页"
    url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
    params = {
        "DocID": s,
    }
    time.sleep(2)
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



def trail(trail_times, dump_f):
    global success_num, times
    if trail_times%2 == 0:
        load_f = open("source_even.json", 'r', encoding='UTF-8')
        switch_f = open("source_odd.json", 'w', encoding='UTF-8')
    else:
        load_f = open("source_odd.json", 'r', encoding='UTF-8')
        switch_f = open("source_even.json", 'w', encoding='UTF-8')

    pre_content = load_f.readline()

    while pre_content:
        times += 1
        if pre_content.startswith(u'\ufeff'):
            content = pre_content.encode('utf8')[3:].decode('utf8')
        else:
            content = pre_content
        j_content = json.loads(content)
        docid = j_content["Docid"]

        docid = docid.strip('\n')
        try:
            group_dict = get_data(docid)
            pre_content = load_f.readline()
            print("ok\n")
            success_num += 1
            html_content = group_dict['html_data']
            arr = html_content.split('FONT-SIZE')
            arr[0] = arr[0].split('\\')[3][1:]

            for i in range(1, len(arr)):
                arr[i] = arr[i].split('FONT-FAMILY')[0]
                arr[i] = arr[i].split('>')[1].rstrip('</div')

            for ele in arr:
                dump_f.write(ele+'\n')
                #print(ele)

            head = group_dict['case_info']
            head = eval(head.replace('null', r'""'))
            head_str = "诉讼记录段原文: " + head["诉讼记录段原文"]
            dump_f.write(head_str + '\n')
            #print(head_str)

            case_tpye = j_content["案件类型"]
            judge_date = j_content["裁判日期"]
            dump_f.write("案件类型: " + case_tpye + '\n' )
            dump_f.write("裁判日期: " + judge_date + "\n")
            dump_f.write("\n\n")
            print("Now we have tried for ", times, " times and succeed ", success_num, " times.\n")
            #print("案件类型: ", case_tpye)
            #print("裁判日期: ", judge_date, "\n")

        except :
            switch_f.write(pre_content)
            pre_content = load_f.readline()
            print("failed\n")
            print("Now we have tried for ", times, " times and succeed ", success_num, " times.\n")
            continue

    print("success number: ", success_num)


def main():
    df = open("test_got_data.txt", 'a', encoding='UTF-8')
    trail_times = 0

    while success_num<10000:
        trail(trail_times, dump_f=df)
        trail_times += 1
    print("Total try times: ", times)


main()

session.close()