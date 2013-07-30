'''
Use to depict a particular living area.
Root is the empty "home" node
System is the root for rooms then appliances (/system/all contains mobile appliances)
/services is the root for services
/zones is the root for thermal zones
/forecasts is the root for forecasts
Created on 15 juil. 2011, Modified 21 Dec. 2011
@author: Stephane Ploix, Minh Hoang Le
'''

__all__ = ["Home"]
from resources.resource import Resource
from resources.datasource import Datasource #,CO2AdviceDatasource,AverageHumidityDatasource,HumidityAdviceDatasource,PmvDatasource
from resources.driver import ZigbeeDriver, RfxcomDriver, Daq8iDriver, MockDriver
from resources.actions import Controller
from utils.domains import TagSet
import configparser

class Home(Resource):
    def __init__(self,database):
        configuration = configparser.ConfigParser()
        configuration.read('hal.cfg')
        MOCK = configuration['MAIN']['MOCK']
        checkingPeriod=float(configuration['MAIN']['CHECKING_PERIOD_IN_SECS'])
        #___________________________DRIVERS________________________
        if MOCK=='yes':
            daq8iDriver=MockDriver(checkingPeriod) #CO2 Driver
            zigbeeDriver = MockDriver(10) #Zigbee Driver
            rfxcomDriver = MockDriver(10) #RfxCom Driver
        else:
            daq8iDriver=Daq8iDriver(10) #CO2 Driver
            zigbeeDriver = ZigbeeDriver(10) #Zigbee Driver
            rfxcomDriver = RfxcomDriver(10) #RfxCom Driver
        daq8iDriver.start()
        zigbeeDriver.start()
        rfxcomDriver.start()
        #___________________________RESOURCES________________________
        # /system
        Resource.__init__(self, '', 'home',database)
        system=Resource('system','system',database)
        self.addContainedResource(system)
        # /system/classroom
        classroom=Resource('classroom','thermalzone',database)
        system.addContainedResource(classroom)
        climateSensors=dict()
        for i in (1,2,3,4):
            climateSensors[i]=Resource('climateSensor'+str(i),'sensor',database)
            classroom.addContainedResource(climateSensors[i])
        # /system/offices
        offices=Resource('offices','thermalzone',database)
        system.addContainedResource(offices)
        for i in (5,6):
            climateSensors[i]=Resource('climateSensor'+str(i),'sensor',database)
            offices.addContainedResource(climateSensors[i])
        # /system/technicalArea
        technicalArea=Resource('technicalArea','thermalZone',database)
        system.addContainedResource(technicalArea)
        for i in (7,8,10):
            climateSensors[i]=Resource('climateSensor'+str(i),'sensor',database)
            technicalArea.addContainedResource(climateSensors[i])
        # /system/outdoor
        outdoor=Resource('outdoor','thermalzone',database)
        system.addContainedResource(outdoor)
        climateSensors[9]=Resource('climateSensor9','sensor',database)
        outdoor.addContainedResource(climateSensors[9])
        # /system/classroom/plugs
        allplugs=Resource('plugs','appliance',database)
        classroom.addContainedResource(allplugs)
        plugs=dict()
        computers=dict()
        switches=dict()
        for i in range(1,16):
            plugs[i]=Resource('plug'+str(i),'appliance',database)
            allplugs.addContainedResource(plugs[i])
            computers[i]=Resource('computer'+str(i),'appliance',database)
            plugs[i].addContainedResource(computers[i])
            switches[i]=Resource('switch'+str(i),'actuator',database)
            plugs[i].addContainedResource(switches[i]) 
        # /system/classroom/presenceSensor
        presenceSensor=Resource('presenceSensor','sensor',database)
        classroom.addContainedResource(presenceSensor)
        # system/classroom/CO2sensor
        co2sensor=Resource('co2sensor','sensor',database)
        classroom.addContainedResource(co2sensor)
        #___________________________CONNECTORS________________________
        temperatureDatasources=dict()
        humidityDatasources=dict()
        for i in range(1,11):
            temperatureDatasources[i]=Datasource('temperature',climateSensors[i],database)
            temperatureDatasources[i].start()
            rfxcomDriver.registerDatasource(('OS',str(i),'temperature'),temperatureDatasources[i])
            climateSensors[i].registerDatasource(temperatureDatasources[i])
            
            humidityDatasources[i]=Datasource('humidity',climateSensors[i],database)
            humidityDatasources[i].start()
            rfxcomDriver.registerDatasource(('OS',str(i),'humidity'),humidityDatasources[i])
            climateSensors[i].registerDatasource(humidityDatasources[i])
            
        #presence sensor
        presenceDatasource=Datasource('presence',presenceSensor,database)
        presenceDatasource.start()
        rfxcomDriver.registerDatasource(('X10','presence'),presenceDatasource)
        presenceSensor.registerDatasource(presenceDatasource)
        
        #CO2 sensor
        co2Datasource=Datasource('concentration',co2sensor,database)
        co2Datasource.start()
        daq8iDriver.registerDatasource(('DAQ8i'),co2Datasource)
        co2sensor.registerDatasource(co2Datasource)
        
        possibleControls=dict()
        possibleControls['switch']=TagSet(('on','off'))
        
        wattmeterDatasources=dict()
        switchDatasources=dict()
        switchControllers=dict()
        for i,plug in plugs.items():
            wattmeterDatasources[i]=Datasource('power',plug,database)
            wattmeterDatasources[i].start()
            zigbeeDriver.registerDatasource(('ZIGBEE',str(i)),wattmeterDatasources[i])
            plug.registerDatasource(wattmeterDatasources[i])
            
            switchDatasources[i]=Datasource('switch',switches[i],database)
            switchDatasources[i].start()
            rfxcomDriver.registerDatasource(('X10','J',str(i)),switchDatasources[i])
            switches[i].registerDatasource(switchDatasources[i])
            
            switchControllers[i]=Controller('switch',possibleControls,switches[i],rfxcomDriver)
            switchControllers[i].start()
            switches[i].registerController(switchControllers[i])
            
#        _________________ Virtual Datasources ______________________________        
#        co2AdviceDatasource=CO2AdviceDatasource('CO2Advice',classroom,database)
#        co2AdviceDatasource.start()
#        CO2.registerVirtualDatasource(co2AdviceDatasource)
#        informaticspace.registerDatasource(co2AdviceDatasource)
#        
#        averageHumidityDatasource=AverageHumidityDatasource('AverageHumidity',classroom,database)
#        averageHumidityDatasource.start()
#        Humidity1.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity2.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity3.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity4.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity5.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity6.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity7.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity8.registerVirtualDatasource(averageHumidityDatasource)
#        Humidity10.registerVirtualDatasource(averageHumidityDatasource)
#        informaticspace.registerDatasource(averageHumidityDatasource)
#        
#        humidityAdviceDatasource=HumidityAdviceDatasource('HumidityAdvice',informaticspace,database)
#        humidityAdviceDatasource.start()
#        averageHumidityDatasource.registerVirtualDatasource(humidityAdviceDatasource)
#        informaticspace.registerDatasource(humidityAdviceDatasource)
#        
#        pmvDatasource = PmvDatasource("pmv",informaticspace,database)
#        pmvDatasource.start()
#        averageHumidityDatasource.registerVirtualDatasource(pmvDatasource)
#        Temperature1.registerVirtualDatasource(pmvDatasource)
#        informaticspace.registerDatasource(pmvDatasource)
        
        #lamp_J1
#        Lamps=Resource('Lamps','appliance',database)
#        informaticspace.addContainedResource(Lamps)
#        
#        plug_J1=Resource('plug1','appliance',database)
#        Lamps.addContainedResource(plug_J1)
#        
#        X10J1=Datasource('X10J1',plug_J1,database)
#        X10J1.start()
#        RFXDriver.registerDatasource(X10J1)
#        
#        X10switch_J1=Resource('X10switch1','actuator',database)
#        plug_J1.addContainedResource(X10switch_J1)
#
#        X10switch_J1.registerDatasource(X10J1)
#        
#        possibleControls['Switch']=TagSet(('on','off','dim','bright'))
#        switchX10_J1=Controller("J1",possibleControls,X10J1,RFXDriver)
#        switchX10_J1.start()
#        X10switch_J1.registerController(switchX10_J1)