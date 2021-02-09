from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateTimeEdit,
		QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, 
		QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
		QSlider, QSpinBox, QStyleFactory, QTableView, QTableWidget, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QWidget, QMainWindow)

import sys
import os
import subprocess
import logging

from functools import partial
from Gui.GUIutils.settings import *
from Gui.GUIutils.guiUtils import *
from Gui.python.ROOTInterface import *
from Gui.QtGUIutils.QtTCanvasWidget import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResultTreeWidget(QWidget):
	def __init__(self,info,width,height,master):
		super(ResultTreeWidget,self).__init__()
		self.master = master
		self.DisplayW = width
		self.DisplayH = height
		self.FileList = []
		self.info = info
		self.ProgressBarList = []
		self.ProgressBar = {}
		self.displayingImage = ""
		self.Plot = []
		self.count = 0

		self.mainLayout = QGridLayout()
		self.setLayout(self.mainLayout)
		self.initializeProgressBar()
		self.setupUi()

		# For test:
		# self.updateResult("/Users/czkaiweb/Research/data")
		
	def initializeProgressBar(self):
		if isCompositeTest(self.info[1]):
			self.ProgressBarList = CompositeList[self.info[1]]
		else:
			self.ProgressBarList= [self.info[1]]

		for index, obj in enumerate(self.ProgressBarList):
			ProgressBar = QProgressBar()
			ProgressBar.setMinimum(0)
			ProgressBar.setMaximum(100)
			self.ProgressBar[index] = ProgressBar

	def setupUi(self):
		#self.DisplayTitle = QLabel('<font size="6"> Result: </font>')
		#self.DisplayLabel = QLabel()
		#self.DisplayLabel.setScaledContents(True)
		#self.displayingImage = 'test_plots/test_best1.png'
		#self.DisplayView = QPixmap('test_plots/test_best1.png').scaled(QSize(self.DisplayW,self.DisplayH), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		#self.DisplayLabel.setPixmap(self.DisplayView)
		#self.ReferTitle = QLabel('<font size="6"> Reference: </font>')
		#self.ReferLabel = QLabel()
		#self.ReferLabel.setScaledContents(True)
		#self.ReferView = QPixmap('test_plots/test_best1.png').scaled(QSize(self.DisplayW,self.DisplayH), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		#self.ReferLabel.setPixmap(self.ReferView)

		self.ProgressWidget = QWidget()
		self.ProgressLayout = QGridLayout()

		for index, key in enumerate(self.ProgressBar.keys()):
			testLabel = QLabel('<b>{}</b>'.format(self.ProgressBarList[index]))
			testProgress = self.ProgressBar[key]

			self.ProgressLayout.addWidget(testLabel,index,0,1,1,Qt.AlignTop)
			self.ProgressLayout.addWidget(testProgress,index,1,1,4,Qt.AlignTop)

		self.ProgressWidget.setLayout(self.ProgressLayout)

		self.OutputTree = QTreeWidget()
		self.OutputTree.horizontalScrollBar().setEnabled(True)
		self.OutputTree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.OutputTree.setHeaderLabels(['Name'])
		self.OutputTree.itemClicked.connect(self.onItemClicked)
		self.TreeRoot = QTreeWidgetItem(self.OutputTree)
		self.TreeRoot.setText(0,"Files..")


		## Old display: To be removed
		#self.mainLayout.addWidget(self.DisplayTitle,0,0,1,2)
		#self.mainLayout.addWidget(self.DisplayLabel,1,0,1,2)
		#self.mainLayout.addWidget(self.ReferTitle,0,2,1,2)
		#self.mainLayout.addWidget(self.ReferLabel,1,2,1,2)
		#self.mainLayout.addWidget(self.OutputTree,0,4,2,1)

		self.mainLayout.addWidget(self.ProgressWidget,0,0,1,2)
		self.mainLayout.addWidget(self.OutputTree,0,2,1,2)

	## Old methods: To be removed
	def resizeImage(self, width, height):
		pass
		#self.DisplayView = QPixmap(self.displayingImage).scaled(QSize(width,height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		#self.DisplayLabel.setPixmap(self.DisplayView)
		#self.update

	@QtCore.pyqtSlot(QTreeWidgetItem, int)
	def onItemClicked(self, item, col):
		self.OutputTree.resizeColumnToContents(0)
		if item.text(0).endswith(";TCanvas"):
			canvas = item.data(0,Qt.UserRole)
			self.displayResult(canvas)

	def DirectoryVAL(self, QTreeNode, node):
		if node.getDaugthers() != []:
			for Node in node.getDaugthers():
				CurrentNode = QTreeWidgetItem()
				if Node.getClassName() ==  "TCanvas":
					CurrentNode.setText(0,Node.getKeyName()+";TCanvas")
					CurrentNode.setData(0,Qt.UserRole,Node.getObject())
				else:
					CurrentNode.setText(0,Node.getKeyName())
				QTreeNode.addChild(CurrentNode)
				self.DirectoryVAL(CurrentNode,Node)
		else:
			return 

	def getResult(self, QTreeNode, sourceFile):
		Nodes = GetDirectory(sourceFile)
		CurrentNode = QTreeWidgetItem()
		for Node in Nodes:
			CurrentNode = QTreeWidgetItem()
			CurrentNode.setText(0,Node.getKeyName())
			QTreeNode.addChild(CurrentNode)
			self.DirectoryVAL(CurrentNode, Node)

	def updateResult(self, sourceFolder):
		process = subprocess.run('find {0} -type f -name "*.root" '.format(sourceFolder), shell=True, stdout=subprocess.PIPE)
		stepFiles = process.stdout.decode('utf-8').rstrip("\n").split("\n")
		if stepFiles == [""]:
			return
		self.FileList += stepFiles

		for File in stepFiles:
			CurrentNode = QTreeWidgetItem()
			CurrentNode.setText(0,File.split("/")[-1])
			CurrentNode.setData(0,Qt.UserRole,File)
			self.TreeRoot.addChild(CurrentNode)
			self.getResult(CurrentNode, File)
			
	def displayResult(self, canvas):
		tmpDir = os.environ.get('GUI_dir')+"/Gui/.tmp"
		if not os.path.isdir(tmpDir)  and os.environ.get('GUI_dir'):
			try:
				os.mkdir(tmpDir)
				logger.info("Creating "+tmpDir)
			except:
				logger.warning("Failed to create "+tmpDir)
		jpgFile = TCanvas2JPG(tmpDir, canvas)
		self.displayingImage = jpgFile

		try:
			#self.DisplayView = QPixmap(jpgFile).scaled(QSize(self.DisplayW,self.DisplayH), Qt.KeepAspectRatio, Qt.SmoothTransformation)
			#self.DisplayLabel.setPixmap(self.DisplayView)
			#self.update
			self.Plot.append("index")
			self.Plot[self.count] = QtTCanvasWidget(self.master,jpgFile)
			self.count = self.count+1
			logger.info("Displaying " + jpgFile)
		except:
			logger.error("Failed to display " + jpgFile)
		pass


