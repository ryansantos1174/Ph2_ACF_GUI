import re

def ArduinoParser(text):
    try:
        StopSingal, ProbeReadsText = ArduinoParserCustomOSU(text)
        return StopSingal, ProbeReadsText
    except Exception as err:
        return False,""


#################Arduino formatting for OSU###############
ProbeMapOSU = {
    'DHT11': "Humidity",
    'MAX31850': "Temperature(single wire)",
    'MAX31865': "Temperature(triple wire)",
    # TODO Add probes that I will need here
}
ThresholdMapOSU = {
    'DHT11': [0,60],
    'MAX31850': [-20,50],
    'MAX31865': [-20,23],
}
def ArduinoParserCustomOSU(text):
    StopSignal = False
    values = re.split(" |\t",text)[1:] # Split at a space or a tab 
    readValue = {}
    ProbeReads = []

    for index,value in enumerate(values):
        value = value.rstrip(":") # Removes the ending colon
        if value in ProbeMapOSU.keys() and 'Temperature' not in values[index-1]:
            readValue[value] = float(values[index+1])

    for probeName,probeValue in readValue.items():
        if probeName in ThresholdMapOSU.keys():
            # Make sure you didnt mess up when setting up the threshold
            if type(ThresholdMapOSU[probeName])!= list or len(ThresholdMapOSU[probeName]) !=2:
                continue
            else:
                if probeValue < ThresholdMapOSU[probeName][0] or  probeValue > ThresholdMapOSU[probeName][1]:
                    colorCode = "#FF0000"
                    if probeName in ['MAX31850','MAX31865']:
                        StopSignal = True
                        
                else:
                    colorCode = "#008000"
                ProbeReads.append('{0}:<span style="color:{1}";>{2}</span>'.format(ProbeMapOSU[probeName],colorCode,probeValue))
                
        else:
            # If there is not a threshold then just read the value
            ProbeReads.append('{0}:{1}'.format(ProbeMapOSU[probeName],probeValue))
    ProbeReadsText = '\t'.join(ProbeReads)
    return StopSignal,ProbeReadsText

    