"""
server.py
author: Zicheng Zeng
date: 2023/5/10
description: 本地服务器端口操作
"""
import threading

from module.common import function
import signal
from threading import Thread


class WebServer:
    def __init__(self, cmd, cwd):
        """
        :param cmd: 服务器运行 command
        :param cwd: 命令执行路径
        """
        self._cmd = cmd
        self._cwd = cwd
        self._server = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("class server exit")
        self.stop()

    def run(self):
        self._server = function.shell_command(self._cmd, cwd=self._cwd)

    def stop(self):
        self._server.send_signal(signal.CTRL_C_EVENT)
