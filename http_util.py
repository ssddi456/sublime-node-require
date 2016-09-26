# -*- coding: utf-8 -*-
import os
import re

import json
import sys

pkg_path = os.path.abspath(os.path.dirname(__file__))


python_version = sys.version_info[0]

if python_version == 3 :
  import urllib.request as urllib
  from urllib.parse import urlencode
else:
  from urllib import urlencode
  import urllib2 as urllib


proxy_handler = urllib.ProxyHandler({})
opener = urllib.build_opener(proxy_handler)
urllib.install_opener(opener)
setting_base_name = 'txt_prepros.sublime-settings'

def read_json( req ) :
  # force no proxy
  try:
    resp = urllib.urlopen(req)
  except Exception:
    sublime.message_dialog(u'网络异常，请检查你的网络设置')
    return

  ret = json.loads(resp.read().decode('utf8', 'ignore'))

  if 'error' in ret and ret['error'] :
    sublime.message_dialog(ret['msg'] or u'服务器返回了一个错误')

  return ret 

def http_post ( url, body ):
  req = urllib.Request(url, urlencode( body))
  req.get_method = lambda : 'POST'
  return read_json(req)

def http_get (url):
  req = urllib.Request(url)
  req.get_method = lambda : 'GET'
  return read_json(req)
