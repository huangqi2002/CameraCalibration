#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from utils.web_util import *
from utils.web_util_aes import *
from model.device import Device


class DeviceServer:
    def __init__(self):
        self.device = None

    def login(self, ip, url="/request.php"):
        self.device = Device()
        self.device.ip = ip
        self.device.url_host = f"http://{ip}"
        self.device.session = create_session()
        user_pwd = f"{self.device.username}:{self.device.password}"
        data_login = {
            "type": "login",
            "module": "BUS_WEB_REQUEST",
            "user_info": AesCtrV2().encrypt_message(user_pwd, 'secret08')
        }
        login_info = json.dumps(data_login)
        resp = post(device=self.device, url=url, data=login_info)
        if not resp:
            return False
        print("login success:", get_session_id(self.device.session))
        return True

    def heart_beat(self):
        data_heart_beat = {
            "type": "is_login_timeout",
            "module": "BUS_WEB_REQUEST",
            "body": {}
        }
        data = json.dumps(data_heart_beat)
        try:
            resp = post(device=self.device, data=data)
            print("get_device_info:", resp)
        except Exception as e:
            print("get_device_info: exception", e)

    def get_device_info(self):
        data_device_info = {
            "type": "get_device_info",
            "module": "BUS_WEB_REQUEST"
        }
        data = json.dumps(data_device_info)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("get_device_info:", resp)
            return json.loads(resp)
        except Exception as e:
            print("get_device_info: exception", e)

    def set_factory_mode(self, mode=0):
        data_mode = {
            "module": "AVS_REQUEST_MESSAGE",
            "type": "set_media_factory_mode",
            "body": {
                "mode": mode
            }
        }
        data = json.dumps(data_mode)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("set_factory_mode:", resp)
            return json.loads(resp)
        except Exception as e:
            print("set_factory_mode: exception", e)

    def get_factory_mode(self):
        data_mode = {
            "module": "AVS_REQUEST_MESSAGE",
            "type": "get_media_factory_mode"
        }
        data = json.dumps(data_mode)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("get_factory_mode:", resp)
            return json.loads(resp)
        except Exception as e:
            print("get_factory_mode: exception", e)

    def test(self):
        data_mode = {
            "module": "AVS_REQUEST_MESSAGE",
            "type": "get_rtsp_prm"
        }
        data = json.dumps(data_mode)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("get_factory_mode:", resp)
            return json.loads(resp)
        except Exception as e:
            print("get_factory_mode: exception", e)

    def upload_file(self, url="/upload.php", upload_path="", filename=""):
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
            post(device=self.device, url=url, data=e, headers=headers, timeout=120)
            return True
        except Exception as e:
            print("upload_file exception:", e)
        return False

    def reboot(self):
        if not self.device:
            return False
        data_reboot = {
            "type": "reboot_dev",
            "module": "SS_BUS_REQUEST"
        }
        data = json.dumps(data_reboot)
        try:
            post(device=self.device, data=data)
        except Exception:
            pass
        print("reboot:", get_session_id(self.device.session))
        self.clear_status()
        return True

    def logout(self):
        if not self.device:
            return False
        data_logout = {
            "type": "logout",
            "module": "BUS_WEB_REQUEST",
            "body": {}
        }
        data = json.dumps(data_logout)
        post(device=self.device, data=data)

        print("logout:", get_session_id(self.device.session))
        self.clear_status()
        return True

    def clear_status(self):
        if not self.device:
            return
        self.device.session.close()
        self.device.session = None
        self.device = None

    @staticmethod
    def check_json_resp_state(json_str, resp_type):
        try:
            json_obj = json.loads(json_str)
            state_code = json_obj['state']
            if state_code == 200:
                print(f"{resp_type} success.")
                return True
        except Exception as e:
            print(f"{resp_type} json except: {e}")
        return False


server = DeviceServer()
