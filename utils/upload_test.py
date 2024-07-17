import json
import os
import urllib

import cv2
import numpy as np
import requests
from requests_toolbelt import MultipartEncoder

from model.app import app_model
from model.config import Config
from model.device import Device
from server.web.web_server import server

encoding = "UTF-8"
HEADERS = {
    "Connect-Type": "application/x-www-from-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "en-US,en;zh-CN,zh",
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/97.0.4692.71 Safari/537.36",
}


class upload_test:
    def __init__(self):
        self.device = Device()
        self.device.session = requests.Session()
        self.device.ip = "192.168.1.100"
        self.device.url_host = f"http://{self.device.ip}"

    def set_ip(self, ip_str):
        self.device.ip = ip_str
        self.device.url_host = f"http://{ip_str}"

    def post(self, device, url="/request.php", params=None, files=None, data=None, timeout=50, headers=None):
        proxies = {"http": None, "https": None}
        if not headers:
            headers = HEADERS

        try:
            resp = device.session.post(url=f"{device.url_host}{url}", params=params, files=files, data=data,
                                       timeout=timeout,
                                       headers=headers, proxies=proxies)
            if resp.status_code == 200:
                return resp.content.decode(encoding=encoding, errors="ignore")
        except Exception as e:
            print("登录失败……")
        return None

    def upload_file(self, url="/upload.php", upload_path="", filename=""):
        print(f"fupload filename={filename}, upload_path={upload_path}")
        if not self.device:
            return False
        name = filename.replace('\\', '/').split("/")[-1]
        params = {"filepath": upload_path, "user_info": ""}
        e = MultipartEncoder(
            fields={
                json.dumps(params): (name, open(filename, "rb"), "application/octet-stream"),
            }
        )

        headers = HEADERS.copy()
        headers['Content-Type'] = e.content_type

        try:
            result = self.post(device=self.device, url=url, data=e, headers=headers, timeout=120)
            return True
        except Exception as e:
            print("upload_file exception:", e)
        return False


def fetchImageFromHttp(image_url, timeout_s=1):
    try:
        if image_url:
            resp = urllib.request.urlopen(image_url, timeout=timeout_s)
            image = np.asarray(bytearray(resp.read()), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            return image
        else:
            return []
    except Exception as error:
        print('获取图片失败', error)
        return []


if __name__ == '__main__':
    # img_response = fetchImageFromHttp("http://192.168.12.231/download.php/chessboard/chessboard_r.jpg")
    # cv2.imshow('img', img_response)
    # cv2.waitKey()
    upload_tools = upload_test()
    upload_tools.set_ip("192.168.110.82")
    upload_tools.upload_file(upload_path="/mnt/usr/kvdb/usr_data_kvdb/external_cfg.json", filename="D:\\VZ\\camera_calibration\\CameraCalibrationTool_repair\\data\\repair\\external\\5dd6f04b-a77c9018\\external_cfg.json")
