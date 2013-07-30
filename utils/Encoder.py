#!/usr/bin/python2.6
'''
Created on 1 July 2010
@author: salome, minh hoang le
'''

class Encoder(): #Encode orders into hexa frames for X10
    def __init__(self,target,parameter):
        self.target=target
        self.house=target[0]
        self.unit=target[1:len(target)]
        self.parameter=parameter 
        self.houseCodeDict={'A':0x60,'B':0x70,'C':0x40,'D':0x50,'E':0x80,'F':0x90,'G':0xA0,'H':0xB0,'I':0xE0,'J':0xF0,'K':0xC0,'L':0xD0,'M':0x00,'N':0x10,'O':0x20,'P':0x30}
        self.unitCodeDict={'1':0x00,'2':0x10,'3':0x08,'4':0x18,'5':0x40,'6':0x50,'7':0x48,'8':0x58}
        
    def encode(self):
        houseCode=self.houseCodeDict[self.house]
        print('Unit : ',self.unit,type(self.unit))
        print(int(self.unit)>8)
        if int(self.unit)>8:
            deviceCode=self.unitCodeDict[str(int(self.unit)-8)]
            houseCode=(0x04+houseCode)
        else:
            deviceCode=self.unitCodeDict[self.unit]
        FFHC=hex(0xFF-houseCode)[2:]
        if len(FFHC)==1:
            FFHC='0'+FFHC
        FFDC=hex(0xFF-deviceCode)[2:]
        if len(FFDC)==1:
            FFDC='0'+FFDC
        offCode=deviceCode+0x20
        deviceCode=hex(deviceCode)[2:]
        houseCode=hex(houseCode)[2:]
        if len(houseCode)==1:
            houseCode='0'+houseCode
        FFOC=hex(0xFF-offCode)[2:]
        offCode=hex(offCode)[2:]
        if len(offCode)==1:
            offCode='0'+offCode
        if len(FFOC)==1:
            FFOC='0'+FFOC
        if len(deviceCode)==1:
            deviceCode='0'+deviceCode
        
        FFMC1=hex(0xFF-0x98)[2:]
        if len(FFMC1)==1:
            FFMC1='0'+FFMC1
        
        FFMC2=hex(0xFF-0x88)[2:]
        if len(FFMC2)==1:
            FFMC2='0'+FFMC2
        
        if self.parameter=='on':
            frame='20 %s %s %s %s'%(houseCode,FFHC,deviceCode,FFDC)
        elif self.parameter=='off':
            frame='20 %s %s %s %s'%(houseCode,FFHC,offCode,FFOC)
        #parameter = DIM
        elif self.parameter=='dim':
            frame='20 %s %s %s %s'%(houseCode,FFHC,98,FFMC1)
        #parameter = BRIGHT
        elif self.parameter=='bright':
            frame='20 %s %s %s %s'%(houseCode,FFHC,88,FFMC2)
        return frame
    
    def HexToBin(self,chaine):
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
        chaine=chaine.replace('a','1010')
        chaine=chaine.replace('B','1011')
        chaine=chaine.replace('b','1011')
        chaine=chaine.replace('C','1100')
        chaine=chaine.replace('c','1100')
        chaine=chaine.replace('D','1101')
        chaine=chaine.replace('d','1101')
        chaine=chaine.replace('E','1110')
        chaine=chaine.replace('e','1110')
        chaine=chaine.replace('F','1111')
        chaine=chaine.replace('f','1111')
        return chaine
