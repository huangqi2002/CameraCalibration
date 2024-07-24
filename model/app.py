#!/usr/bin/env python3
# -*- coding: utf-8 -*-
class App:
    version_app = "v1.2.7"

    work_path_root: str
    work_path_configs: str
    work_path_internal: str
    work_path_external: str

    config_model = None
    config_stream = None
    config_video = None

    config_fg = None

    device_model = None

    video_server = None  # 标签与播放地址对应关系
    camera_list = {}  # 相机与标签对应关系

    login_retry_max_count = 20
    is_connected = False
    show_log_view = False

    # 用于求取外参的内参路径
    config_ex_internal_path = None


app_model = App()
