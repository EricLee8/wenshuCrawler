import base64
import re
from urllib import parse

import execjs
from execjs.runtime_names import Node
from lxml import html

_pattern = re.compile(r"dynamicurl\|(?P<path>.+?)\|wzwsquestion\|(?P<question>.+?)\|wzwsfactor\|(?P<factor>\d+)")


def decrypt_wzws(text: str) -> str:
    try:
        return _decrypt_by_python(text)
    except Exception:
        return _decrypt_by_nodejs(text)


def _decrypt_by_python(text: str) -> str:
    base_url = "http://wenshu.court.gov.cn"

    group_dict = _pattern.search(text).groupdict()
    question = group_dict["question"]
    factor = int(group_dict["factor"])
    path = group_dict["path"]

    label = "WZWS_CONFIRM_PREFIX_LABEL{}".format(sum(ord(i) for i in question) * factor + 111111)
    challenge = base64.b64encode(label.encode()).decode()

    dynamic_url = parse.urljoin(base_url, path)
    dynamic_url = "{url}?{query}".format(url=dynamic_url, query="wzwschallenge={}".format(challenge))
    return dynamic_url


def _decrypt_by_nodejs(text: str) -> str:
    base_url = "http://wenshu.court.gov.cn"

    custom_js = """
    window = {};
    document = {
        createElement: () => ({ style: "", appendChild: () => ({}), submit: () => ({}) }),
        body: { appendChild: obj => { window.location = obj.action } }
    };
    atob = str => Buffer.from(str, "base64").toString("binary");
    get_location = () => window.location;
    """
    html_doc = html.fromstring(text)
    js = html_doc.xpath("//script/text()")[0]

    ctx = execjs.get(Node).compile(custom_js + js)
    location = ctx.call("get_location")

    dynamic_url = parse.urljoin(base_url, location)
    return dynamic_url
