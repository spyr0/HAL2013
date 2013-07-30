'''
Create an action request buffer (Requestbuffer).
If a reference to an action sender is sent to the constructor of the Requestbuffer,
values that are pushed to the buffer are directly send to the control of an appliance.
Otherwise action requests are stored into a buffer for collection by an energy manager.  
Created on 5 août 2011
@author: stephane
'''
__all__ = ["Requestbuffer","Controller"]

import datetime,time,threading
import resources.datasource
import resources.driver
import utils.domains
import json

class Requestbuffer(threading.Thread):
    def __init__(self,name,controller,possibleControls=None):
        threading.Thread.__init__(self)
        if controller==None and possibleControls==None:
            raise RuntimeError('either controller or possibleControls has to be defined when creating a Requestbuffer')
        self.name=name
        self.buffer=list()
        self.controller=controller
        self.bufferLock=threading.Lock()
        self.possibleControls=possibleControls
        self.running=True
    def stop(self):
        self.running=False
    def run(self):
        while self.running:
            time.sleep(.1)
    def isDirect(self):
        return self.controller!=None
    def push(self,client,parameters):
        if self.controller!=None:
            return self.controller.send(client,parameters)    
        else:
            self.bufferLock.acquire()
            jsonControlParameters=parameters['control'][0]
            print(jsonControlParameters)
            error=checkErrorInControlParameters(client,self.possibleControls,jsonControlParameters)
            if error!=None:
                self.lock.release()
                return error
            request=Request(client,jsonControlParameters)
            if request not in self.buffer:
                self.buffer.append(request)
                self.bufferLock.release()
                return request.getXML(len(self.buffer))
            else:
                self.bufferLock.release()
                return "Request sent by %s is already into buffer"%(client)
    def pop(self):
        if self.controller!=None:
            return ""
        else:
            request=None
            self.bufferLock.acquire()
            if len(self.buffer)>0:
                request=self.buffer.pop(0)
            self.bufferLock.release()
            if request!=None:
                return request.getXML(len(self.buffer))
            else:
                return "<ActionRequest><NumberOfAwaitingRequests>0</NumberOfAwaitingRequests></ActionRequest>"
    def getPossibleControlParameters(self):
        if controller!=None:
            return controller.getPossibleControlParameters()
        else:
            return getPossibleControlParameters(self.possibleControls)
        
class Request:
    def __init__(self,client,jsonControlParameters):
        self.jsonControlParameters=jsonControlParameters
        self.xmlBeginRequest="<Requester>%s</Requester>"%(client)
        self.xmlBeginRequest+="<Date>%i</Date>"%(time.mktime(datetime.datetime.utcnow().timetuple()))
        self.xmlBeginRequest+="<Control>"+jsonControlParameters+"</Control>"
    def getJsonControlParameters(self):
        return self.jsonControlParameters
    def getXML(self,bufferSize):
        response="<ControlRequest>"
        response+="<NumberOfAwaitingRequests>%i</NumberOfAwaitingRequests>"%(bufferSize)
        response+=self.xmlBeginRequest
        response+="</ControlRequest>"
        return response
    def __eq__(self,other):
        if other==None and len(self.jsonControlParameters)!=0:
            return False
        elif other==None and len(self.jsonControlParameters)==0:
            return True
        elif len(self.jsonControlParameters)==0 and len(other.jsonControlParameters)!=0:
            return False
        elif len(self.jsonControlParameters)!=0 and len(other.jsonControlParameters)==0:
            return False
        else:
            return self.jsonControlParameters==other.jsonControlParameters 
    
class Controller(threading.Thread):
    '''
    send actions to appliances
    '''
    def __init__(self,name,possibleControls,datasource=None,driver=None):
        '''
        parametersWithDomains is a dictionnary with parameter names as keys and utils.domains as objects
        datasource is defined in datasource
        '''
        threading.Thread.__init__(self)
        self.lock=threading.Lock()
        self.running=True
        self.name=name
        self.datasource=datasource
        self.driver=driver
        self.possibleControls=possibleControls
        self.registeredVirtualControllers=dict()
    def getName(self):
        return self.name
    def stop(self):
        self.running=False
    def run(self):
        while self.running:
            time.sleep(.1)
    def send(self,client,parameters):
        self.lock.acquire()
        jsonControlParameters=parameters['control'][0]
        print(jsonControlParameters)
        error=checkErrorInControlParameters(client,self.possibleControls,jsonControlParameters)
        if error!=None:
            self.lock.release()
            return error
        control="<ControlRequest>"
        control+="<Requester>%s</Requester><Control>"%(client)
        control+=jsonControlParameters
        control+="</Control></ControlRequest>"
        if self.datasource!=None:
            self.datasource.setValue(self.name,jsonControlParameters)
        if self.driver!=None:
            self.driver.setControl(self.name, jsonControlParameters)
        self.lock.release()
        return control
    def getPossibleControlParameters(self):
        return getPossibleControlParameters(self.possibleControls)
    def close(self):
        pass

def checkErrorInControlParameters(client,possibleControls,jsonControlParameters):
    jsonControl=json.loads(jsonControlParameters)
    print(jsonControl)
    if jsonControl==None:
        return "Control sent by %s has not been sent because it does not contain an json formated control parameter"%(client)
    for parameterName in jsonControl:
        for parameterName in jsonControl:
            if parameterName not in possibleControls:
                return "Control sent by %s has not been sent because parameter '%s' is unknown"%(client,parameterName)
            else:
                if not possibleControls[parameterName].contains(jsonControl[parameterName]):
                    return "Control sent by %s has not been sent because value '%s' corresponding to parameter '%s' is unknown"%(client,jsonControl[parameterName],parameterName)
    if len(jsonControl)==0:
        return "Control sent by %s has not been sent because the control parameter does not contain any value"%(client)
    return None

def getPossibleControlParameters(possibleControls):
    possibleControlParameters=list()
    for parameter in possibleControls:
        possibleControlParameters.append("<control><name>"+parameter+"</name>"+possibleControls[parameter].display()+"</control>")
    return possibleControlParameters
    
if __name__ == '__main__':
    possibleControls=dict()
    possibleControls["set"]=utils.domains.TagSet(("on","off"))
    possibleControls["tune"]=utils.domains.Interval(0,1)
    possibleControls["valid"]=utils.domains.ValueSet((0,1))
    ##################################################
    print("* just with a request buffer")
    requestbuffer=Requestbuffer('test',None,possibleControls)
    requestbuffer.start()
    parameters=dict()
    parameters['control']=['{"set":"on","tune":0.654,"valid":0}']
    print(requestbuffer.push('localhost', parameters))
    time.sleep(1)
    print(requestbuffer.push('192.168.0.12', parameters))
    time.sleep(1)
    parameters['control']=['{"valid":1}']
    print(requestbuffer.push('localhost', parameters))
    time.sleep(1)
    for _ in range(0,5):
        print(requestbuffer.pop())
    requestbuffer.stop()
    ##################################################
    print("* with a requestbuffer and a controller")
    controller=Controller("test",possibleControls)
    controller.start()
    requestbuffer=Requestbuffer("test",controller)
    requestbuffer.start()
    parameters['control']=['{"valid":0}']
    print(requestbuffer.push('localhost', parameters)) 
    time.sleep(1)
    print(requestbuffer.push('192.168.0.12', parameters))
    time.sleep(1)
    parameters['control']=['{"valid":1}']
    print(requestbuffer.push('localhost', parameters))
    time.sleep(1)
    requestbuffer.stop()
    controller.stop()
    ##################################################
    print("* with a requestbuffer, a controller and a datasource")
    datasource=resources.datasource.Datasource('control')
    datasource.register('localhost')
    datasource.start()
    controller=Controller("test",possibleControls,datasource)
    controller.start()
    print('possible controls ->')
    print(controller.getPossibleControlParameters())
    requestbuffer=Requestbuffer('test',controller,None)
    requestbuffer.start()
    parameters['control']=['{"valid":0}']
    print(requestbuffer.push('localhost', parameters))
    time.sleep(1)
    print(requestbuffer.push('192.168.0.12', parameters))
    time.sleep(1)
    parameters['control']=['{"valid":1}']
    print(requestbuffer.push('localhost', parameters))
    time.sleep(1)
    values=datasource.collect('localhost')
    for value in values:
        print(value)
    requestbuffer.stop()
    datasource.stop()
    controller.stop()
    #################################################
    print("* just with a controller")
    controller=Controller("test",possibleControls,datasource)
    controller.start()
    parameters['control']=['{"valid":0}']
    print(controller.send('localhost', parameters))
    time.sleep(1)
    print(controller.send('192.168.0.12', parameters))
    time.sleep(1)
    parameters['control']=['{"valid":1}']
    print(controller.send('localhost', parameters))
    time.sleep(1)
    controller.stop()
    #################################################
    print("* just with a controller and a datasource")
    datasource=resources.datasource.Datasource('control')
    datasource.register('localhost')
    datasource.start()
    controller=Controller("test",possibleControls,datasource)
    controller.start()
    parameters['control']=['{"valid":0}']
    print(controller.send('localhost', parameters))
    time.sleep(1)
    print(controller.send('192.168.0.12', parameters))
    time.sleep(1)
    parameters['control']=['{"valid":1}']
    print(controller.send('localhost', parameters))
    time.sleep(1)
    values=datasource.collect('localhost')
    for value in values:
        print(value)
    controller.stop();
    datasource.stop();
    #################################################
    print("* with a controller, a datasource and a driver")
    datasource=resources.datasource.Datasource('example')
    datasource.start()
    driver=resources.driver.MySampleDriver('my driver for sample protocol',10,datasource)
    driver.start()
    controller=Controller("test",possibleControls,datasource,driver)
    controller.start()
    parameters['control']=['{"valid":0}']
    print(controller.send('localhost', parameters))
    time.sleep(1)
    print(controller.send('192.168.0.12', parameters))
    time.sleep(1)
    parameters['control']=['{"valid":1}']
    print(controller.send('localhost', parameters))
    time.sleep(1)
    driver.stop()
    datasource.stop()
    controller.stop()
