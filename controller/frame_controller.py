
import os
import pathlib
import json
import logging

import serial as serial_ports
import serial.tools.list_ports as list_ports

from logging.handlers import TimedRotatingFileHandler
from PyQt5 import QtCore, QtGui, QtWidgets

from ui.ui_main_page import Ui_MainWindow
from controller.meter_controller import meter_controller
from controller.setting_controller import setting_controller


class frame_controller(QtWidgets.QMainWindow):
    SerialPort = ""
    DataBits = "8"
    StopBit = "1"
    BaudRate = ""
    Parity = ""
    TimeOut = 0
    IntervalTime = 0
    SendCMDList = ""
    LogFileName = ""
    serial_port_paths = list("")
    serial_port_names = list("")
    serial_port_databits = list("")
    serial_port_stopbits = list("")
    serial_port_baudrates = list("")
    serial_port_parity = list("")
    logger = None
    def __init__(self, parent = None):
        super(frame_controller, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_control_()

    def _setup_control_(self):
        self.getSettings()
        self.scanCenter()
        self.initCombobox()
        self.initLogging()
        self.initMenubar()

    def initLogging(self):
        # logname = "Logs.log"
        logname = self.LogFileName
        handler = TimedRotatingFileHandler(logname, when="midnight", interval=1)
        handler.suffix = "%Y%m%d"
        
        self.logger = logging.getLogger(name='RUN')
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info("Claire tools init")
        

    def initCombobox(self):
        self.serial_port_paths, self.serial_port_names = self.getUsbInfo()
        self.serial_port_baudrates, self.serial_port_databits, self.serial_port_parity, self.serial_port_stopbits = self.initComboboxValues()

    def scanCenter(self):
        _screen_ = QtWidgets.QDesktopWidget().screenGeometry()
        _size_ = self.geometry()
        self.move((_screen_.width() - _size_.width()) / 2, (_screen_.height() - _size_.height()) / 2)
    
    def initMenubar(self):
        _actionSetting_Serial_Port = self.ui.actionSetting_Serial_Port
        _actionMonitor = self.ui.actionMonitor
        _actionSetting_Serial_Port.triggered.connect(self.switchPage)
        _actionMonitor.triggered.connect(self.switchPage)
        self.ui.stackedWidget.insertWidget(0,meter_controller(self))
        self.ui.stackedWidget.insertWidget(1,setting_controller(self))

    def switchPage(self):
        sender = self.sender()
        if sender == self.ui.actionMonitor:
            print("0")
            self.ui.stackedWidget.setCurrentIndex(0)
        elif sender == self.ui.actionSetting_Serial_Port:
            print("1")
            self.ui.stackedWidget.setCurrentIndex(1)
        else:
            print("0")
            self.ui.stackedWidget.setCurrentIndex(0) 

    def processTrigger(self, message, times=50000):
        self.ui.statusbar.showMessage(message ,times)
    
    def event(self, QEvent):
        if QEvent.type() == QEvent.StatusTip:
            if QEvent.tip() == "":
                QEvent = QtGui.QStatusTipEvent("Menu bar")  # 此处为要始终显示的内容
        return super().event(QEvent)
    
    def getUsbInfo(self):
        _serial_ports = ""
        _serial_ports_name = ""
        if os.name == "nt":
            # windows
            _comports = [port for port in list_ports.comports()]
            if _comports.__len__() > 0:
                _serial_ports = [p for p in _comports[0]]
                _serial_ports_name = [p for p in _comports.name]
            else :
                _serial_ports = []
                _serial_ports_name = []
        else :
            _serial_ports = [port[0] for port in list_ports.comports()]
            _serial_ports_name = [port.name for port in list_ports.comports()]
        return _serial_ports, _serial_ports_name
        
    def initComboboxValues(self):
        '''
        :return: Baud rate, Data bits, Parity, Stop bits
        '''
        _baud_rates = ["300", "1200", "2400", "9600", "19200", "38400", "115200"]
        _data_bits = ["5", "6", "7", "8"]
        _parity = ["None", "Even", "Odd", "Mark", "Space"]
        _stop_bits = ["1","1.5", "2"]
        return _baud_rates, _data_bits, _parity, _stop_bits

    def getSettings(self):
        _json_file_ = pathlib.Path("_serial_port_.json")
        if _json_file_.exists() == False:
            _setting_dict_ = { "Port Path": "","Baud Rate": 115200, "Parity": "N", "Data Bits": 8, "Stop Bit": 1, "Time Out": 10, "Interval Time": 10, "Send CMD List":"GRCCT,GRL,GRXYZ,GRYXY,", "Log File Name":"Log.log"}
            # Serializing json
            _json_object_ = json.dumps(_setting_dict_)
            # Writing to sample.json
            with open("_serial_port_.json", "w") as outfile:
                outfile.write(_json_object_)
        
        with open("_serial_port_.json","r") as openfile:
            # Reading from json file
            _read_dict_ = json.load(openfile)
        self.SerialPort = _read_dict_["Port Path"]
        self.BaudRate = _read_dict_["Baud Rate"]
        self.Parity = _read_dict_["Parity"]
        self.DataBits = _read_dict_["Data Bits"]
        self.StopBit = _read_dict_["Stop Bit"]
        self.TimeOut = _read_dict_["Time Out"]
        self.IntervalTime = _read_dict_["Interval Time"]
        self.SendCMDList = _read_dict_["Send CMD List"]
        self.LogFileName = _read_dict_["Log File Name"]

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message', "Do you want to exit?",
                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        # 判断返回值，如果点击的是Yes按钮，我们就关闭组件和应用，否则就忽略关闭事件
        if reply == QtWidgets.QMessageBox.Yes:
            self.save_cfg()
            event.accept()
        else:
            event.ignore()
