import re

_pattern = re.compile(r'var caseinfo=JSON.stringify\((?P<case_info>.+?)\);\$'
                      r'.+(var dirData = (?P<dir_data>.+?);if)?'  # 2018年底改版了，dirData没有返回了
                      r'.+var jsonHtmlData = (?P<html_data>".+");',
                      re.S)


def parse_detail(text: str) -> dict:
    return _pattern.search(text).groupdict()
