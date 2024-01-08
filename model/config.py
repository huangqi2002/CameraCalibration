#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os.path


class Config:
    def __init__(self, config_file):
        self.config_file = config_file

    def read_config_file(self, config_type):
        path = os.path.join(self.config_file, config_type)
        with open(path, encoding="utf-8", errors="ignore") as f:
            result = json.load(f)
        return result
