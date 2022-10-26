import os
import serial as serial_ports
import serial.tools.list_ports as list_ports

from PyQt5 import QtCore, QtGui, QtWidgets
from ui.ui_setting_page import Ui_setting_page

class setting_controller(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(setting_controller, self).__init__(parent=parent)
        self.ui = Ui_setting_page()
        self.parent = parent
        self.ui.setupUi(self)
        self.setup_control()

    def setup_control(self):
        ""
