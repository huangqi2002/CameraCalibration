#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from utils.web_util import *
from utils.web_util_aes import *
from model.device import Device
from model.app import app_model


class DeviceServer:
    def __init__(self):
        self.device = None

    def login(self, ip, url="/request.php", timeout=50):
        self.device = Device()
        self.device.ip = ip
        self.device.url_host = f"http://{ip}"
        self.device.username = app_model.config_fg.get("username")
        self.device.password = app_model.config_fg.get("password")
        self.device.session = create_session()
        user_pwd = f"{self.device.username}:{self.device.password}"
        data_login = {
            "type": "login",
            "module": "BUS_WEB_REQUEST",
            "user_info": AesCtrV2().encrypt_message(user_pwd, 'secret08')
        }
        login_info = json.dumps(data_login)
        resp = post(device=self.device, url=url, data=login_info, timeout=timeout)
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
            result = post(device=self.device, url=url, data=e, headers=headers, timeout=120)
            return True
        except Exception as e:
            print("upload_file exception:", e)
        return False

    def get_internal_cfg(self):
        internal_cfg_data = {
            "module": "ALG_REQUEST_MESSAGE",
            "type": "get_internal_calibration"
        }
        data = json.dumps(internal_cfg_data)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("get_internal_cfg_data:", resp)
            return json.loads(resp)
        except Exception as e:
            print("get_internal_cfg_data: exception", e)

    def get_external_cfg(self):
        external_cfg_data = {
            "module": "ALG_REQUEST_MESSAGE",
            "type": "get_external_cfg"
        }
        data = json.dumps(external_cfg_data)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("get_external_cfg_data:", resp)
            return json.loads(resp)
            # return json.loads(resp)
        except Exception as e:
            print("get_external_cfg_data: exception", e)

    def get_osd_para(self):
        get_osd_para_data = {
            "module": "AVS_REQUEST_MESSAGE",
            "type": "get_osd_prm"
        }
        data = json.dumps(get_osd_para_data)
        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            # print("get_osd_para:", resp)
            return json.loads(resp)
        except Exception as e:
            print("get_osd_para: exception", e)

    def ctrl_osd(self, enable):
        # for time_index in range(app_model.login_retry_max_count):
        #     login_result = self.login(app_model.device_model.ip)
        #     if not login_result:
        #         time.sleep(1)
        #         continue
        # login_result = self.login(app_model.device_model.ip)
        # if not login_result:
        #     return None

        self.get_osd_para()
        # close_osd_data = {
        #     "type": "set_osd_prm",
        #     "module": "AVS_REQUEST_MESSAGE",
        #     "body": {
        #         "channel": [
        #             {
        #                 "chan_id": i,
        #                 "osd_param": {
        #                     "date": {"enable": enable, "pos": 1310736, "date_format": 0},
        #                     "datetime": {"enable": enable, "pos": 58916891, "time_format": 1},
        #                     "usr_text": [
        #                         {"enable": enable, "context": "T1NEIFRleHQ=", "pos": 58590116, "color": 0, "font_size": 1},
        #                         {"enable": enable, "context": "T1NEIFRleHQ=", "pos": 655560, "color": 0, "font_size": 1},
        #                         {"enable": enable, "context": "T1NEIFRleHQ=", "pos": 655660, "color": 0, "font_size": 1},
        #                         {"enable": enable, "context": "T1NEIFRleHQ=", "pos": 655760, "color": 0, "font_size": 1},
        #                         {"enable": enable, "context": "T1NEIFRleHQ=", "pos": 655860, "color": 0, "font_size": 1}
        #                     ],
        #                     "font_size": 1,
        #                     "color": 0,
        #                     "align": 0
        #                 },
        #                 "realtime_show": {
        #                     "car_info": 0,
        #                     "event_type_enable": 0,
        #                     "extend_pos": 1,
        #                     "plate_pos": True,
        #                     "realtime_result": 1,
        #                     "virtualloop_area": 1
        #                 }
        #             } for i in range(7)
        #         ]
        #     }
        # }
        # print(close_osd_data)

        get_data = self.get_osd_para()
        if get_data["body"]["channel"] is None:
            print("get_data failed")
            return None
        try:
            channel_data = get_data["body"]["channel"]
            for one_dict in channel_data:
                one_dict["osd_param"]["date"]["enable"] = enable
                one_dict["osd_param"]["datetime"]["enable"] = enable
                for one_usr_text in one_dict["osd_param"]["usr_text"]:
                    one_usr_text["enable"] = enable
            print("ctrl_osd successful.")
        except Exception as e:
            print(f"An error occurred during ctrl_osd: {e}")
        close_osd_data = {
            "type": "set_osd_prm",
            "module": "AVS_REQUEST_MESSAGE",
            "body": {
                "channel": channel_data
            }
        }

        data = json.dumps(close_osd_data)

        try:
            resp = post(device=self.device, data=data)
            if not resp:
                return None
            print("close_osd:", resp)
            return json.loads(resp)
        except Exception as e:
            print("close_osd: exception", e)

    def reboot(self):
        if not self.device:
            return False

        # self.get_device_info()

        data_reboot = {
            "type": "reboot_dev",
            "module": "SS_BUS_REQUEST"
        }

        data = json.dumps(data_reboot)
        try:
            reboot_result = post(device=self.device, data=data)
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
