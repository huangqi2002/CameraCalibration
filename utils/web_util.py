#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

encoding = "UTF-8"
HEADERS = {
    "Connect-Type": "application/x-www-from-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "en-US,en;zh-CN,zh",
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
}


def post(device, url="/request.php", params=None, files=None, data=None, timeout=50, headers=None):
    proxies = {"http": None, "https": None}
    if not headers:
        headers = HEADERS
    resp = device.session.post(url=f"{device.url_host}{url}", params=params, files=files, data=data, timeout=timeout,
                               headers=headers, proxies=proxies)
    if resp.status_code == 200:
        return resp.content.decode(encoding=encoding, errors="ignore")
    return None


def get(device, url, stream=False):
    proxies = {"http": None, "https": None}
    resp = device.session.get(url=f"{device.url_host}{url}", timeout=50, headers=HEADERS, proxies=proxies,
                              stream=stream)
    if resp.status_code == 200:
        return resp
    return None


def create_session():
    return requests.Session()


def get_session_id(session):
    if session is None:
        return None
    return session.cookies.get("sessionID")
