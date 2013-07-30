'''
A class to receive and possible decode rough data from sensors,...
Created on 1 aout 2011
@author: stephane
'''
__all__ = ["Driver","MockDriver","ZigbeeDriver","RfxcomDriver","Daq8iDriver"]
import json
#import codecs
import threading, random
import resources.datasource
from utils import Encoder,DecoderRFX,DecoderZig,TrameDividing
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import date
import datetime, time
import configparser

class Driver(threading.Thread):
    '''
    Use to collect actual data and to send them to a datasource
    but also to send data to an actual resource via a controller
    '''
    def __init__(self,periodInSecs=10):
        threading.Thread.__init__(self)
        self.running=True
        self.periodInSecs=periodInSecs
        self.registeredDatasources=dict()
        self.configuration = configparser.ConfigParser()
        self.configuration.read('hal.cfg')

    def stop(self):
        self.running=False

    def getPeriodInSecs(self):
        return self.periodInSecs

    def registerDatasource(self,identifiers_list,datasource):
        self.registeredDatasources[identifiers_list]=datasource
        
    def getRegisteredDatasource(self,identifiers_list):
        return self.registeredDatasources[identifiers_list]

    def setControl(self,controlledAppliance,jsonControlParameters):
        print("-> control applied to "+controlledAppliance+": "+jsonControlParameters)

class MockDriver(Driver):
    '''
    Use to collect actual data and to send them to a datasource
    but also to send data to an actual resource via a controller
    '''
    def __init__(self,periodInSecs,possibleValues=range(100)):
        Driver.__init__(self,periodInSecs)
        self.possibleValues=possibleValues

    def run(self):
        while self.running:
            for identifiers_list in self.registeredDatasources:
                self.registeredDatasources[identifiers_list].setValue('mock',self.possibleValues[random.randint(0,len(self.possibleValues))-1])
            time.sleep(self.getPeriodInSecs())

class ZigbeeDriver(Driver):
    '''
    Use to collect actual data and to send them to a datasource
    but also to send data to an actual resource via a controller
    '''
    def __init__(self,periodInSecs):
        Driver.__init__(self,periodInSecs)

    def run(self):
        serial = __import__("serial",globals(),locals(),fromlist=['*'])
        self.serialPort=serial.Serial()
        self.serialPort.port = int(self.configuration['ZIGBEE']['PORT'])
        self.serialPort.baudrate=int(self.configuration['ZIGBEE']['BAUDRATE'])
        self.serialPort.timeout=int(self.configuration['ZIGBEE']['TIMEOUT_IN_SECS'])
        self.serialPort.open()

        while True:
            wattMeterNumber=0
            while wattMeterNumber<15: #and j!=4:
                wattMeterNumber+=1
                try:
                    self.serialPort.write(("+++").encode('latin1'))
                    s=self.serialPort.read(3)
                    temp="ATDL %s\r\n"%(str(wattMeterNumber+9129))
                    self.serialPort.write(temp.encode('latin1'))
                    s=self.serialPort.read(3)
                    self.serialPort.write(("ATCN\r\n").encode('latin1'))
                    s=self.serialPort.read(3)
                    self.serialPort.write((" ").encode('latin1'))
                    s=self.serialPort.read(28)
                    hexData=' '.join(["%02X"%x for x in s])
                except:
                    #write to file
                    day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
                    hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
                    zigbeefile = open('bugZigbee.log',"a",encoding='utf-8')
                    zigbeefile.write(hour+','+day+': there is a problem with Zigbee Driver'+'----'+'appliance in process: '+str(wattMeterNumber)+"\n")
                    zigbeefile.close()
                    self.serialPort.close()
                    #reset the connexion
                    while not self.serialPort.isOpen():
                        self.serialPort=serial.Serial()
                        self.serialPort.port=self.configuration['ZIGBEE']['PORT']
                        self.serialPort.baudrate=self.configuration['ZIGBEE']['BAUDRATE']
                        self.serialPort.timeout=self.configuration['ZIGBEE']['TIMEOUT_IN_SECS']
                        self.serialPort.open()
                        time.sleep(5)
                        if self.serialPort.isOpen():
                            day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
                            hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
                            zigbeefile = open('bugZigbee.log',"a",encoding='utf-8')
                            zigbeefile.write(hour+','+day+": Zigbee Driver has been reset\n")
                            zigbeefile.close()
                else:
                    if hexData=='':
                        continue
                    if hexData[81:83]!='C1':
                        end=''
                        k=28
                        while end!='C1' and k<47:
                            end=self.serialPort.read(1)
                            k+=1
                            end=' '.join(["%02X"%x for x in end])
                            #print ('end of frame :',end)
                            hexData+=' '+end
                            #print ('with add :',hexData)
                        for i in range(len(hexData)):
                            if hexData[i:i+2]=='7D':
                                temp=hexData[i+3:i+5]
                                if temp=='5D':
                                    hexData=hexData[0:i]+'7D'+hexData[i+5:len(hexData)]
                                elif temp=='E0':
                                    hexData=hexData[0:i]+'C0'+hexData[i+5:len(hexData)]
                                elif temp=='E1':
                                    hexData=hexData[0:i]+'C1'+hexData[i+5:len(hexData)]
                                    
                    decoder= DecoderZig.DecoderZig(hexData)
                    decodedZigbeeFrame=decoder.decode()
                    if decodedZigbeeFrame['address'] is not 'unknown':
                        print('++++++++++wattMeter'+str(wattMeterNumber)+'++++++++++: '+str(decodedZigbeeFrame["activePower"]))
                        self.getRegisteredDatasource(('ZIGBEE',str(wattMeterNumber))).setValue(self.name,decodedZigbeeFrame["activePower"])
                        time.sleep(float(self.configuration['ZIGBEE']['SEND_REQUEST_FREQUENCY_IN_SECS']))
                    else:
                        print("Unknown Frame :\n",decodedZigbeeFrame["frame"])
                    

class RfxcomDriver(Driver):
    '''
    Use to collect actual data and to send them to a datasource
    but also to send data to an actual resource via a controller
    datasource are registered with identifiers_list=('OS','canal','humidity'),('OS','canal','temperature')
    '''
    def __init__(self,periodInSecs):
        Driver.__init__(self,periodInSecs)

    def run(self):
        self.localSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.localSocket.setblocking(1)
        self.RFXCOM_IP_ADDRESS = self.configuration['RFXCOM']['RFXCOM_IP_ADDRESS']
        self.RFXCOM_OUT_PORT = int(self.configuration['RFXCOM']['RFXCOM_OUT_PORT'])
        self.localSocket.connect((self.RFXCOM_IP_ADDRESS,self.RFXCOM_OUT_PORT))
        print('RFXCOM is connected at '+self.RFXCOM_IP_ADDRESS+':'+str(self.RFXCOM_OUT_PORT))
        while True:
            try:
                data=self.localSocket.recv(1024)
                hexData=' '.join(["%02X"%x for x in data])
                if len(hexData)!= 14 and len(hexData)!= 20 and len(hexData)!= 32 and len(hexData)!= 35:
                    complexRfxcomFrame=TrameDividing.TrameDividing(hexData)
                    rfxcomFrameList=complexRfxcomFrame.dividing()
                else:
                    rfxcomFrameList=[hexData]
                for rfxcomFrame in rfxcomFrameList:
                    decodedRfxcomFrame=DecoderRFX.DecoderRfx(rfxcomFrame).decoderRfx()
                    if decodedRfxcomFrame!=0:
                        if decodedRfxcomFrame["protocole"]!=0:
                            if decodedRfxcomFrame["protocole"]=='osTemp':
                                self.getRegisteredDatasource(('OS',str(decodedRfxcomFrame['canal']),'humidity')).setValue('rfxcom',str(decodedRfxcomFrame['humidite']))
                                self.getRegisteredDatasource(('OS',str(decodedRfxcomFrame['canal']),'temperature')).setValue('rfxcom',str(decodedRfxcomFrame['temperature']))
                            elif decodedRfxcomFrame['protocole'] =='X10':
                                print("X10 Frame :\n", decodedRfxcomFrame)
                                self.getRegisterDatasource(('X10',str(decodedRfxcomFrame['maison']),str(decodedRfxcomFrame['adresse']))).setValue('rfxcom',str(decodedRfxcomFrame['ordre']))
                            elif decodedRfxcomFrame["protocole"] == 'presence':
                                print("presence Frame :\n", decodedRfxcomFrame)
                                self.getRegisterDatasource(('X10','presence')).setValue('rfxcom',decodedRfxcomFrame['presence'])
                            elif decodedRfxcomFrame["protocole"]=='unknown':
                                print("Unknown Frame :\n",decodedRfxcomFrame)
                            else : 
                                print('It is not a known frame')
            except:
                day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
                hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
                rfxLogFile = open('bugRFXDriver.log','a',encoding='utf-8')
                rfxLogFile.write(hour+','+day+': connection to RFXCOM has been reset'+"\n")
                rfxLogFile.close()
                print("connection to RFXCOM is reset")
                self.localSocket.close()
                self.localSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.localSocket.setblocking(1)
                self.localSocket.connect((self.RFXCOM_IP_ADDRESS,self.RFXCOM_OUT_PORT))

    def setControl(self,controlledAppliance,jsonControlParameters):
        print("-> control applied to "+controlledAppliance+": "+jsonControlParameters)
        self.encoder=Encoder.Encoder(str(controlledAppliance),json.loads(jsonControlParameters)["switch"])
        frame=self.encoder.encode()
        frames=['F0 37 F0 37',frame]
        print(frames)
        print('responses:')
        try:
            response=''
            for frame in frames:
                print(frame)
                byte=[]
                frame = ''.join(frame.split(" ")) #decode hex to binary
                frame_length=len(frame)
                for i in range(0,frame_length,2):
                    byte.append(chr(int(frame[i:i+2],16)))
                bytesequence=''.join(byte)
                print(bytesequence, type(bytesequence))
                rfxcomSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                rfxcomSocket.setblocking(1)
                rfxcomSocket.connect((self.RFXCOM_IP_ADDRESS,self.RFXCOM_IN_PORT))
                rfxcomSocket.send(bytesequence.encode('latin1','ignore'))
                response+=' '.join(["%02X "%x for x in rfxcomSocket.recv(1024)])
                print(response)
                rfxcomSocket.close()
        except:
            day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
            hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
            rfxLogFile = open('bugRFXDriver.log','a',encoding='utf-8')
            rfxLogFile.write(hour+','+day+': controller RFX is error'+'\n')
            rfxLogFile.close()    
            rfxcomSocket.close()
            print('Error : bad control')

class Daq8iDriver(HTTPServer,Driver):
    def __init__(self,periodInSecs):
        Driver.__init__(self,periodInSecs)
        SERVER_IP_INTERFACE = self.configuration['MAIN']['SERVER_IP_INTERFACE']
        LOCAL_OPEN_PORT = int(self.configuration['DAQ8i']['LOCAL_OPEN_PORT'])
        print("Server for DAQ8i is connected at http://%s:%i/..."%(SERVER_IP_INTERFACE,int(LOCAL_OPEN_PORT)))
        HTTPServer.__init__(self, (SERVER_IP_INTERFACE, int(LOCAL_OPEN_PORT)), Daq8iRequestHandler)
    def run(self):
        self.serve_forever()

class Daq8iRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        words=urlparse(self.path)
        word = words[4]
        n=len(word)
        index=0
        while (index<n):
            if word[index]== '&':
                break
            else:
                index+=1
        word=word[4:index]
        CO2Value=float(word)*400
        print('++++++++emission CO2 ++++++++:  ' +str(CO2Value))
        self.server.getRegisteredDatasource(('DAQ8i')).setValue('DAQ8i',CO2Value)

if __name__ == '__main__':
    datasource=resources.datasource.Datasource('example')
    driver=MockDriver(10,('on','off','middle'))
    driver.start()
    time.sleep(10)
    driver.setControl("oven", "{'switch':'on','temperature':'180'}")
    driver.stop()