#!/usr/bin/env python3
# -*- coding: utf-8 -*-
class Device:
    ip: str = ""
    sn: str = ""
    username = "admin"
    password = "admin1"
    board_version: int = ""

    url_host: str = ""

    device_type: str = ""
    session = None
    heart_timer = None
