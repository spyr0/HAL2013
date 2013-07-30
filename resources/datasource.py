'''
A 'Datasource' is a value provider. A 'DataSubscriber' is created for each client
 (identified by its ip address) when it registers to the datasource.
Created on 16 juil. 2011
@author: stephane
'''
__all__ = ["Datasource","CO2AdviceDatasource","AverageHumidityDatasource","HumidityAdviceDatasource","PmvDatasource"]

import datetime,time,threading
import random, math

class Datasource(threading.Thread):
    '''
    A datasource provides data. Data may come from ab actual appliance or from other datasources for virtual appliances
    '''
    def __init__(self,name,parentRessource,database=None):
        threading.Thread.__init__(self)
        self.name=name
        self.database=database
        self.parentRessource=parentRessource
        self.valueLock=threading.Lock()
        self.registeringLock=threading.Lock()
        self.date=None
        self.value=list()
        self.numberOfReceivedData=0
        self.registeredDataSubscribers=dict()
        self.registeredVirtualDatasources=dict()
        self.lastSaveTime=0
    def stop(self):
        self.running=False
    def run(self):
        self.running=True
        while self.running:
            time.sleep(.1)
    def setValue(self,valueProviderName,value):
        self.valueLock.acquire()
        self.date=time.mktime(datetime.datetime.now().timetuple())
        if (self.date-self.lastSaveTime>1):
            self.lastSaveTime=self.date
            self.value=self.perform(valueProviderName,self.date,value)
            self.numberOfReceivedData+=1
            data=(self.date,self.numberOfReceivedData,self.value)
            if self.database !=None:
                self.database.recordData(self.parentRessource.getURL()+'/'+self.name,data)
        for subscriber in tuple(self.registeredDataSubscribers.values()):
            subscriber.addData(data)
        for virtualDatasource in self.registeredVirtualDatasources:
            self.registeredVirtualDatasources[virtualDatasource].setValue(self.name,self.value)
        self.valueLock.release()
    def getData(self):
        self.valueLock.acquire()
        if self.numberOfReceivedData==0:
            self.valueLock.release()
            return None
        else:
            data=(self.date,self.numberOfReceivedData,self.value)
            self.valueLock.release()
            return data
    def getName(self):
        return self.name
    def register(self,dataSubscriberName,maxSize=1000,overflow=1000):
        self.registeringLock.acquire()
        if dataSubscriberName not in self.registeredDataSubscribers:
            dataSubscriber=DataSubscriber(dataSubscriberName,self,maxSize,overflow) 
            self.registeredDataSubscribers[dataSubscriberName]=dataSubscriber
        self.registeringLock.release()
    def registerVirtualDatasource(self,virtualDatasource,maxSize=1000,overflow=1000):
        self.registeringLock.acquire()
        if virtualDatasource.getName() not in self.registeredDataSubscribers:
            self.registeredVirtualDatasources[virtualDatasource.getName()]=virtualDatasource
        self.registeringLock.release()
    def unregister(self,dataSubscriberName):
        self.registeringLock.acquire()
        if dataSubscriberName in self.registeredDataSubscribers:
            del(self.registeredDataSubscribers[dataSubscriberName])
        self.registeringLock.release()
    def collect(self,dataSubscriberName):#(subscriberName)->listOfValues or None
        self.valueLock.acquire()
        if dataSubscriberName in self.registeredDataSubscribers:
            dataSubscriber = self.registeredDataSubscribers[dataSubscriberName]
            self.valueLock.release()
            return dataSubscriber.collectData()
        else:
            self.valueLock.release()
            return None
    def perform(self,valueProviderName,date,value):
        return value
    def getParentRessource(self):
        return self.parentRessource

class DataSubscriber(object):
    '''
    Use to register datasource subscriber i.e. web client that are interested by all the data of a datasource.
    A datasubscriber is mainly a size-limited buffer that collects data for a subscriber 
    '''
    def __init__(self,dataSubscriberName,datasource,maxSize=1000,overflow=1000):
        self.buffer=list()
        self.bufferSize=0
        self.numberOfLostData=0
        self.maxSize=maxSize
        self.overflow=overflow
        self.datasource=datasource
        self.dataSubscriberName=dataSubscriberName
        self.lock=threading.Lock()
        
    def addData(self,data):
        self.lock.acquire()
        self.buffer.append(data)
        self.lock.release()
        if self.bufferSize<self.maxSize:
            self.bufferSize+=1
        else:
            self.buffer.pop(0)
            self.numberOfLostData+=1
            if self.numberOfLostData>=self.overflow:
                datasource.unregister(self.dataSubscriberName)
                
    def collectData(self):
        self.lock.acquire()
        data=self.buffer
        self.buffer=list()
        self.bufferSize=0
        self.numberOfLostValues=0
        self.lock.release()
        return data

class VirtualDatasource(Datasource):
    '''
    A virtual datasource callects, processes and publishes data coming from other datasources as a standard datasource.
    A virtual datasource can correspond to a virtual sensor or to any kind of state model
    '''
    def __init__(self,name,database=None):
        Datasource.__init__(self,name,database)
        self.valueProviders=dict()
        self.computationLock=threading.Lock()
        
    def perform(self,valueProviderName,date,value):
        self.computationLock.acquire()
        self.valueProviders[valueProviderName]=value
        sumation=0
        for valueProviderName in self.valueProviders:
            sumation+=self.valueProviders[valueProviderName]
        self.computationLock.release()
        return sumation/len(self.valueProviders)

class CO2AdviceDatasource(Datasource):
    '''
    A virtual datasource callects, processes and publishes data coming from other datasources as a standard datasource.
    A virtual datasource can correspond to a virtual sensor or to any kind of state model
    '''
    def __init__(self,name,parentRessource,database=None):
        Datasource.__init__(self,name,parentRessource,database)
        self.valueProviders=dict()
        self.computationLock=threading.Lock()
        self.requiredDatasourceProvider='CO2'
    def perform(self,valueProviderName,date,value): #computations performed to compute the values published by the virtual datasource
        self.computationLock.acquire()
        self.valueProviders[valueProviderName]=value #memorize the value provider, i.e. the datasource that provides the data
        if self.valueProviders[self.requiredDatasourceProvider]<450:
            self.computationLock.release()
            return 'Excellente qualite: taux de CO2 normal de l atmosphere'
        elif self.valueProviders[self.requiredDatasourceProvider]<600:
            self.computationLock.release()
            return 'Qualite moyenne'
        elif self.valueProviders[self.requiredDatasourceProvider]<800:
            self.computationLock.release()
            return 'Qualite moderee: taux de CO2 tolerable en lieu ferme'
        elif self.valueProviders[self.requiredDatasourceProvider]<1000:
            self.computationLock.release()
            return 'Qualite moderee : taux de CO2 correct en lieu ferme'
        elif self.valueProviders[self.requiredDatasourceProvider]<5000:
            self.computationLock.release()
            return 'Qualite faible mais acceptable'
        else:
            self.computationLock.release()
            return 'Danger de mort !!'
        
class AverageHumidityDatasource(Datasource):
    '''
    A virtual datasource callects, processes and publishes data coming from other datasources as a standard datasource.
    A virtual datasource can correspond to a virtual sensor or to any kind of state model
    '''
    def __init__(self,name,parentRessource,database=None):
        Datasource.__init__(self,name,parentRessource,database)
        self.valueProviders=dict()
        self.computationLock=threading.Lock()
    def perform(self,valueProviderName,date,value): #computations performed to compute the values published by the virtual datasource
        self.computationLock.acquire()
        self.valueProviders[valueProviderName]=float(value[0:2]) #memorize the value provider, i.e. the datasource that provides the data
        taux_humidite_moyen=0.
        for valueProvider in self.valueProviders:
            taux_humidite_moyen=taux_humidite_moyen+self.valueProviders[valueProvider]
        if len(self.valueProviders)==0:
            self.computationLock.release()
            return -1
        else:
            self.computationLock.release()
            return taux_humidite_moyen/len(self.valueProviders)
        return taux_humidite_moyen
 
class HumidityAdviceDatasource(Datasource):
    '''
    A virtual datasource callects, processes and publishes data coming from other datasources as a standard datasource.
    A virtual datasource can correspond to a virtual sensor or to any kind of state model
    '''
    def __init__(self,name,parentRessource,database=None):
        Datasource.__init__(self,name,parentRessource,database)
        self.valueProviders=dict()
        self.computationLock=threading.Lock()
        self.requiredDatasource='AverageHumidity'
    def perform(self,valueProviderName,date,value): #computations performed to compute the values published by the virtual datasource
        self.computationLock.acquire()
        self.valueProviders[valueProviderName]=value #memorize the value provider, i.e. the datasource that provides the data
        if self.valueProviders[self.requiredDatasource]<50:
            p=2*self.valueProviders[self.requiredDatasource]
            f=-2*self.valueProviders[self.requiredDatasource]+100 
        else:
            p=-2*self.valueProviders[self.requiredDatasource]+200
            f=-2*self.valueProviders[self.requiredDatasource]+100
        if p>80:
            self.computationLock.release()
            return 'Bonne humidite'
        elif p>50 and f<0:
            self.computationLock.release()
            return'Humidite moyenne : trop humide'
        elif p>50 and f>0:
            self.computationLock.release()
            return 'Humidite moyenne : trop sec' 
        elif p<50 and f<0:
            self.computationLock.release()
            return 'Humidite mauvaise : bien trop humide'
        elif p<50 and f>0:
            self.computationLock.release()
            return 'Humidite mauvaise : bien trop sec'
        
class PmvDatasource(Datasource):
    '''
    A virtual datasource callects, processes and publishes data coming from other datasources as a standard datasource.
    A virtual datasource can correspond to a virtual sensor or to any kind of state model
    '''
    def __init__(self,name,parentRessource,database=None):
        Datasource.__init__(self,name,parentRessource,database)
        self.valueProviders=dict()
        self.computationLock=threading.Lock()
        self.humidityValueProvider='AverageHumidity'
        self.temperatureValueProvider='Temperature1'
    def perform(self,valueProviderName,date,value): #computations performed to compute the values published by the virtual datasource
        self.computationLock.acquire()
        self.valueProviders[valueProviderName]=value #memorize the value provider, i.e. the datasource that provides the data
        #print(self.humidityValueProvider)
        #print(self.temperatureValueProvider)
        print(self.valueProviders)
        if self.humidityValueProvider in  self.valueProviders and  self.temperatureValueProvider in  self.valueProviders:
            H=self.valueProviders[self.humidityValueProvider]
            T=self.valueProviders[self.temperatureValueProvider]
            teneur_en_humidite=H/1000; # Teneur en humidite 
            temperature_piece_fahrenheit=T*1.8+32; # Temperature de la piece (en F)
            temperature_peau_Celcius = -0.0054*T*T + 0.7437*T + 16.616; # Temperature de la peau sous les vetements (depend de la temperature de la piece) (en C)
            temperature_peau_fahrenheit= temperature_peau_Celcius * 1.8 + 32; # Temperature de la peau sous les vetements (en F)
            niveau_habillement = 1.1; # Estimation du niveau d'habillement
            #resistance_habillement = 5.75; # Resistance de  l'habillement (R-value: ft2 F h/Btu) 
            coefficient_convection_thermique = 0.68; # Coefficient de convection thermique (en  Btu/h ft2 F)
            coefficient_de_radiation_thermique= 0.7; # Coefficient de radiation thermique (en  Btu/h ft2 F)
            taux_humidite_a_la_saturation = 0.00002238*temperature_peau_Celcius*temperature_peau_Celcius + 0.000085714*temperature_peau_Celcius + 0.0040833; # Taux d'humidite a la saturation (fonction de la temperature de la peau sous les vetements)
            metabolic_rate= 430.0/19.4; # M=Metabolic rate (en Btu/h ft2)
        
            L=metabolic_rate-niveau_habillement*coefficient_convection_thermique*(temperature_peau_fahrenheit-temperature_piece_fahrenheit)-niveau_habillement*coefficient_de_radiation_thermique*(temperature_peau_fahrenheit-temperature_piece_fahrenheit)-156*(taux_humidite_a_la_saturation-teneur_en_humidite)-0.42*(metabolic_rate-18.43)-0.00076*metabolic_rate*(93.2-temperature_piece_fahrenheit)-2.78*metabolic_rate*(0.0365-teneur_en_humidite); # The thermal load (en Btu/h ft2)
            PMV = 3.155*(0.303*math.exp(-0.114*metabolic_rate) +0.028)*L;
            self.computationLock.release()
            return PMV;
        else:
            self.computationLock.release()
            return -1

# for testing
if __name__ == '__main__':
    datasource=Datasource('my datasource')
    datasource.register('example',100,100)
    datasource.start()
    
    for i in range(100):
        datasource.setValue('sampleValueProvider',random.randint(0,100))
    print(datasource.getData())
    
    for i in range(50):
        datasource.setValue('sampleValueProvider',random.randint(0,100))
    values=datasource.collect('example')
    
    for value in values:
        print("value: %i,%i,%i"%(value))
    time.sleep(1)
    
    for i in range(100):
        datasource.setValue('sampleValueProvider',random.randint(0,100))
    print(datasource.getData())
    values=datasource.collect('example')
    for value in values:
        print("value: %i,%i,%i"%(value))
    datasource.stop()
