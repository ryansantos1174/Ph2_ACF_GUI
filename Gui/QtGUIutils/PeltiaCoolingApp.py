# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from cgi import test
from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5.QtWidgets import QWidget

class Peltia(QWidget):
    def __init__(self, dimension):
        super(Peltia, self).__init__()
        self.MainWindow = QtWidgets.QMainWindow()
        self.setupUi(self.MainWindow)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(532, 361)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.currentCurrentLabel = QtWidgets.QLabel(self.centralwidget)
        self.currentCurrentLabel.setObjectName("currentCurrentLabel")
        self.gridLayout.addWidget(self.currentCurrentLabel, 5, 1, 1, 1)
        self.lcdNumber = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdNumber.setObjectName("lcdNumber")
        self.gridLayout.addWidget(self.lcdNumber, 4, 1, 1, 1)
        self.currentTempDisplay = QtWidgets.QLCDNumber(self.centralwidget)
        self.currentTempDisplay.setObjectName("currentTempDisplay")
        self.gridLayout.addWidget(self.currentTempDisplay, 4, 0, 1, 1)
        self.currentHumidityLabel = QtWidgets.QLabel(self.centralwidget)
        self.currentHumidityLabel.setObjectName("currentHumidityLabel")
        self.gridLayout.addWidget(self.currentHumidityLabel, 5, 0, 1, 1)
        self.setTempButton = QtWidgets.QPushButton(self.centralwidget)
        self.setTempButton.setObjectName("setTempButton")
        self.gridLayout.addWidget(self.setTempButton, 1, 1, 1, 1)
        self.currentHumidityDisplay = QtWidgets.QLCDNumber(self.centralwidget)
        self.currentHumidityDisplay.setObjectName("currentHumidityDisplay")
        self.gridLayout.addWidget(self.currentHumidityDisplay, 6, 0, 1, 1)
        self.setTempInput = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.setTempInput.setObjectName("setTempInput")
        self.gridLayout.addWidget(self.setTempInput, 1, 0, 1, 1)
        self.lcdNumber_2 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdNumber_2.setObjectName("lcdNumber_2")
        self.gridLayout.addWidget(self.lcdNumber_2, 6, 1, 1, 1)
        self.currentVoltageLabel = QtWidgets.QLabel(self.centralwidget)
        self.currentVoltageLabel.setObjectName("currentVoltageLabel")
        self.gridLayout.addWidget(self.currentVoltageLabel, 2, 0, 1, 1)
        self.currentTempLabel = QtWidgets.QLabel(self.centralwidget)
        self.currentTempLabel.setObjectName("currentTempLabel")
        self.gridLayout.addWidget(self.currentTempLabel, 2, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 532, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.setTempButton.clicked.connect(self.setTemp)


        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "Set Temperature"))
        self.currentCurrentLabel.setText(_translate("MainWindow", "Current"))
        self.currentHumidityLabel.setText(_translate("MainWindow", "Humidity"))
        self.setTempButton.setText(_translate("MainWindow", "Set Temp"))
        self.currentVoltageLabel.setText(_translate("MainWindow", "Voltage"))
        self.currentTempLabel.setText(_translate("MainWindow", "Current Temp"))

    def setTemp(self):
        print(self.setTempInput.value() * 40)
        # Send temperature reading to device
    
    


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Peltia()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())