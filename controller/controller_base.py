#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject

from utils.log_util import Log


class BaseController(QObject):
    def __init__(self, base_view, base_model=None):
        super().__init__()
        self.view = base_view
        self.model = base_model

        self.log = Log()
        self.init()

    def init(self):
        pass
