#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLabel


class Video:
    rotate: int = 0

    label: QLabel = None
    timer: QTimer = None
