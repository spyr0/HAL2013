#!/usr/bin/python2.6
'''
Created on 25 may 2010
@author: salome
'''

from datetime import date
import datetime
import time

class DecoderRfx(): #Decode frames from RFXCOM
    def __init__(self,frame):
        self.internalFrame=frame
        self.tramDictionnary = {"50":32, "30":20, "20":14, "44":29}
        
    def decoderRfx(self):
        self.temp=dict()
        if(self.checkCompletFrame(self.internalFrame)):
            frame=self.internalFrame.replace(" ","") 
            if frame[0:2]=='50' or frame[0:2]=='58':
                self.temp=self.DecodeOS(frame[2:])
            elif frame[0:2]=='30':
                self.temp=self.DecodeRFX(frame[2:])
            elif frame[0:2]=='20'and frame[0:6]!='2040BF':
                self.temp=self.DecodeX10(frame[2:])
            elif frame[0:6]=='2040BF':
                self.temp=self.DecodePresence(frame[2:])
            else :
                self.temp=self.Unknown(frame)
        else:
            self.temp=self.Unknown(self.internalFrame)
        
        return self.temp
            
    
    def checkCompletFrame(self, frame):
        isCompletFrame = False
        #on cherche si la trame courante est complete, cela veut dire que la trame suivante commence par un des labels
        for label, length in self.tramDictionnary.items():
            if not isCompletFrame:
                if (str(frame[0:2]) ==label) & (len(frame)==length):
                    isCompletFrame = True
                    break
            else:
                #write to file
                day = str(date.today().day) + '/' + str(date.today().month) + '/' + str(date.today().year)
                hour = str(datetime.datetime.today().hour) + ':' + str(datetime.datetime.today().minute) + ':' + str(datetime.datetime.today().second)
                rfxfile = open('errorFrameRFX.txt',"a",encoding='utf-8')
                rfxfile.write(hour+','+day+': error frame :'+frame+"\n")
                rfxfile.close()
                
                print ("Sorry, it is not a complete tram")
                break
            
        return  isCompletFrame
    
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
        chaine=chaine.replace('B','1011')
        chaine=chaine.replace('C','1100')
        chaine=chaine.replace('D','1101')
        chaine=chaine.replace('E','1110')
        chaine=chaine.replace('F','1111')
        return chaine
    
    def BintoNum(self,chaine):
        i=0
        num=0
        while (i<len(chaine)):
            num = num + int(chaine[i])*2**((len(chaine)-1)-i)
            i+=1
        return num
    
    def DecodeRFX(self,trame): #RFXMeter Frames
        trame=self.HexToBin(trame)
        RFXdic={"protocole":"rfx"}
        address=self.BintoNum(trame[0:16]) #Address
        RFXdic["adresse"]=address
        energy=float(self.BintoNum(trame[16:32])) #Energy
        energy=energy/1000
        RFXdic["energie"]=energy
        byte=trame[40:48]
        paquetType=self.BintoNum(byte[0:4]) #Type
        RFXdic["paquettype"]=paquetType
        parite=byte[4:8] #Parity
        RFXdic["parite"]=parite
        date = time.localtime()
        date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
        RFXdic["date"]=date
        return RFXdic
    
    def DecodeOS(self,trame): #Oregon Scientific frames
        sensors={1:58,2:222,3:211,4:252,5:26,6:90,7:79,8:241,9:180,10:69} #Everytime batteries are changed, this list needs to be actualised
        trame=self.HexToBin(trame)
        id= trame[0:8] + trame[8:16]
        if self.BintoNum(id) == 64040: #Outside Temperature Sensor
            OSdic={"protocole":"osTemp", "id":64040,"checksum":0}
            byte2 = trame[16:24]
            channel=self.BintoNum(byte2[0:4]) #Channel
            address=self.BintoNum(trame[24:32])
            """if sensors[channel]!=address or channel<1 or channel>10: #Sensor outside PREDIS
                print "Frame received from an extern sensor"
                return 0"""
            if 1 :
                OSdic["canal"] = channel
                OSdic["adresse"] = address #Address
                byte4 = trame[32:40]
                temp3 = self.BintoNum(byte4[0:4]) #Decimale temperature
                OSdic["batterie"] = byte4[5]
                byte5=trame[40:48]
                temp1 = self.BintoNum(byte5[0:4]) #Dizaine temperature
                temp2 = self.BintoNum(byte5[4:8]) #Unite temperature
                temperature = str(temp1) + str(temp2) + str('.') + str(temp3)
                byte6 = trame[48:56]
                hum2 =self.BintoNum(byte6[0:4])
                signe = self.BintoNum(byte6[4]) #Signe temperature
                if signe == '1' : temperature = str('-') + temperature
                OSdic["temperature"] = float(temperature)
                byte7 = trame[56:64]
                humstatus = self.BintoNum(byte7[0:2]) #status humidity
                if humstatus == 0: OSdic["hum_stat"]="normal"
                elif humstatus == 1: OSdic["hum_stat"]="comfort"
                elif humstatus == 2: OSdic["hum_stat"]="dry"
                elif humstatus == 3: OSdic["hum_stat"]="wet"
                hum1 = self.BintoNum(byte7[4:8])
                OSdic["humidite"]=hum1*10+hum2 #Humidity (percent)
                checksum1 = self.BintoNum(trame[64:72])
                i=0
                somme=0
                while (i<8):
                    octet = trame[i*8:(i+1)*8]
                    demioctet1 = self.BintoNum(octet[0:4])
                    demioctet2 = self.BintoNum(octet[4:8])
                    somme = somme + demioctet1 + demioctet2
                    i += 1
                if (checksum1 == somme - 10) :
                    OSdic["checksum"] = '1' #'1' for correct frame
                    date = time.localtime()
                    date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
                    OSdic["date"]=date
        elif self.BintoNum(id) == 6793:  #anemometer
            OSdic={"protocole":"osAnem", "id":6793 ,"checksum":0}
            OSdic["adresse"] = self.BintoNum(trame[24:32]) #Address
            byte4 = trame[32:40]
            dir3 = self.BintoNum(byte4[0:4]) #Unite angle
            util = self.BintoNum(byte4[4:8]) #charge batterie (%)
            OSdic["batterie"]=100-util*10
            byte5=trame[40:48]
            """on n'utilise pas dir1 et dir2 pour donner la direction
            #Le premier chiffre de l'angle
            dir1 = self.BintoNum(byte5[0:4])
            #Le deuxieme chiffre de l'angle
            dir2 = self.BintoNum(byte5[4:8])
            """
            dir = dir3*360/16. #precision de (360/16) degres
            OSdic["direction"]=int(dir)
            byte6 = trame[48:56]
            speed2 =self.BintoNum(byte6[0:4]) #vitesse 2
            speed3=self.BintoNum(byte6[4:8]) #vitesse 3
            byte7 = trame[56:64]
            avspeed3 = self.BintoNum(byte7[0:4]) #vitesse moyenne 3
            speed1 = self.BintoNum(byte7[4:8]) #vitesse 1
            speed=speed1*10 + speed2 + speed3/10.
            OSdic["vitesse"] = speed
            byte8 = trame[64:72]
            avspeed1 = self.BintoNum(byte7[0:4]) #vitesse moyenne 1
            avspeed2 = self.BintoNum(byte7[4:8]) #vitesse moyenne 2
            avspeed = avspeed1*10 + avspeed2 + avspeed3/10.
            OSdic["vitesse_moyenne"] = avspeed
            checksum1 = self.BintoNum(trame[72:80])
            i=0
            somme=0
            while (i<8):
                octet = trame[i*8:(i+1)*8]
                demioctet1 = self.BintoNum(octet[0:4])
                demioctet2 = self.BintoNum(octet[4:8])
                somme = somme + demioctet1 + demioctet2
                i += 1
            if (checksum1 == somme - 10) :
                OSdic["checksum"] = '1' #'1' for correct frame
            date = time.localtime()
            date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
            OSdic["date"]=date
        else: #OS module unknown
            OSdic={"protocole":"", "date":""}
            OSdic["protocole"] = "Unknown"
            date = time.localtime()
            date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
            OSdic["date"]=date
        return OSdic
    
    def DecodeX10(self,trame): # X10 frames
        trame=self.HexToBin(trame)
        X10dic = {"protocole":"X10", "maison":"", "adresse":0, "tous":0, "ordre":0, "date":""}
        Maisondic = {0:"M",1:"N", 2:"O", 3:"P", 4:"C", 5:"D", 6:"A", 7:"B", 8:"E", 9:"F", 10:"G", 11:"H", 12:"K", 13:"L", 14:"I", 15:"J"}
        byte0=trame[0:8]
        maison=self.BintoNum(byte0[0:4]) #House
        maison=Maisondic[maison]
        X10dic["maison"]=maison
        byte2=trame[16:24]
        X10dic["tous"]=byte2[0]
        if byte2[2]=='0':
            X10dic["ordre"]='On'
        elif byte2[2]=='1':
            X10dic["ordre"]='Off'
        else:
            X10dic["ordre"]='Unknown'
        adresse= [0,0,0,0] #address equipement
        adresse[1] = byte2[1]
        adresse[2] = byte2[4]
        adresse[3] = byte2[3]
        adresse[0] = byte0[5]
        print('Adresse a decoder : ',adresse)
        adr= self.BintoNum(str(adresse[0])+str(adresse[1])+str(adresse[2])+str(adresse[3]))+1
        X10dic["adresse"]= adr
        date = time.localtime()
        date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
        X10dic["date"]=date
        return X10dic
    
    def DecodePresence(self,trame): # X10 frames
        trame=self.HexToBin(trame)
        X10dic = {"protocole":"presence", "maison":"", "adresse":0, "tous":0, "presence":0, "date":""}
        Maisondic = {0:"M",1:"N", 2:"O", 3:"P", 4:"C", 5:"D", 6:"A", 7:"B", 8:"E", 9:"F", 10:"G", 11:"H", 12:"K", 13:"L", 14:"I", 15:"J"}
        byte0=trame[0:8]
        maison=self.BintoNum(byte0[0:4]) #House
        maison=Maisondic[maison]
        X10dic["maison"]=maison
        byte2=trame[16:24]
        X10dic["tous"]=byte2[0]
        if byte2[2]=='0':
            X10dic["presence"]='presence'
        elif byte2[2]=='1':
            X10dic["presence"]='no presence'
        else:
            X10dic["ordre"]='Unknown'
        adresse= [0,0,0,0] #address equipement
        adresse[1] = byte2[1]
        adresse[2] = byte2[4]
        adresse[3] = byte2[3]
        adresse[0] = byte0[5]
        print('Adresse a decoder : ',adresse)
        adr= self.BintoNum(str(adresse[0])+str(adresse[1])+str(adresse[2])+str(adresse[3]))+1
        X10dic["adresse"]= adr
        date = time.localtime()
        date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
        X10dic["date"]=date
        return X10dic
    
    def Unknown(self,frame): #Unknown frame
        dic={"protocole":"unknown","frame":"", "date":""}
        dic["frame"] = frame
        date = time.localtime()
        date = str(date[1]) + "/" + str(date[2]) + "/" + str(date[0]) +" at " + str(date[3]) +":" + str(date[4]) + ":" + str(date[5])
        dic["date"]=date
        return dic