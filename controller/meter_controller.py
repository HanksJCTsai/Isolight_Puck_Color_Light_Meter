import os
import datetime
import string
import sys
import time
import traceback
import serial as serial_ports
import serial.tools.list_ports as list_ports
import logging

from enum import Enum
from PyQt5 import QtCore, QtGui, QtWidgets

from ui.ui_meter_page import Ui_meter_page_

class ui_control_enum(Enum):
    INIT = "INIT"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    STOP = "STOP"
    TESTCONNECT = "TESTCONNECT"

class meter_controller(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(meter_controller, self).__init__(parent=parent)
        self.parent = parent
        self.ui = Ui_meter_page_()
        self.ui.setupUi(self)
        # Combobox
        self.ui_port =  self.ui.port_cbb
        self.ui_baud_rate = self.ui.baudrate_cbb
        self.ui_data_bits = self.ui.databits_cbb
        self.ui_parity = self.ui.parity_cbb
        self.ui_stop_bits = self.ui.stopbits_cbb
        self.ui_sendcmds = self.ui.sendcmd_cbb
        # LCD Number
        self.ui_interval_counter = self.ui.intervaltime_ldn
        # Button
        self.ui_test_connect = self.ui.testconnect_btn
        self.ui_play = self.ui.play_btn
        self.ui_pause = self.ui.pause_btn
        self.ui_stop = self.ui.stop_btn
        self.ui_sendcmd = self.ui.sendcmd_btn
        # textLine
        self.ui_connect_status = self.ui.connectstatus_txta
        self.ui_threads_status = self.ui.threadsstatus_txta
        self.ui_sendcmd_logs = self.ui.sendcmd_txta
        self.ui_receive_logs = self.ui.receive_txta
        # lineEdit
        self.ui_grcct = self.ui.grcct_txt
        self.ui_grl = self.ui.grl_txt
        self.ui_grxyz_x = self.ui.grxyz_x_txt
        self.ui_grxyz_y = self.ui.grxyz_y_txt
        self.ui_grxyz_z = self.ui.grxyz_z_txt
        self.ui_gryxy_y1 = self.ui.gryxy_y1_txt
        self.ui_gryxy_x = self.ui.gryxy_x_txt
        self.ui_gryxy_y2 = self.ui.gryxy_y2_txt
        # Init value
        self.setUpControl()

    def setUpControl(self):
        # Set logger 
        self.logger = self.parent.logger
        self.logger.info("Meter page init")
        # Set Button Event
        self.ui_test_connect.clicked.connect(self.onButtonClicked)
        self.ui_play.clicked.connect(self.onButtonClicked)
        self.ui_pause.clicked.connect(self.onButtonClicked)
        self.ui_stop.clicked.connect(self.onButtonClicked)
        self.ui_sendcmd.clicked.connect(self.onButtonClicked)
        # Set combobox values
        self.ui_port.addItems(list(self.parent.serial_port_names))
        self.ui_baud_rate.addItems(list(self.parent.serial_port_baudrates))
        self.ui_parity.addItems(list(self.parent.serial_port_parity))
        self.ui_data_bits.addItems(list(self.parent.serial_port_databits))
        self.ui_stop_bits.addItems(list(self.parent.serial_port_stopbits))
        self.ui_sendcmds.addItems(self.parent.SendCMDList.split(","))
        # Set LCD Number
        self.ui_interval_counter.display(int(self.parent.IntervalTime))
        # Set value for config
        if self.parent.SerialPort != None and self.parent.SerialPort != "":
            self.ui_port.setCurrentIndex((list(self.parent.serial_port_names)).index(self.parent.SerialPort))
        if self.parent.DataBits != None and self.parent.DataBits != "":
            self.ui_data_bits.setCurrentIndex((list(self.parent.serial_port_databits)).index(self.parent.DataBits))
        if self.parent.StopBit != None and self.parent.StopBit != "":
            self.ui_stop_bits.setCurrentIndex((list(self.parent.serial_port_stopbits)).index(self.parent.StopBit))
        if self.parent.BaudRate != None and self.parent.BaudRate != "":
            self.ui_baud_rate.setCurrentIndex((list(self.parent.serial_port_baudrates)).index(self.parent.BaudRate))
        if self.parent.Parity != None and self.parent.Parity != "":
            self.ui_parity.setCurrentIndex((list(self.parent.serial_port_parity)).index(self.parent.Parity))
        if self.parent.TimeOut !=None or self.parent.TimeOut !="":
            self.timeout = (int(self.parent.TimeOut))
        else:
            self.timeout = 0
        if self.parent.IntervalTime !=None and self.parent.IntervalTime !="":
            self.intervaltime = (int(self.parent.IntervalTime))
        else:
            self.intervaltime = 0
        if self.parent.SendCMDList != None or len(self.parent.SendCMDList) > 0:
            self.autoSendCMDList = self.parent.SendCMDList
        # Set init UI
        self.toggleForSerOpenOrClose(ui_control_enum.INIT)
        # Set  Global
        global lightMeterSerialPort, receive_thread, conuttime_thread, toggle_resume
        conuttime_thread = None
        receive_thread = None
        lightMeterSerialPort = None
        toggle_resume = False

    def closeSerialPort(self):
        global lightMeterSerialPort
        try:
            new_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = ""
            port = (list(self.parent.serial_port_paths)[self.ui_port.currentIndex()])
            baudrate = self.ui_baud_rate.currentText()
            if lightMeterSerialPort != None:
                lightMeterSerialPort.close()
            msg = new_datetime + ": " + port + " is closeed " + baudrate + ".\n"
        except Exception as e:
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            msg =  new_datetime + ": " + port + " has error " + str(baudrate) +" :"+ errMsg
        finally:
            return msg 

    def openSerialPort(self, cmd:str = ""):
        global lightMeterSerialPort
        try:
            # new_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # if lightMeterSerialPort == None:
            msg = ""
            port = (list(self.parent.serial_port_paths)[self.ui_port.currentIndex()])
            baudrate = int(self.ui_baud_rate.currentText())
            parity = str(self.ui_parity.currentText())
            databits = int(self.ui_data_bits.currentText())
            stopbit = int(self.ui_stop_bits.currentText())
            timeout = self.timeout
            lightMeterSerialPort = serial_ports.Serial(port, baudrate, databits, parity[0].upper() , stopbit, timeout)
            if lightMeterSerialPort.isOpen() is True:
                msg = port + " is Opened " + str(baudrate) 
            else:
                msg = port + " is failed " + str(baudrate)
            if len(cmd) > 0:
                # lightMeterSerialPort.write(bytes(cmd + "\r",'ascii'))
                lightMeterSerialPort.write((cmd + "\r").encode())
                msg = "Send command to light meter by manual. " + cmd
        except Exception as e:
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            msg =  port + " has error " + str(baudrate) +" : " + errMsg
        finally:
            return msg

    def refreshLog(self, textEdit:QtWidgets.QPlainTextEdit ,message:str = ""):
        cursor = QtGui.QTextCursor(textEdit.document())
        cursor.setPosition(0)
        textEdit.setTextCursor(cursor)
        textEdit.insertPlainText(message)
    
    def refreshLogForReceiveLog(self ,message:str):
        cursor = QtGui.QTextCursor(self.ui_receive_logs.document())
        cursor.setPosition(0)
        self.ui_receive_logs.setTextCursor(cursor)
        self.ui_receive_logs.insertPlainText(message)

    def refreshLogForSendCMDLog(self ,message:str):
        cursor = QtGui.QTextCursor(self.ui_sendcmd_logs.document())
        cursor.setPosition(0)
        self.ui_sendcmd_logs.setTextCursor(cursor)
        self.ui_sendcmd_logs.insertPlainText(message)

    def onButtonClicked(self):
        global lightMeterSerialPort, conuttime_thread, receive_thread, toggle_resume
        sender = self.sender()
        status = ""
        msg = ""
        if sender == self.ui_test_connect :
            # self.toggleForSerOpenOrClose(ui_control_enum.TESTCONNECT)
            status = self.openSerialPort()
            self.refreshLog(self.ui_connect_status, status)
            self.logger.info(status)
        elif sender == self.ui_play:
            self.toggleForSerOpenOrClose(ui_control_enum.PLAY)
            if toggle_resume :
                conuttime_thread.resume()
                # receive_thread.resume()
            if conuttime_thread == None:
                status = self.openSerialPort()
                conuttime_thread = counterTimeThread(lightMeterSerialPort, self.intervaltime ,self.autoSendCMDList, self.logger)
                conuttime_thread.counter_signal.connect(self.ui_interval_counter.display)
                conuttime_thread.refreshsendcmdlog_signal.connect(self.refreshLogForSendCMDLog)
                conuttime_thread.start()
            if receive_thread == None:
                receive_thread = serialPortThread(lightMeterSerialPort, self.logger)
                receive_thread.grcct_signal.connect(self.ui_grcct.setText)
                receive_thread.grl_signal.connect(self.ui_grl.setText)
                receive_thread.grxyz_x_signal.connect(self.ui_grxyz_x.setText)
                receive_thread.grxyz_y_signal.connect(self.ui_grxyz_y.setText)
                receive_thread.grxyz_z_signal.connect(self.ui_grxyz_z.setText)
                receive_thread.gryxy_y1_signal.connect(self.ui_gryxy_y1.setText)
                receive_thread.gryxy_x_signal.connect(self.ui_gryxy_x.setText)
                receive_thread.gryxy_y2_signal.connect(self.ui_gryxy_y2.setText)
                receive_thread.refreshreceivecmdlog_signal.connect(self.refreshLogForReceiveLog)
                receive_thread.start()
            toggle_resume = False
            msg = (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ": Do to play.\n"
            self.refreshLog(self.ui_threads_status,msg)
            self.logger.info("Do to play.")
            self.logger.info(status)
        elif sender == self.ui_pause:
            self.toggleForSerOpenOrClose(ui_control_enum.PAUSE)
            if conuttime_thread != None:
                conuttime_thread.pause()
            # if receive_thread != None:
            #     receive_thread.pause()
            toggle_resume = True
            msg = (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ": Do to pause.\n"
            self.refreshLog(self.ui_threads_status, msg)
            self.logger.info("Do to pause.")
        elif sender == self.ui_stop:
            self.toggleForSerOpenOrClose(ui_control_enum.STOP)
            if conuttime_thread != None:
                conuttime_thread.stop()
            # if receive_thread != None:
            #     receive_thread.stop()
            msg = (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ": Do to stop.\n"
            self.refreshLog(self.ui_threads_status, msg)
            self.logger.info("Do to stop.")
        elif sender == self.ui_sendcmd:
            singleCMD = self.ui_sendcmds.currentText()
            status = self.openSerialPort(singleCMD)
            if receive_thread ==None:
                receive_thread = serialPortThread(lightMeterSerialPort, self.logger)
                receive_thread.grcct_signal.connect(self.ui_grcct.setText)
                receive_thread.grl_signal.connect(self.ui_grl.setText)
                receive_thread.grxyz_x_signal.connect(self.ui_grxyz_x.setText)
                receive_thread.grxyz_y_signal.connect(self.ui_grxyz_y.setText)
                receive_thread.grxyz_z_signal.connect(self.ui_grxyz_z.setText)
                receive_thread.gryxy_y1_signal.connect(self.ui_gryxy_y1.setText)
                receive_thread.gryxy_x_signal.connect(self.ui_gryxy_x.setText)
                receive_thread.gryxy_y2_signal.connect(self.ui_gryxy_y2.setText)
                receive_thread.refreshreceivecmdlog_signal.connect(self.refreshLogForReceiveLog)
                receive_thread.start()
            self.refreshLog(self.ui_sendcmd_logs, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + status + ".\n")
            self.logger.info(status)
            
    def toggleForSerOpenOrClose(self, toggle: ui_control_enum = ui_control_enum.INIT):
        # when tool initialize
        if toggle == ui_control_enum.INIT:
            # control combobox enabled
            self.ui_port.setEnabled(True)
            self.ui_data_bits.setEnabled(True)
            self.ui_baud_rate.setEnabled(True)
            self.ui_stop_bits.setEnabled(True)
            self.ui_parity.setEnabled(True)
            # control button enabled
            self.ui_test_connect.setEnabled(True)
            self.ui_play.setEnabled(True)
            self.ui_pause.setEnabled(False)
            self.ui_stop.setEnabled(False)
        elif toggle == ui_control_enum.TESTCONNECT:
            # control combobox enabled
            self.ui_port.setEnabled(False)
            self.ui_data_bits.setEnabled(False)
            self.ui_baud_rate.setEnabled(False)
            self.ui_stop_bits.setEnabled(False)
            self.ui_parity.setEnabled(False)
            # control button enabled
            self.ui_test_connect.setEnabled(True)
            self.ui_play.setEnabled(True)
            self.ui_pause.setEnabled(False)
            self.ui_stop.setEnabled(False)
        elif toggle == ui_control_enum.PLAY:
            # control combobox enabled
            self.ui_port.setEnabled(False)
            self.ui_data_bits.setEnabled(False)
            self.ui_baud_rate.setEnabled(False)
            self.ui_stop_bits.setEnabled(False)
            self.ui_parity.setEnabled(False)
            # control button enabled
            self.ui_test_connect.setEnabled(False)
            self.ui_play.setEnabled(False)
            self.ui_pause.setEnabled(True)
            self.ui_stop.setEnabled(False)
        elif toggle == ui_control_enum.PAUSE:
            # control combobox enabled
            self.ui_port.setEnabled(False)
            self.ui_data_bits.setEnabled(False)
            self.ui_baud_rate.setEnabled(False)
            self.ui_stop_bits.setEnabled(False)
            self.ui_parity.setEnabled(False)
            # control button enabled
            self.ui_test_connect.setEnabled(False)
            self.ui_play.setEnabled(True)
            self.ui_pause.setEnabled(False)
            self.ui_stop.setEnabled(True)
        elif toggle == ui_control_enum.STOP:
            # control combobox enabled
            self.ui_port.setEnabled(True)
            self.ui_data_bits.setEnabled(True)
            self.ui_baud_rate.setEnabled(True)
            self.ui_stop_bits.setEnabled(True)
            self.ui_parity.setEnabled(True)
            # control button enabled
            self.ui_test_connect.setEnabled(True)
            self.ui_play.setEnabled(True)
            self.ui_pause.setEnabled(False)
            self.ui_stop.setEnabled(False)

class counterTimeThread(QtCore.QThread):
    counter_signal = QtCore.pyqtSignal(int)
    refreshsendcmdlog_signal = QtCore.pyqtSignal(str)
    receiveforserialport_signal = QtCore.pyqtSignal(list)
    exception_signal = QtCore.pyqtSignal(str)
    
    def __init__(self, serialport, intervaltime:int, sendCMD:string, logger):
        super(counterTimeThread, self).__init__()
        self.ispause = False
        self.isstop = False
        self.intervaltime = intervaltime
        self.autosendcmd = sendCMD.replace(",","\r")
        self.ser = serialport
        self.cond = QtCore.QWaitCondition()
        self.mutex = QtCore.QMutex()
        self.logger = logger

    def run(self):
        try:
            self.i = self.intervaltime
            while not self.ispause:        
                time.sleep(1)
                self.mutex.lock()
                if self.ispause:
                    self.i += 1
                    self.cond.wait(self.mutex)
                elif self.isstop:
                    self.i = self.intervaltime
                    self.counter_signal.emit(self.intervaltime)
                    self.mutex.unlock()
                    break
                elif self.i == 0:
                    self.counter_signal.emit(self.i)
                    # send CMD to meter
                    self.ser.write((self.autosendcmd).encode())
                    self.refreshsendcmdlog_signal.emit((datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ": Auto send CMD: " + self.autosendcmd.replace("\r"," ") + "\n")
                    self.logger.info("Auto send CMD: " + self.autosendcmd.replace("\r"," "))
                    self.i = self.intervaltime
                else : 
                    self.counter_signal.emit(self.i) 
                    self.i -=1
                self.mutex.unlock()
        except Exception as e:
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            self.logger.error(errMsg)
            self.exception_signal.emit(errMsg)
        finally:
            self.mutex.unlock()

    def pause(self):
        self.ispause = True

    def resume(self):
        self.ispause = False
        self.isstop = False
        self.cond.wakeAll()

    def stop(self):
        self.ispause = False
        self.isstop = True
        self.i = self.intervaltime
        self.counter_signal.emit(self.intervaltime)

class serialPortThread(QtCore.QThread):
    # refresh UI value of grcct, grl, grxyz, gryxy
    grcct_signal = QtCore.pyqtSignal(str)
    grl_signal = QtCore.pyqtSignal(str)
    grxyz_x_signal = QtCore.pyqtSignal(str)
    grxyz_y_signal = QtCore.pyqtSignal(str)
    grxyz_z_signal = QtCore.pyqtSignal(str)
    gryxy_y1_signal = QtCore.pyqtSignal(str)
    gryxy_x_signal = QtCore.pyqtSignal(str)
    gryxy_y2_signal = QtCore.pyqtSignal(str)
    refreshreceivecmdlog_signal = QtCore.pyqtSignal(str)
    # Exception singal
    exception_signal = QtCore.pyqtSignal(str)

    def __init__(self, serialport:serial_ports, logger:logging):
        super(serialPortThread, self).__init__()
        self.playing = False
        self.isstop = False
        self.ser = serialport
        self.cond = QtCore.QWaitCondition()
        self.mutex = QtCore.QMutex()
        self.logger = logger

    def run(self):
        try:
            self.playing = True
            while self.playing:
                self.mutex.lock()
                if not self.playing:
                    self.cond.wait(self.mutex)
                if self.isstop:
                    self.mutex.unlock()
                    break
                if self.ser.inWaiting() > 0:   
                    time.sleep(0.1)
                    result = (lightMeterSerialPort.read_all()).decode()
                    meterValues = ((result).replace(">","").replace("\x1bEGRCCT",",").replace("\x1bEGRL",",").replace("\x1bEGRXYZ 0",",").replace("\x1bEGRYXY 0",","))
                    meterValuesList = meterValues.split("\r\n")
                    for response in meterValuesList:
                        if len(response) > 0:
                            responseList = response.split(",")
                            if len(responseList) > 1 :
                                if str(responseList[0]).upper() == "GRCCT":
                                    self.grcct_signal.emit(str(responseList[1]))
                                elif str(responseList[0]).upper() == "GRL":
                                    self.grl_signal.emit(str(responseList[1]))
                                elif str(responseList[0]).upper() == "GRXYZ":
                                    self.grxyz_x_signal.emit(str(responseList[1]))
                                    self.grxyz_y_signal.emit(str(responseList[2]))
                                    self.grxyz_z_signal.emit(str(responseList[3]))
                                elif str(responseList[0]).upper() == "GRYXY":
                                    self.gryxy_y1_signal.emit(str(responseList[1]))
                                    self.gryxy_x_signal.emit(str(responseList[2]))
                                    self.gryxy_y2_signal.emit(str(responseList[3]))
                    self.refreshreceivecmdlog_signal.emit((datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ": Receive data :" + meterValues.replace("\r\n","") + "\n")
                    self.logger.info("Receive data: " + meterValues.replace("\r\n","  "))
                self.mutex.unlock()
        except Exception as e:
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            self.logger.error(errMsg)
            self.exception_signal.emit(errMsg)
        finally:
            self.mutex.unlock()
    
    def pause(self):
        self.playing = False

    def resume(self):
        self.playing = True
        self.cond.wakeAll()

    def stop(self):
        self.isstop = True