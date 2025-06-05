# Created by Yossy on 2025/05/31

import subprocess
import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui

from generate_obs_config import generate_obs_config

PYTHON = 'python'
VENV = '.venv\\Scripts\\python.exe'
if os.path.isfile(VENV):
    PYTHON = VENV

class MainWidget(QtWidgets.QWidget):

    process = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AC6 Overlay Control')
        self.button_start = QtWidgets.QPushButton('Start')
        self.button_stop = QtWidgets.QPushButton('Stop')
        self.button_generate_obsconfig = QtWidgets.QPushButton('Generate OBS Config')

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.button_start)
        layout.addWidget(self.button_stop)
        layout.addWidget(self.button_generate_obsconfig)

        # Setup connections 
        self.button_start.clicked.connect(self.start_process)
        self.button_stop.clicked.connect(self.kill_process)
        self.button_generate_obsconfig.clicked.connect(self.generate_obs_config)

    @QtCore.Slot() 
    def start_process(self):
        if self.process:
            self.kill_process()
        self.process = subprocess.Popen(([PYTHON, '-m', 'streamlit', 'run', 'controller.py']))

    @QtCore.Slot()
    def kill_process(self):
        subprocess.Popen.kill(self.process)

    @QtCore.Slot()
    def generate_obs_config(self):
        "Generate OBS config from a template"
        generate_obs_config()


def run_application():
    app = QtWidgets.QApplication([])
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    run_application()
