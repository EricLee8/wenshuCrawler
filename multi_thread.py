import json
import requests
import time
import random
from queue import Queue
import threading
import multiprocessing as mp

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

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
})

success_time = 0
dump_f = open("test_got_data.txt", 'a', encoding='UTF-8')
verbose = True

class wenshuCrawlThread(threading.Thread):
    # noinspection PyMissingConstructor
    def __init__(self, thread_name, jsonQueue, dataQueue, size):
        super(wenshuCrawlThread, self).__init__()
        self.thread_name = thread_name
        self.jsonQueue = jsonQueue
        self.dataQueue = dataQueue
        self.size = size

    def run(self):
        global success_time
        while success_time < self.size:
            try:
                json_content = self.jsonQueue.get(False)
            except:
                continue
            #不知道为什么，反正就是要这样处理一下
            if json_content.startswith(u'\ufeff'):
                json_content = json_content.encode('utf8')[3:].decode('utf8')
            #处理完成

            dict_content = json.loads(json_content)
            try:
                data = [get_data(dict_content["Docid"]), dict_content]
                self.dataQueue.put(data, False)
                if verbose:
                    print("Thread " + threading.current_thread().thread_name + " succeed!")

            except: #页面访问出错
                self.jsonQueue.put(json_content, False) #重新把刚刚的数据放进jsonQueue里
                if verbose:
                    print("Thread " + threading.current_thread().thread_name + " failed!")
            #finally:
                #print("%d, %d" %(self.jsonQueue.qsize(),self.dataQueue.qsize()))

class parseStoreThread(threading.Thread):
    # noinspection PyMissingConstructor
    def __init__(self, thread_name, dataQueue, size, lock, file_name):
        super(parseStoreThread, self).__init__()
        self.thread_name = thread_name
        self.dataQueue = dataQueue
        self.size = size
        self.lock = lock
        self.file_name = file_name

    def run(self):
        global success_time
        while success_time < self.size:
            time.sleep(0.05)
            try:
                data = self.dataQueue.get(False)
                text = get_text(data[0], data[1])
                with self.lock:
                    dump_f.write(text)
                    success_time += 1
                    if verbose:
                        print("Thread " + threading.current_thread().thread_name + " succeed!")
            except:
                continue


def get_data(s):
    error_msg = "请开启JavaScript并刷新该页"
    url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
    params = {
        "DocID": s,
    }
    time.sleep(0.05)
    response = session.get(url, params=params, proxies=random.choice(proxy_list), timeout=8)
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

def get_text(group_dict, dict_content):
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

    case_tpye = "案件类型: " + dict_content["案件类型"] + '\n'
    judge_date = "裁判日期: " +  dict_content["裁判日期"] + '\n'
    text = text + case_tpye + judge_date + '\n'

    return text



def multi_thread_crawl(load_file_name ,dump_file_name):
    global success_time, dump_f
    dump_f.close()
    dump_f = open(dump_file_name, 'a', encoding='UTF-8')

    load_f = open(load_file_name, 'r', encoding='UTF-8')

    size = 100
    thread_number = 8
    total_success_time = 0
    writeLock = threading.Lock()

    for k in range(200):
        j_queue = Queue()
        d_queue = Queue()
        success_time = 0

        for i in range(size):
            j_queue.put(load_f.readline())

        crawl_thread_list = []
        for i in range(thread_number):
            thread = wenshuCrawlThread("Crawl_thread-"+str(i), j_queue, d_queue, size)
            thread.start()
            crawl_thread_list.append(thread)

        parse_thread_list = []
        for i in range(thread_number):
            thread = parseStoreThread("Parse_thread-"+str(i), d_queue, size, writeLock, "test_got_data.txt")
            thread.start()
            parse_thread_list.append(thread)

        for thread in crawl_thread_list:
            thread.join()
        for thread in parse_thread_list:
            thread.join()
        total_success_time += size
        print("Number %d round completed!!!\n" %k)

    print(str(total_success_time) + '\n')

def main():
    p = mp.Pool(4)
    for i in range(4):
        p.apply_async(multi_thread_crawl, args=("2w_" + str(i+1) + ".json" ,"df" + str(i+1) + ".txt"))
    p.close()
    p.join()

if __name__=='__main__':
    main()

session.close()