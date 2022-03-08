from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import (QPixmap, QTextCursor, QColor)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateTimeEdit,
		QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPlainTextEdit,
		QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
		QSlider, QSpinBox, QStyleFactory, QTableView, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QTreeWidget, QHBoxLayout,
		QVBoxLayout, QWidget, QMainWindow, QMessageBox, QSplitter)

import sys
import os
import re
import subprocess
import threading
import time
from datetime import datetime
import random
from subprocess import Popen, PIPE

from Gui.GUIutils.DBConnection import *
from Gui.GUIutils.guiUtils import *
#from Gui.QtGUIutils.QtStartWindow import *
from Gui.QtGUIutils.QtCustomizeWindow import *
from Gui.QtGUIutils.QtTableWidget import *
from Gui.QtGUIutils.QtMatplotlibUtils import *
from Gui.QtGUIutils.QtLoginDialog import *
from Gui.python.ResultTreeWidget import *
from Gui.python.TestValidator import *
from Gui.python.ANSIColoringParser import *

class TestHandler(QObject):
	backSignal = pyqtSignal(object)
	haltSignal = pyqtSignal(object)
	finishSingal = pyqtSignal(object)
	proceedSignal = pyqtSignal(object)
	outputString = pyqtSignal(object)
	stepFinished = pyqtSignal(object)

	def __init__(self,master,info,firmware):
		super(TestHandler,self).__init__()
		self.master = master
		self.master.globalStop.connect(self.urgentStop)
		self.firmware = firmware
		self.info = info
		self.connection = self.master.connection
		self.firmwareName = self.firmware.getBoardName()
		self.ModuleMap = dict()
		self.ModuleType = self.firmware.getModuleByIndex(0).getModuleType()
		self.RunNumber = "-1"

		self.processingFlag = False
		self.ProgressBarList = []
		self.input_dir = ''
		self.output_dir = ''
		self.config_file = '' #os.environ.get('GUI_dir')+ConfigFiles.get(self.calibration, "None")
		self.rd53_file  = {}
		self.grade = -1
		self.currentTest = ""
		self.outputFile = ""
		self.errorFile = ""

		self.autoSave = False

		self.runNext = threading.Event()
		self.testIndexTracker = -1
		self.listWidgetIndex = 0
		self.outputDirQueue = []
		#Fixme: QTimer to be added to update the page automatically
		self.grades = []
		self.modulestatus = []

		self.run_process = QProcess(self)
		self.run_process.readyReadStandardOutput.connect(self.on_readyReadStandardOutput)
		self.run_process.finished.connect(self.on_finish)
		self.readingOutput = False
		self.ProgressingMode = "None"
		self.ProgressValue = 0
		self.runtimeList = []
		self.info_process = QProcess(self)
		self.info_process.readyReadStandardOutput.connect(self.on_readyReadStandardOutput_info)

		self.initializeRD53Dict()

	def  initializeRD53Dict(self):
		self.rd53_file = {}
		beboardId = 0
		for module in self.firmware.getAllModules().values():

			ogId = module.getOpticalGroupID()
			moduleName = module.getModuleName()
			moduleId = module.getModuleID()
			moduleType = module.getModuleType()
			for i in range(BoxSize[moduleType]):
				self.rd53_file["{0}_{1}_{2}".format(moduleName,moduleId,i)] = None
			fwPath = "{0}_{1}_{2}".format(beboardId,ogId,moduleId)
			self.ModuleMap[fwPath] = moduleName
	def configTest(self):
		try:
			RunNumberFileName = os.environ.get('Ph2_ACF_AREA')+"/test/RunNumber.txt"
			if os.path.isfile(RunNumberFileName):
				runNumberFile = open(RunNumberFileName,"r")
				runNumberText = runNumberFile.readlines()
				self.RunNumber = runNumberText[0].split('\n')[0]
				logger.info("RunNumber: {}".format(self.RunNumber))
		except:
			logger.warning("Failed to retrive RunNumber")
		

		if self.currentTest == "" and isCompositeTest(self.info[1]):
			testName = CompositeList[self.info[1]][0]
		elif self.currentTest ==  None:
			testName = self.info[1]
		else:
			testName = self.currentTest

		ModuleIDs = []
		for module in self.firmware.getAllModules().values():
			#ModuleIDs.append(str(module.getModuleID()))
			ModuleIDs.append(str(module.getModuleName()))
			
		self.output_dir, self.input_dir = ConfigureTest(testName, "_Module".join(ModuleIDs), self.output_dir, self.input_dir, self.connection)

		for key in self.rd53_file.keys():
			if self.rd53_file[key] == None:
				self.rd53_file[key] = os.environ.get('Ph2_ACF_AREA')+"/settings/RD53Files/CMSIT_RD53.txt"
		if self.input_dir == "":
			SetupRD53ConfigfromFile(self.rd53_file,self.output_dir)
		else:
			SetupRD53Config(self.input_dir,self.output_dir, self.rd53_file)

		if self.input_dir == "":
			if self.config_file == "":
				tmpDir = os.environ.get('GUI_dir') + "/Gui/.tmp"
				if not os.path.isdir(tmpDir)  and os.environ.get('GUI_dir'):
					try:
						os.mkdir(tmpDir)
						logger.info("Creating "+tmpDir)
					except:
						logger.warning("Failed to create "+tmpDir)
				config_file = GenerateXMLConfig(self.firmware,self.currentTest,tmpDir)
				#config_file = os.environ.get('GUI_dir')+ConfigFiles.get(testName, "None")
				if config_file:
					SetupXMLConfigfromFile(config_file,self.output_dir,self.firmwareName,self.rd53_file)
				else:
					logger.warning("No Valid XML configuration file")
				#QMessageBox.information(None,"Noitce", "Using default XML configuration",QMessageBox.Ok)
			else:
				SetupXMLConfigfromFile(self.config_file,self.output_dir,self.firmwareName,self.rd53_file)
		else:
			if self.config_file != "":
				SetupXMLConfigfromFile(self.config_file,self.output_dir,self.firmwareName,self.rd53_file)
			else:
				tmpDir = os.environ.get('GUI_dir') + "/Gui/.tmp"
				if not os.path.isdir(tmpDir)  and os.environ.get('GUI_dir'):
					try:
						os.mkdir(tmpDir)
						logger.info("Creating "+tmpDir)
					except:
						logger.warning("Failed to create "+tmpDir)
				config_file = GenerateXMLConfig(self.firmware,self.currentTest,tmpDir)
				#config_file = os.environ.get('GUI_dir')+ConfigFiles.get(testName, "None")
				if config_file:
					SetupXMLConfigfromFile(config_file,self.output_dir,self.firmwareName,self.rd53_file)
				else:
					logger.warning("No Valid XML configuration file")

				# To be remove:
				#config_file = os.environ.get('GUI_dir')+ConfigFiles.get(testName, "None")
				#SetupXMLConfigfromFile(config_file,self.output_dir,self.firmwareName,self.rd53_file)
				#SetupXMLConfig(self.input_dir,self.output_dir)

		self.initializeRD53Dict()
		self.config_file = ""
		return

	def saveConfigs(self):
		for key in self.rd53_file.keys():
			try:
				os.system("cp {0}/test/CMSIT_RD53_{1}.txt {2}/CMSIT_RD53_{1}_OUT.txt".format(os.environ.get("Ph2_ACF_AREA"),key,self.output_dir))
			except:
				print("Failed to copy {0}/test/CMSIT_RD53_{1}.txt {2}/CMSIT_RD53_{1}_OUT.txt".format(os.environ.get("Ph2_ACF_AREA"),key,self.output_dir))

	def resetConfigTest(self):
		self.input_dir = ""
		self.output_dir = ""
		self.config_file = ""
		self.initializeRD53Dict()

	def initialTest(self):
		if "Re" in self.RunButton.text():
			self.grades = []
			if isCompositeTest(self.info[1]):
				for index in range(len(CompositeList[self.info[1]])):
					self.ResultWidget.ProgressBar[index].setValue(0)
			else:
				self.ResultWidget.ProgressBar[0].setValue(0)

	def runTest(self):
		self.ResetButton.setDisabled(True)
		#self.ControlLayout.removeWidget(self.RunButton)
		#self.RunButton.deleteLater()
		#self.ControlLayout.addWidget(self.ContinueButton,1,0,1,1)
		testName = self.info[1]

		self.input_dir = self.output_dir
		self.output_dir = ""

		#self.StatusCanvas.renew()
		#self.StatusCanvas.update()
		#self.HistoryLayout.removeWidget(self.StatusCanvas)
		#self.HistoryLayout.addWidget(self.StatusCanvas)

		if isCompositeTest(testName):
			self.runCompositeTest(testName)
		elif isSingleTest(testName):
			self.runSingleTest(testName)
		else:
			QMessageBox.information(None, "Warning", "Not a valid test", QMessageBox.Ok)
			return

	def runCompositeTest(self,testName):
		if self.haltSignal:
			return
		if self.testIndexTracker == len(CompositeList[self.info[1]]):
			self.testIndexTracker = 0
			return
		testName = CompositeList[self.info[1]][self.testIndexTracker]
		self.runSingleTest(testName)


	def runSingleTest(self,testName):
		self.starttime = None
		self.ProgressingMode = "None"
		self.currentTest = testName
		self.configTest()
		self.outputFile = self.output_dir + "/output.txt"
		self.errorFile = self.output_dir + "/error.txt"
		if os.path.exists(self.outputFile):
			self.outputfile = open(self.outputFile,"a")
		else:
			self.outputfile = open(self.outputFile,"w")
		#self.ContinueButton.setDisabled(True)
		#self.run_process.setProgram()
		self.info_process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
		self.info_process.setWorkingDirectory(os.environ.get("Ph2_ACF_AREA")+"/test/")
		self.info_process.start("echo",["Running COMMAND: CMSITminiDAQ  -f  CMSIT.xml  -c  {}".format(Test[self.currentTest])])
		self.info_process.waitForFinished()

		self.run_process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
		self.run_process.setWorkingDirectory(os.environ.get("Ph2_ACF_AREA")+"/test/")
		#self.run_process.setStandardOutputFile(self.outputFile)
		#self.run_process.setStandardErrorFile(self.errorFile)
		
		#self.run_process.start("python", ["signal_generator.py"])
		#self.run_process.start("tail" , ["-n","6000", "/Users/czkaiweb/Research/Ph2_ACF_GUI/Gui/forKai.txt"])
		#self.run_process.start("./SignalGenerator")

		if Test[self.currentTest] in ["pixelalive","noise","latency","injdelay","clockdelay","threqu","thrmin","scurve","gainopt","thradj","physics","gain"]:
			self.run_process.start("CMSITminiDAQ", ["-f","CMSIT.xml", "-c", "{}".format(Test[self.currentTest])])
		else:
			self.info_process.start("echo",["test {} not runnable, quitting...".format(Test[self.currentTest])])
	

		#self.run_process.start("ping", ["-c","5","www.google.com"])
		#self.run_process.waitForFinished()
		self.displayResult()
		

		#Question = QMessageBox()
		#Question.setIcon(QMessageBox.Question)
		#Question.setWindowTitle('SingleTest Finished')
		#Question.setText('Save current result and proceed?')
		#Question.setStandardButtons(QMessageBox.No| QMessageBox.Save | QMessageBox.Yes)
		#Question.setDefaultButton(QMessageBox.Yes)
		#customizedButton = Question.button(QMessageBox.Save)
		#customizedButton.setText('Save Only')
		#reply  = Question.exec_()

		#if reply == QMessageBox.Yes or reply == QMessageBox.Save:
		#	self.saveTest()
		#if reply == QMessageBox.No or reply == QMessageBox.Save:
		#	self.haltSignal = True
		#self.refreshHistory()
		#self.finishSingal = False


	def abortTest(self):
		reply = QMessageBox.question(None, "Abort", "Are you sure to abort?", QMessageBox.No | QMessageBox.Yes, QMessageBox.No)

		if reply == QMessageBox.Yes:
			self.run_process.kill()
			self.haltSignal = True
			self.sendProceedSignal()
			self.starttime = None
		else:
			return
		self.RunButton.setText("Re-run")
		self.RunButton.setDisabled(False)
	
	def urgentStop(self):
		self.run_process.kill()
		self.haltSignal = True
		self.sendProceedSignal()

		self.RunButton.setText("Re-run")
		self.RunButton.setDisabled(True)

	def validateTest(self):
		try:
			status = True
			# Fixme: the grading for test results
			grade, passmodule = ResultGrader(self.output_dir, self.currentTest, self.RunNumber, self.ModuleMap)
			self.grades.append(grade)
			self.modulestatus.append(passmodule)
		
			self.ResultWidget.StatusLabel[self.testIndexTracker-1].setText("Pass")
			self.ResultWidget.StatusLabel[self.testIndexTracker-1].setStyleSheet("color: green")
			for module in passmodule.values():
				if False in module.values():
					status = False
					self.ResultWidget.StatusLabel[self.testIndexTracker-1].setText("Failed")
					self.ResultWidget.StatusLabel[self.testIndexTracker-1].setStyleSheet("color: red")
		

			time.sleep(0.5)
			return status
		#self.StatusCanvas.renew()
		#self.StatusCanvas.update()
		#self.HistoryLayout.removeWidget(self.StatusCanvas)
		#self.HistoryLayout.addWidget(self.StatusCanvas)
		except Exception as err:
			logger.error(err)

	def saveTest(self):
		#if self.parent.current_test_grade < 0:
		if self.run_process.state() == QProcess.Running:
			QMessageBox.critical(self,"Error","Process not finished",QMessageBox.Ok)
			return

		try:
			if self.RunNumber == "-1":
				os.system("cp {0}/test/Results/Run000000*.root {1}/".format(os.environ.get("Ph2_ACF_AREA"),self.output_dir))
				#os.system("cp {0}/test/Results/Run000000*.txt {1}/".format(os.environ.get("Ph2_ACF_AREA"),self.output_dir))
				#os.system("cp {0}/test/Results/Run000000*.xml {1}/".format(os.environ.get("Ph2_ACF_AREA"),self.output_dir))
			else:
				os.system("cp {0}/test/Results/Run{1}*.root {2}/".format(os.environ.get("Ph2_ACF_AREA"),self.RunNumber,self.output_dir))
				#os.system("cp {0}/test/Results/Run{1}*.txt {2}/".format(os.environ.get("Ph2_ACF_AREA"),self.RunNumber,self.output_dir))
				#os.system("cp {0}/test/Results/Run{1}*.xml {2}/".format(os.environ.get("Ph2_ACF_AREA"),self.RunNumber,self.output_dir))
		except:
			print("Failed to copy file to output directory")

	def saveTestToDB(self):
		if isActive(self.connection) and self.autoSave:
			try:
				localDir = self.output_dir
				getFiles = subprocess.run('find {0} -mindepth 1  -maxdepth 1 -type f -name "*.root"  '.format(localDir), shell=True, stdout=subprocess.PIPE)
				fileList = getFiles.stdout.decode('utf-8').rstrip('\n').split('\n')
				moduleList = [module for module in localDir.split('_') if "Module" in module]

				if fileList  == [""]:
					logger.warning("No ROOT file found in the local folder, skipping...")
					return

				## Submit all files
				for submitFile in fileList:
					data_id = hashlib.md5('{}'.format(submitFile).encode()).hexdigest()
					if not self.checkRemoteFile(data_id):
						self.uploadFile(submitFile, data_id)

					## Submit records for all modules
					for module in moduleList:
						#print ("Module is {0}".format(module))
						module_id = module.strip('Module')
						#print ("Module_ID is {0}".format(module_id))
						getConfigInFiles = subprocess.run('find {0} -mindepth 1  -maxdepth 1 -type f -name "CMSIT_RD53_{1}_*_IN.txt"  '.format(localDir,module_id), shell=True, stdout=subprocess.PIPE) #changed module_id to module
						configInFileList = getConfigInFiles.stdout.decode('utf-8').rstrip('\n').split('\n')
						getConfigOutFiles = subprocess.run('find {0} -mindepth 1  -maxdepth 1 -type f -name "CMSIT_RD53_{1}_*_OUT.txt"  '.format(localDir,module_id), shell=True, stdout=subprocess.PIPE) #changed module_id to module
						configOutFileList = getConfigOutFiles.stdout.decode('utf-8').rstrip('\n').split('\n')
						getXMLFiles = subprocess.run('find {0} -mindepth 1  -maxdepth 1 -type f -name "*.xml"  '.format(localDir), shell=True, stdout=subprocess.PIPE)
						XMLFileList = getXMLFiles.stdout.decode('utf-8').rstrip('\n').split('\n')
						configcolumns = []
						configdata = []
						for configInFile in configInFileList:
							if configInFile != [""]:
								configcolumns.append("Chip{}InConfig".format(configInFile.split('_')[-2]))
								configInBuffer = open(configInFile,'rb')
								configInBin = configInBuffer.read()
								configdata.append(configInBin)
						for configOutFile in configOutFileList:
							if configOutFile != [""]:
								configcolumns.append("Chip{}OutConfig".format(configOutFile.split('_')[-2]))
								configOutBuffer = open(configOutFile,'rb')
								configOutBin = configOutBuffer.read()
								configdata.append(configOutBin)
						
						xmlcolumns = []
						xmldata = []
						if len(XMLFileList) > 1:
							print ("Warning!  There are multiple xml files here!")
						for XMLFile in XMLFileList:
							if XMLFile != [""]:
								xmlcolumns.append("xml_file")
								xmlBuffer = open(XMLFile, 'rb')
								xmlBin = xmlBuffer.read()
								xmldata.append(xmlBin)

						#Columns = ["part_id","date","testname","description","grade","data_id","username", "config_file", "xml_file"]
						#Columns = ["part_id","test_id","test_name","date","test_grade","user","Chip0InConfig","Chip0OutConfig","Chip1InConfig","Chip1OutConfig","Chip2InConfig","Chip2OutConfig","Chip3InConfig","Chip3OutConfig","plot1","plot2"]
						Columns = ["part_id","test_id","test_name","date","test_grade","user","plot1","plot2","root_file"]
						SubmitArgs = []
						Value = []
						record = formatter(localDir,Columns, part_id=module)
						#record = formatter(localDir,Columns, part_id=str(module_id))
						#for column in ['part_id']:
						for column in Columns:
							if column == "part_id":
								SubmitArgs.append(column) 
								Value.append(module) 
							if column == "date":
								SubmitArgs.append(column)
								if str(sys.version).split(" ")[0].startswith(("3.7","3.8","3.9")):
									TimeStamp = datetime.fromisoformat(localDir.split('_')[-2])
								elif str(sys.version).split(" ")[0].startswith(("3.6")):
									TimeStamp = datetime.strptime(localDir.split('_')[-2].split('.')[0], '%Y-%m-%dT%H:%M:%S')
								#print ("timestamp is {0}".format(TimeStamp))
								Value.append(TimeStamp)
								#Value.append(record[Columns.index(column)])
							if column == "test_name":
								SubmitArgs.append(column)
								Value.append(record[Columns.index(column)])
							if column == "description":
								SubmitArgs.append(column)
								Value.append("No Comment")
							if column == "test_grade":
								SubmitArgs.append(column)
								Value.append(-1)
							if column == "test_id":
								SubmitArgs.append(column)
								Value.append(data_id)
							if column == "user":
								SubmitArgs.append(column)
								Value.append(self.master.TryUsername)
							if column == "root_file":
								SubmitArgs.append(column)
								Value.append(submitFile.split("/")[-1])

						SubmitArgs = SubmitArgs + configcolumns + xmlcolumns
						Value = Value + configdata + xmldata
			
						try:
							insertGenericTable(self.connection, "module_tests", SubmitArgs, Value)
						except:
							print("Failed to insert")
			except Exception as err:
				QMessageBox.information(self,"Error","Unable to save to DB", QMessageBox.Ok)
				print("Error: {}".format(repr(err)))
				return

	def checkRemoteFile(self, file_id):
		remoteRecords = retrieveWithConstraint(self.connection,"result_files",file_id = file_id, columns = ["file_id"])
		return remoteRecords != []

	def uploadFile(self, fileName, file_id):
		fileBuffer = open(fileName, 'rb')
		data = fileBuffer.read()
		insertGenericTable(self.connection, "result_files", ["file_id","file_content"],[file_id,data])
	#######################################################################
	##  For real-time terminal display
	#######################################################################

	@QtCore.pyqtSlot()
	def on_readyReadStandardOutput(self):
		if self.readingOutput == True:
			print("Thread competition detected")
			return
		self.readingOutput = True
		
		alltext = self.run_process.readAllStandardOutput().data().decode()
		self.outputfile.write(alltext)
		#outputfile.close()
		textline = alltext.split('\n')
		#fileLines = open(self.outputFile,"r")
		#textline = fileLines.readlines()

		for textStr in textline:
			try: 
				if self.starttime != None:
					self.currentTime = time.time()
					runningTime = self.currentTime - self.starttime
				else:
					self.starttime = time.time()
					self.currentTime = self.starttime
				
				self.ResultWidget.runtime[self.testIndexTracker].setText('{0} s'.format(round(runningTime,1)))
			except Exception as err:
				logger.info("Error occures while parsing running time, {0}".format(err))

			if self.ProgressingMode == "Perform":			
				if ">>>> Progress :" in textStr:
					try:
						index = textStr.split().index("Progress")+2
						self.ProgressValue = float(textStr.split()[index].rstrip("%"))
						if self.ProgressValue == 100:
							self.ProgressingMode = "Summary"
						self.ResultWidget.ProgressBar[self.testIndexTracker].setValue(self.ProgressValue)										
					except:
						pass
					
				continue
			#	if ("Global threshold for" in textStr):

			elif (self.ProgressingMode == "Summary"):
				toUpdate, UpdatedFEKey, valueIndex = self.updateNeeded(textStr)
				if toUpdate:
					try:
						#print("made it to Summary")
						UpdatedValuetext = textStr.split()[valueIndex]
						#print(re.sub(r'\033\[(\d|;)+?m','',globalThresholdtext))
						UpdatedValue = int(re.sub(r'\033\[(\d|;)+?m','',UpdatedValuetext))
						print("New {0} value is {1}".format(UpdatedFEKey,UpdatedValue))
						print(textStr.split())
						#globalThreshold = int(textStr.split()[-1])
						chipIdentifier = textStr.split('=')[-1].split('is')[0]
						chipIdentifier = re.sub(r'\033\[(\d|;)+?m','',chipIdentifier).split(']')[0]
						HybridIDKey = chipIdentifier.split("/")[2]
						ChipIDKey = chipIdentifier.split("/")[3]
						print("hybrid id {0}".format(HybridIDKey))
						print("chipID {0}".format(ChipIDKey))
						updatedXMLValueKey = "{}/{}".format(HybridIDKey,ChipIDKey)
						updatedXMLValues[updatedXMLValueKey][UpdatedFEKey] = UpdatedValue
						
					except Exception as err:
						logger.error("Failed to update ")
										
			elif "@@@ Initializing the Hardware @@@" in textStr:
				self.ProgressingMode = "Configure"
			elif "@@@ Performing" in textStr:
				self.ProgressingMode = "Perform"
				self.ConsoleView.appendHtml('<b><span style="color:#ff0000;"> Performing the {} test </span></b>'.format(self.currentTest))

			text = textStr.encode('ascii')
			numUpAnchor, text = parseANSI(text)
			#if numUpAnchor > 0:
			#	textCursor = self.ConsoleView.textCursor()
			#	textCursor.beginEditBlock()
			#	textCursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
			#	textCursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
			#	for numUp in range(numUpAnchor):
			#		textCursor.movePosition(QTextCursor.Up, QTextCursor.KeepAnchor)
			#	textCursor.removeSelectedText()
			#	textCursor.deletePreviousChar()
			#	textCursor.endEditBlock()
			#	self.ConsoleView.setTextCursor(textCursor)
			textCursor = self.ConsoleView.textCursor()
			self.ConsoleView.setTextCursor(textCursor)
			self.ConsoleView.appendHtml(text.decode("utf-8"))
		self.readingOutput = False

	def updateNeeded(self,textStr):
		currentTest = Test[self.currentTest]
		if  currentTest in ["thradj","thrmin"] and "Global threshold for" in textStr:
			return True,"Vthreshold_LIN",-1
		elif currentTest in ["gainopt"] and "Krummenacher Current" in textStr:
			return True,"KRUM_CURR_LIN",-1
		elif currentTest in ["injdelay"]:
			if "New latency dac" in textStr:
				return True,"LATENCY_CONFIG",-2
			elif "New injection delay" in textStr:
				return True,"INJECTION_SELECT",-2
			else:
				return (False, None, 0)
		else:
			return (False, None, 0)
		
	@QtCore.pyqtSlot()
	def on_readyReadStandardOutput_info(self):
		if os.path.exists(self.outputFile):
			outputfile = open(self.outputFile,"a")
		else:
			outputfile = open(self.outputFile,"w")
		
		alltext = self.info_process.readAllStandardOutput().data().decode()
		outputfile.write(alltext)
		outputfile.close()
		textline = alltext.split('\n')

		for textStr in textline:
			self.ConsoleView.appendHtml(textStr)
		
	@QtCore.pyqtSlot()
	def on_finish(self):
		self.RunButton.setDisabled(True)
		self.RunButton.setText("&Continue")
		self.finishSingal = True
		self.outputfile.close()

		#To be removed
		#if isCompositeTest(self.info[1]):
		#	self.ListWidget.insertItem(self.listWidgetIndex, "{}_Module_0_Chip_0".format(CompositeList[self.info[1]][self.testIndexTracker-1]))
		#if isSingleTest(self.info[1]):
		#	self.ListWidget.insertItem(self.listWidgetIndex, "{}_Module_0_Chip_0".format(self.info[1]))

		self.testIndexTracker += 1
		self.saveConfigs()

		if isCompositeTest(self.info[1]):
			if self.testIndexTracker == len(CompositeList[self.info[1]]):
				self.RunButton.setText("&Re-run")
				self.RunButton.setDisabled(False)
		if isSingleTest(self.info[1]):
			#self.RunButton.setText("&Finish")
			#self.RunButton.setDisabled(True)
			self.RunButton.setText("&Re-run")
			self.RunButton.setDisabled(False)

		# Save the output ROOT file to output_dir
		self.saveTest()

		# validate the results
		status = self.validateTest()

		# show the score of test
		self.refreshHistory()

		# For test
		# self.ResultWidget.updateResult("/Users/czkaiweb/Research/data")
		self.ResultWidget.updateResult(self.output_dir)

		if self.autoSave:
			self.saveTestToDB()
		self.update()

		if status == False and isCompositeTest(self.info[1]) and self.testIndexTracker < len(CompositeList[self.info[1]]):
			self.forceContinue()

		if isCompositeTest(self.info[1]):
			self.runTest()
