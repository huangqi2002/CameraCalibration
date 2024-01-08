#!/usr/bin/env python3
# -*- coding: utf-8 -*-
class Camera:
    is_open: bool = False
    rtsp_url: str = None

    frame = None
    fps = 10
    frame_time = int(1000 / fps)
    frame_error_count = 0

    cap = None
