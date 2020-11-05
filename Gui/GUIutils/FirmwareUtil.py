'''
  FirmwareUtil.py
  brief                 utility functions for firmware 
  author                Kai Wei
  version               0.1
  date                  03/11/20
  Support:              email to wei.856@osu.edu
'''
import subprocess
from  subprocess import Popen,PIPE
from  datetime import datetime

def firmwarePingCheck(fAddress,fileName):
	outputFile = open(fileName,'a+')
	subprocess.run(["echo","\n[{0}]\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))], stdout=outputFile, stderr=outputFile)
	returnCode = subprocess.run(["ping","-c","1","-W","1",fAddress], stdout=outputFile, stderr=outputFile).returncode
	return returnCode

#Fixme
def fpgaConfigCheck(firmwareName,fileName):
	returnCode = 0
	return returnCode

def fwStatusParser(firmwareName, fAddress,fileName):
	pingReturnCode = firmwarePingCheck(fAddress,fileName)
	if pingReturnCode == 2:
		return "Ping failed","color:red"

	fpgaReturnCode = fpgaConfigCheck(firmwareName,fileName)
	if fpgaReturnCode == 1:
		return "FPGA configuration failed", "color:red"
	
	return "Connected","color: green"



FwStatusCheck = {
	""				  :       '''Please run frimware check  first ''',
	"Ping failed"     :       '''Please check: 
								 1. FC7 board is connected
								 2. FC7 is connected to PC via Ethernet cable
								 3. The assigned IP address is correct
								 4. rarpd service is running
									''',
	"Connected"		  : 	  '''Good'''
}

FEPowerUpVD = {
	"SLDO"			  :  [1.75, 1.82],
	"Direct"		  :  [1.15, 1.25]
}

FEPowerUpVA = {
	"SLDO"			  :  [1.75, 1.82],
	"Direct"		  :  [1.15, 1.25]	
}

FEPowerUpAmp = {
	"SLDO"			  :  [0.5, 1.3],
	"Direct"		  :  [0.5, 1.3]	
}

	