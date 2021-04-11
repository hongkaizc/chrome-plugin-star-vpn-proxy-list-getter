import grequests
import requests
import hashlib
from crypto import Cipher_AES
import base64
import time
import json
import os
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def b64_decode(s):
    return base64.b64decode(s).decode()


def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def read_file(pf):
    return os.path.isfile(pf) and open(pf).read() or ''


def write_file(fn, c):
    open(fn, 'w').write(c)


'''
var key = CryptoJS.enc.Utf8.parse(hex_md5(json.s + ConsoleManager.onOpen.toString() + ConsoleManager.onClose.toString() + ConsoleManager.init.toString() + client.init.toString() + client.checkProxy.toString() + client.getProxy.toString() + p.on.toString()).substring(json.startIndex,json.endIndex));var decrypt = CryptoJS.AES.decrypt(json.d, key, {mode:CryptoJS.mode.ECB,padding: CryptoJS.pad.Pkcs7});var d = CryptoJS.enc.Utf8.stringify(decrypt).toString();
'''

headers = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'DNT': '1',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'chrome-extension://jajilbjjinjmgcibalaakngmkilboobh',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
}

key = b64_decode(read_file('keyjs.txt'))

current_acc = read_file('login.id')


def decode_response(r):
    return Cipher_AES(
        md5(r['s'] + key)[r['startIndex']:r['endIndex']], r['d']
    ).decrypt(r['d'], 'MODE_ECB', "PKCS5Padding", "base64")


def post(url, data):
    cookies = {
        'JSESSIONID': '9AAD4A3329938A4C6545662F5368C463',
        'token': 'af0c24670c97dd78584b47a1a7d6f087',
        'strLoginId': current_acc,
    }
    return requests.post(url, timeout=5, headers=headers, cookies=cookies, data=data, verify=False)


def gpost(url, data):
    cookies = {
        'JSESSIONID': '9AAD4A3329938A4C6545662F5368C463',
        'token': 'af0c24670c97dd78584b47a1a7d6f087',
        'strLoginId': current_acc,
    }
    return grequests.post(url, timeout=5, headers=headers, cookies=cookies, data=data, verify=False)


def get(url):
    cookies = {
        'JSESSIONID': '9AAD4A3329938A4C6545662F5368C463',
        'token': 'af0c24670c97dd78584b47a1a7d6f087',
        'strLoginId': current_acc,
    }
    return requests.get(url, headers=headers, cookies=cookies)


def is_expire(uid):
    print('正在检测帐号%s是否在体验时间段内' % uid)
    t = post(
        'https://astarvpn.center/astarnew/user/userInfo?1618148703377',
        {'strP': 'jajilbjjinjmgcibalaakngmkilboobh', 'strlognid': uid}
    ).json()
    if t['nCode'] > 0:
        print(t['strText'])
        return True
    t = t['jsonObject']['nCurrValidTime']
    print('免费时长剩余：', t)
    return t == '0'


def get_proxy_result(rsp):
    p = json.loads(decode_response(rsp))
    if p['strText'] == 'succ':
        p['jsonObject']['s'] = p['jsonObject']['_p']
        p['jsonObject']['d'] = p['jsonObject']['_s']
        return decode_response(p['jsonObject']).split('\'HTTPS ')[1].strip()[:-3]
    return None


def get_proxy(s, i) -> dict:
    return gpost(
        'https://astarvpn.center/astarnew/NewVPN/getProxy?%s' % time.time(),
        {'strP': 'jajilbjjinjmgcibalaakngmkilboobh', 'lid': i, 'strtoken': s, 'nonlinestate': '1', 'version': '109',
         'strlognid': current_acc}
    )


def get_proxy_list():
    j = post(
        'https://astarvpn.center/astarnew/NewVPN/getProxyList',
        {'strP': 'jajilbjjinjmgcibalaakngmkilboobh', 'nonlinestate': '1', 'version': '109',
         'strlognid': current_acc}
    ).json()
    return json.loads(decode_response(j)), j


def map_proxy_list():
    if is_expire(current_acc):
        print('免费时间过去了，正在注册新帐号...')
        reg = register()
        if reg is True:
            print('注册成功，使用新注册帐号[%s]重新获取代理' % read_file('login.id'))
            return map_proxy_list()
        print('想个办法换个 ip 试试？')
        exit(2)
    print('正在获取可用代理列表', flush=True)
    l, j = get_proxy_list()
    l = [{'name': info['n'], 'i': info['i'], 'c': info['c']} for info in l['jsonObject']['d']]
    print('共获取到%s个测试点' % len(l), flush=True)
    # 非异步请求
    # for i in l:
    #     print('正在获取', i['name'], '代理', flush=True)
    #     r = get_proxy(j['s'], i['i'])
    #     if r:
    #         pl.append({'http_proxy': r, 'name': i['name']})

    return [
        get_proxy_result(r.json())
        for r in grequests.map(get_proxy(j['s'], i['i']) for i in l)
        if r and get_proxy_result(r.json())
    ]


def register():
    acc = '%s@qq.com' % time.time()
    print('正在注册：', acc)
    data = {
        'strP': 'jajilbjjinjmgcibalaakngmkilboobh',
        'strlognid': acc,
        'strpassword': acc,
        'strvcode': 'zz43',
        'clientUUID': '8d3c97bd-57e3-432e-837d-44696eec34662021310224038437'
    }

    r = post('https://astarvpn.center/astarnew/user/register', data=data).json()
    print('注册返回结果：', r)
    if 'successful' in r['strText']:
        global current_acc
        current_acc = acc
        write_file('login.id', acc)
        return True
    return r['strText']


if __name__ == '__main__':
    pl = map_proxy_list()
    plt = '\r\n'.join(pl)
    write_file('proxy.list', plt)
    print('已将获取到的%s个代理写入 proxy.list 当中.' % len(pl))
