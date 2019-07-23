import re

import execjs
from execjs.runtime_names import Node

from ._unzip import unzip


def decrypt_runeval(runeval: str) -> str:
    if runeval.startswith("w63"):
        raise ValueError("invalid RunEval: w63")

    raw_js = unzip(runeval).decode()

    if "系统繁忙".encode("unicode_escape").decode() in raw_js:
        raise ValueError("invalid RunEval: 系统繁忙")

    try:
        parse_result = _decrypt_by_python(raw_js)
    except Exception:
        parse_result = _decrypt_by_nodejs(raw_js)

    if "while" in parse_result:
        raise ValueError("invalid RunEval: while(1)")

    key = re.search(r'com\.str\._KEY="(?P<key>\w+)"', parse_result).group("key")
    return key


def _decrypt_by_python(js: str) -> str:
    replace_map = {
        '!+[]': '1',
        '!![]': '"true"',
        '![]': '"false"',
        '("true"+[])': '"true"',
        '("false"+[])': '"false"',
        '[+[]]': '[0]',
        '(+[])': '0',
        '[][[]]': '"undefined"',
        '[]+[]': '""',
        '""+{}': '"[object Object]"',
        '["false"]+{}': '"false[object Object]"',
        '+1+[0]': '10',
        '+{}+""': '"NaN"',
        '["false"]': '"false"',
    }

    for old, new in replace_map.items():
        js = js.replace(old, new)

    js_fragments = js.split(";")

    args = re.search(r"String\.fromCharCode\((?P<args>.+)\)", js_fragments[0]).group("args")
    hide_script = repr("".join(chr(i.count("1")) for i in args.split(",")))

    text = js_fragments[3].replace("$hidescript", hide_script)[7:-2]
    result = eval(text)
    return result


def _decrypt_by_nodejs(js: str) -> str:
    js_code = js.replace("_[_][_](", "return ")[:-4]

    ctx = execjs.get(Node).compile(js_code)
    result = ctx.eval("")
    return result
