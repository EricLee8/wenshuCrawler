import requests
import random
import re
import lxml
from lxml import etree

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
url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
params = {"DocID": "7c28e2a3-0051-4fe8-be6e-aa1f0010ebf4",}
response = session.get(url, params=params, proxies=random.choice(proxy_list))
html = etree.HTML(response.text)



