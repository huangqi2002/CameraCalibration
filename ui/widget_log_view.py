#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ui.ui_base import BaseView
from ui.ui_widget_log_view import Ui_WidgetLogView


class WidgetLogView(BaseView, Ui_WidgetLogView):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

