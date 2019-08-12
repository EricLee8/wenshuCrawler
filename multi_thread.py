# -*- coding: UTF-8 -*-
import json
import requests
import time
import random
from queue import Queue
import threading
import multiprocessing as mp
import datetime
import os
import re

from wenshu_utils.document.parse import parse_detail
from wenshu_utils.wzws.decrypt import decrypt_wzws


ip_file = open("ip_use_2.0.txt", "r")
ip_list = []
for line in ip_file.readlines():
    ip_list.append({ "https" : line.strip('\n')})
regex = re.compile(r"[\u4e00-\u9fa5]")
regex2 = re.compile(r"[0-9]")
zh_note_list = ['、', '，', '《', '》', '。', '？', '！', '“', '”', '‘', '’', '：', '（', '）', '…', '—', '％']


# 代理服务器
proxyHost = "http-dyn.abuyun.com"
proxyPort = "9020"

#账号密码
proxyUser = "H670894FUO7F7F5D"
proxyPass = "5FDDDFACD81AE0C8"
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
total_success_time = 0
pre_success_time = 0
delay_time = 0.10
speed_test_time = 30
first_time_out = 6
second_time_out = 4
total_number_per_file = 100000
reboot_counter = 0
max_failing_time = 5
process_name = "Process-" + str(os.getpid())
lf_name = "10w_"
finish = False
verbose = False
is_need_reboot = False


dump_f = open("test_got_data.txt", 'a', encoding='UTF-8')

start_from = []
for i in range(4):
    try:
        c = len([ "" for line in open("df" + str(i+1) + ".json", "r", encoding='UTF-8')])
        start_from.append(c)
    except:
        start_from.append(0)

print( process_name + " start from: " + str(start_from) )
print('\n')


class wenshuCrawlThread(threading.Thread):
    # noinspection PyMissingConstructor
    def __init__(self, thread_name, jsonQueue, dataQueue, size):
        super(wenshuCrawlThread, self).__init__()
        self.thread_name = thread_name
        self.jsonQueue = jsonQueue
        self.dataQueue = dataQueue
        self.size = size

    def run(self):
        global success_time, is_need_reboot
        while success_time < self.size and (not is_need_reboot):
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
    def __init__(self, thread_name, dataQueue, size, lock):
        super(parseStoreThread, self).__init__()
        self.thread_name = thread_name
        self.dataQueue = dataQueue
        self.size = size
        self.lock = lock

    def run(self):
        global success_time, total_success_time, is_need_reboot
        while success_time < self.size and (not is_need_reboot):
            time.sleep(delay_time)
            try:
                data = self.dataQueue.get(False)
                j_text = json.dumps( get_JSON_dict(data[0], data[1]), ensure_ascii=False ) + '\n'
                #text = get_text(data[0], data[1])
                with self.lock:
                    dump_f.write(j_text)
                    total_success_time += 1
                    #print(j_text)
                    success_time += 1
                    if verbose:
                        print("Thread " + threading.current_thread().thread_name + " succeed!")
            except:
                #if verbose:
                    #print("Thread " + threading.current_thread().thread_name + " failed!")
                continue


def get_data(s):
    global first_time_out, second_time_out
    error_msg = "window.location.href="
    url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
    params = {
        "DocID": s,
    }
    time.sleep(delay_time)
    response = session.get(url, params=params, proxies=random.choice(ip_list), timeout=first_time_out)
    text = response.content.decode()

    if error_msg in text:
        retry = 3
        for _ in range(retry):
            response = session.get(url, params=params, proxies=random.choice(ip_list), timeout=second_time_out)
            text = response.content.decode()
            if error_msg not in text:
                break
        else:
            if verbose:
                print("连续{}次获取数据失败".format(retry))

    group_dict = parse_detail(response.text)
    #pprint(group_dict)
    return  group_dict


def get_zh_text(s):
    text = ""
    sl = s.split('>')
    for ele in sl:
        if len(re.findall(regex, ele[0])) != 0 or len(re.findall(regex2, ele[0])) != 0 or ele[0] in zh_note_list:
            second_list = ele.split('<')
            for ele2 in second_list:
                if len(re.findall(regex, ele2[0])) != 0 or ele2[0] in zh_note_list:
                    if len(ele2) < 3:
                        text = text + ele2
                    else:
                        text = text + ele2 + '\n'
                elif len(re.findall(regex2, ele2[0])) != 0:
                    if text[len(text)-1] == '\n':
                        text = text[:len(text)-1]
                    text = text + ele2
    return text


def get_JSON_dict(group_dict, dict_content):
    # group_dict 是从网上返回的东西，dict_content是从docid文件里获取的信息
    j_dict = {}
    html_content = group_dict['html_data']
    text = get_zh_text(html_content)

    j_dict["判决书"] = text

    try:
        head = group_dict['case_info']
        head = eval(head.replace('null', r'""'))
        j_dict["诉讼记录段原文"] = head["诉讼记录段原文"]
        j_dict["案件名称"] = head["案件名称"]
        j_dict["案号"] = head["案号"]

    except KeyError:
        if verbose:
            print("Fatal error: there is no such key in dict!!!\n")

    try:
        j_dict["案件类型"] = dict_content["案件类型"]
        j_dict["裁判日期"] = dict_content["裁判日期"]
        j_dict["案号"] = dict_content["案号"]
        j_dict["审判程序"] = dict_content["审判程序"]
    except KeyError:
        if verbose:
            print("Fatal error: there is no such key in dict!!!\n")

    return j_dict


def timer_task():
    global pre_success_time, total_success_time, finish, reboot_counter, is_need_reboot, max_failing_time

    # to calculate the speed
    speed = (total_success_time - pre_success_time) / (speed_test_time/60) * 60
    pre_success_time = total_success_time
    print(process_name + ":  " + datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S') + "  speed: " + str(speed) +"/h" + "  total success time: " + str(total_success_time) )

    # to tell if the process need to be reboot
    if speed == 0:
        reboot_counter += 1
        if reboot_counter >= max_failing_time:
            reboot_counter = 0
            is_need_reboot = True
            time.sleep(15)
            print(process_name + " :连续速度为0已经 " + str(max_failing_time) + " 个" + str(speed_test_time) + "秒, 现在重启进程!!!!!!!!\n")
            i = int(process_name.replace("Process-", ""))
            multi_thread_crawler(lf_name + str(i+1) + ".json" ,"df" + str(i+1) + ".json", total_success_time, i)
            return False
    else:
        reboot_counter = 0

    if not finish:
        t = threading.Timer(speed_test_time, timer_task)
        t.start()


def multi_thread_crawler(load_file_name ,dump_file_name, start, name_number):
    global success_time, dump_f, count_f, finish, total_number_per_file, is_need_reboot, process_name, reboot_counter, total_success_time

    dump_f.close()
    process_name = "Process-" + str(name_number)
    is_need_reboot = False
    reboot_counter = 0
    finish = False

    total_success_time = start
    #print(process_name + " :total success time: " + str(total_success_time) + '\n')

    if total_number_per_file == start:
        time.sleep(1)
        finish = True
        print(process_name + " has already finished!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! "  + '\n')
        return finish

    dump_f = open(dump_file_name, 'a', encoding='UTF-8')
    load_f = open(load_file_name, 'r', encoding='UTF-8')
    size = 100
    writeLock = threading.Lock()
    thread_number = 25

    # to process the remain data (零头) ==============================================================
    for _ in range(start):
        load_f.readline()
    lingtou = start % size
    print(process_name + " 零头：" + str(lingtou) )
    new_start = start
    if lingtou != 0:
        remain = size - lingtou
        new_start = start + remain
        print(process_name + " 还有 %d 的数据是除去零头的剩余数据，处理完后从第 %d 个数据开始主进程！\n" %(remain, new_start))
        assert new_start%size == 0
        js_queue = Queue()
        da_queue = Queue()
        success_time = 0
        for k in range(remain):
            js_queue.put(load_f.readline())

        #  Speed test -----------------------------------------------------
        timer = threading.Timer(speed_test_time, timer_task)
        # 等待speed_test_time间隔调用一次timer_task() 函数
        timer.start()
        #  Speed test -----------------------------------------------------

        remain_crawl_thread_list = []
        for i in range(thread_number):
            thread = wenshuCrawlThread("Remain_Crawl_thread-" + str(i), js_queue, da_queue, remain)
            thread.start()
            remain_crawl_thread_list.append(thread)
        remain_parse_thread_list = []
        for i in range(thread_number):
            thread = parseStoreThread("Rmain_Parse_thread-" + str(i), da_queue, remain, writeLock)
            thread.start()
            remain_parse_thread_list.append(thread)
        for thread in remain_crawl_thread_list:
            thread.join()
        for thread in remain_parse_thread_list:
            thread.join()
        if is_need_reboot:
            dump_f.close()
            return 0
        print(process_name + ":  " + "Remain %d data processed!!!" %remain )
    # to process the remain data (零头) ==============================================================
    else: #就算没有零头也需要启动测速函数
        #  Speed test -----------------------------------------------------
        timer = threading.Timer(speed_test_time, timer_task)
        # 等待speed_test_time间隔调用一次timer_task() 函数
        timer.start()
        #  Speed test -----------------------------------------------------


    # mian process! ==================================================================================
    print(process_name + ":  " + "Now start the main process!!!\n")
    round_times = (total_number_per_file - new_start) // size
    already_rounds = new_start // size
    total_round_times = total_number_per_file // size

    for k in range(round_times):
        j_queue = Queue()
        d_queue = Queue()
        success_time = 0

        for i in range(size):
            j_queue.put(load_f.readline())

        #爬取线程
        crawl_thread_list = []
        for i in range(thread_number):
            thread = wenshuCrawlThread("Crawl_thread-"+str(i), j_queue, d_queue, size)
            thread.start()
            crawl_thread_list.append(thread)

        #数据处理、储存线程
        parse_thread_list = []
        for i in range(thread_number):
            thread = parseStoreThread("Parse_thread-"+str(i), d_queue, size, writeLock)
            thread.start()
            parse_thread_list.append(thread)

        for thread in crawl_thread_list:
            thread.join()
        for thread in parse_thread_list:
            thread.join()
        # for rebooting
        if is_need_reboot:
            dump_f.close()
            return 0
        print(process_name + ":  " + "Number %d/%d round completed!!!\n" %(k+already_rounds+1,total_round_times))

    finish = True
    load_f.close()
    dump_f.close()
    print(process_name + " finished!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # mian process! ==================================================================================


def main():
    global start_from
    is_test = False

    if not is_test:
        is_real_finish = False
        while not is_real_finish:
            p = mp.Pool(4)
            for i in range(4):
                p.apply_async( multi_thread_crawler, args=(lf_name + str(i+1) + ".json" ,"df" + str(i+1) + ".json", start_from[i], i) )
            p.close()
            p.join()

            is_real_finish = True
            start_from = []
            for i in range(4):
                c = len(["" for line in open("df" + str(i + 1) + ".json", "r", encoding='UTF-8')])
                start_from.append(c)

            for i in range(4):
                if start_from[i] < total_number_per_file:
                    is_real_finish = False
                    print("=========================================================================================\n")
                    print("The processes finished ABNORMALLY, and now restart the processes!!!!!\n")
                    print("=========================================================================================\n")
                    break

        print("=========================================================================================\n")
        print("The processes have finished normally and now exit!!!!!!!\n")
        print("=========================================================================================\n")

    else:
        multi_thread_crawler("10w_1.json", "test.json", 0, 1)


'''
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
'''

'''
def old_get_JSON_dict(group_dict, dict_content):
    # group_dict 是从网上返回的东西，dict_content是从docid文件里获取的信息
    text = ""
    j_dict = {}
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

    j_dict["判决书"] = text

    try:
        head = group_dict['case_info']
        head = eval(head.replace('null', r'""'))
        j_dict["诉讼记录段原文"] = head["诉讼记录段原文"]
    except KeyError:
        if verbose:
            print("Fatal error: there is no such key[case_info or 诉讼记录原文] in dict!!!\n")
        j_dict["诉讼记录段原文"] = ""

    try:
        j_dict["案件类型"] = dict_content["案件类型"]
        j_dict["裁判日期"] = dict_content["裁判日期"]
    except KeyError:
        if verbose:
            print("Fatal error: there is no such key[案件类型 or 裁判日期] in dict!!!\n")
        j_dict["案件类型"] = ""
        j_dict["裁判日期"] = ""

    return j_dict
'''


if __name__=='__main__':
    main()

session.close()