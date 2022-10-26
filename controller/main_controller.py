import os
import serial as serial_ports
import serial.tools.list_ports as list_ports

from PyQt5 import QtCore, QtGui, QtWidgets
# from ui.Ui_main_page import Ui_mainWindow

class main_controller(QtWidgets.QMainWindow):
    # def __init__(self):
    #     super().__init__()
    #     self.ui = Ui_mainWindow()
    #     self.ui.setupUi(self)
    #     self.setup_control()
    
    def setup_control(self):
        self.serial_port_paths, self.serial_port_names = self.getUsb_info()
        baud_rates = self.setBaudRate_info()
        # self.clicked_counter = 0
        self.ui.cleanBtn.clicked.connect(self.onButtonClicked)
        self.ui.senedBtn.clicked.connect(self.onButtonClicked)
        # About connection / disconnection
        self.ui.connectBtn.clicked.connect(self.onButtonClicked)
        self.ui.DisconnectBtn.clicked.connect(self.onButtonClicked)
        self.ui.portNameCbb.addItems(list(self.serial_port_names))
        self.ui.baudRateCbb.addItems(list(baud_rates))
    
    def onButtonClicked(self):
        sender = self.sender()
        if sender == self.ui.cleanBtn:
            print(f"You clicked {sender.objectName()}.")
        elif sender == self.ui.senedBtn:
            print(f"You clicked {sender.objectName()}.")
        elif sender ==  self.ui.connectBtn:
            uart, msg = self.openSerial_port()
        else:
            print(f"? clicked {sender.objectName()}.")
    
    def getUsb_info(self):
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
    
    def setBaudRate_info(self):
        _baud_rates = ["300", "1200", "2400", "9600", "19200", "38400", "115200"]
        return _baud_rates

    def openSerial_port(self):
        msg = ""
        port = list(self.serial_port_paths)[self.ui.portNameCbb.currentIndex()]
        baudrate = "115200"
        parity = "N"
        databits = 8
        stopbit = 1
        timeout = 10
        uart = serial_ports.Serial(port, baudrate, databits, parity, stopbit, timeout)
        if uart.isOpen() is True:
            msg = port + "is Opened " + baudrate
        else:
            msg = port + "is failed " + baudrate
        return uart, msg