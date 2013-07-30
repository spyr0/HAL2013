#!/usr/bin/python2.6
'''
Created on 2 july 2010
@author: salome, minh hoang le
'''

from datetime import date
import datetime
import time

class DecoderZig: #Decode Zigbee frames
    def __init__(self,frame):
        self.internalFrame=frame
        self.internalFrame=self.internalFrame.replace(" ","")
        self.dictionnary=dict()
        
    def hexToBin(self,chaine):
        chaine=chaine.replace('0','0000')
        chaine=chaine.replace('1','0001')
        chaine=chaine.replace('2','0010')
        chaine=chaine.replace('3','0011')
        chaine=chaine.replace('4','0100')
        chaine=chaine.replace('5','0101')
        chaine=chaine.replace('6','0110')
        chaine=chaine.replace('7','0111')
        chaine=chaine.replace('8','1000')
        chaine=chaine.replace('9','1001')
        chaine=chaine.replace('A','1010')
        chaine=chaine.replace('B','1011')
        chaine=chaine.replace('C','1100')
        chaine=chaine.replace('D','1101')
        chaine=chaine.replace('E','1110')
        chaine=chaine.replace('F','1111')
        return chaine
    def binToDec(self,chaine):
        i=0
        num=0
        while (i<len(chaine)):
            num = num + int(chaine[i])*2**((len(chaine)-1)-i)
            i+=1
        return num
    def decode(self):
        try:
            if(self.representsInt(self.internalFrame[2:10])):
                self.dictionnary['address']=int(self.internalFrame[2:10])
                self.internalFrame=self.hexToBin(self.internalFrame)
                self.dictionnary['voltage']=self.binToDec(self.internalFrame[64:72]+self.internalFrame[56:64])/100
                self.dictionnary['current']=self.binToDec(self.internalFrame[80:88]+self.internalFrame[72:80])
                self.dictionnary['activeEnergy']=self.binToDec(self.internalFrame[112:120]+self.internalFrame[104:112]+self.internalFrame[96:104]+self.internalFrame[88:96])/10
                self.dictionnary['apparentEnergy']=self.binToDec(self.internalFrame[144:152]+self.internalFrame[136:144]+self.internalFrame[128:136]+self.internalFrame[120:128])/10
                self.dictionnary['RSSI']=(self.binToDec(self.internalFrame[152:160])*100)/255
                self.dictionnary['activePower']=self.binToDec(self.internalFrame[176:184]+self.internalFrame[168:176])/10
                self.dictionnary['apparentPower']=self.binToDec(self.internalFrame[192:200]+self.internalFrame[184:192])/10
                return self.dictionnary
            else:
                #write to file
                day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
                hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
                zigbeefile = open('errorFrameZigbee.txt',"a",encoding='utf-8')
                zigbeefile.write(hour+','+day+': error frame :'+self.internalFrame+"\n")
                zigbeefile.close()
                print ("Sorry, it is not a good frame zigbee")
                return self.Unknown(self.internalFrame)
        except:
            #write to file
            day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
            hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
            zigbeefile = open('bugZigbee.txt',"a",encoding='utf-8')
            zigbeefile.write(hour+','+day+': there is a problem with Zigbee : '+'error frame :'+self.internalFrame[2:10]+"\n")
            zigbeefile.close()
            
            
            
    def representsInt(self,s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
        
    def Unknown(self,frame): #Unknown frame
        dic={"address":"unknown","frame":"", "date":""}
        dic["frame"] = frame
        date = time.localtime()
        date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
        dic["date"]=date
        return dic
