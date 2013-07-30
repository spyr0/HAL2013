'''
A 'Resource' corresponds to a node in the URL namespace hierarchy.
A 'ResourceExposer' is created for each resource. It contains the methods that are accessible through the HAL webserver
Created on 15 juil. 2011
@author: stephane
'''
__all__ = ["Resource"]

import datetime,time

def xmlEncapsulate(message,isOk=True):
    if isOk:
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><message><status>ok</status>%s</message>"%(message)
    else:
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><message><status>error</status>%s</message>"%(message)
    
class Resource(object):
    '''
    A resource is defined by an URL. It may be a thermal zone, a room, an appliance or a service
    '''
    def __init__(self,name,resourceType,database=None):#(name:string,type:string)
        self.name=name
        self.type=resourceType
        self.container=None
        self.database=database
        self.containedResources=dict()
        self.datasources=dict()
        self.controllers=dict()
        self.requestBuffers=dict()
        self.resourceExposer=ResourceExposer(self)
        
    def getName(self):#()->string
        return self.name
    
    def getExposer(self):#()->ResourceExposer
        return self.resourceExposer
    
    def getType(self):#()->string
        return self.type
    
    def getURL(self):#()->string
        if self.container==None:
            return '/'
        else:
            parent=self.container
            url='/'+self.name
            while parent.getContainer()!=None:
                url='/'+parent.getName()+url
                parent=parent.getContainer()
            return url
        
    def getContainer(self):#()->string
        return self.container
    
    def setContainer(self,container):#(string)->string
        self.container=container
        
    def getContainedResources(self):#()->listIterator
        return self.containedResources.values()
    
    def addContainedResource(self,resource):#(Resource)
        self.containedResources[resource.getName()]=resource
        resource.setContainer(self)
        
    def getResource(self,pathToResource):#(string)->Resource
        if len(pathToResource)==0:
            return self
        elif pathToResource[0] in self.containedResources:
            return self.containedResources[pathToResource[0]].getResource(pathToResource[1:])
        else:
            return None
        
    def registerDatasource(self,datasource):
        self.datasources[datasource.getName()]=datasource
        
    def getDatasources(self):
        return self.datasources
    
    def getDatasource(self,datasourceName):
        if datasourceName in self.datasources:
            return self.datasources[datasourceName]
        else:
            return None
        
    def registerController(self,controller):
        self.controllers[controller.getName()]=controller
        
    def getControllers(self):
        return self.controllers
    
    def getController(self,controllerName):
        if controllerName in self.controllers:
            return self.controllers[controllerName]
        else:
            return None
        
    def registerRequestBuffer(self,requestBuffer):
        self.requestBuffers[requestBuffer.getName()]=requestBuffer
        
    def getRequestBuffers(self):
        return self.requestBuffers
    
    def getRequestBuffer(self,requestBufferName):
        if requestBufferName in self.requestBuffers:
            return self.requestBuffers[requestBufferName]
        else:
            return None
        
    def setData(self,name,value):#(string,double_tupleOfDouble)
        self.datasources[name]=value

class ResourceExposer(object):
    def __init__(self,resource):#(Resource)
        self.resource=resource
        
    def description(self,parameters):
        '''
        provide a XML description of the resource
        '''
        response="<name>%s</name><url>%s</url><type>%s</type>"%(self.resource.getName(),self.resource.getURL(),self.resource.getType())
        for datasourceName in self.resource.getDatasources():
            response+="<datasource><name>%s</name></datasource>"%(datasourceName)
        for requestbufferName in self.resource.getRequestBuffers(): 
            response+="<requestbuffer><name>%s</name>"%(requestbufferName)
            possibleRequests=self.resource.getController(requestbufferName).getPossibleControlParameters() ################# bug 
            for possibleRequest in possibleRequests:
                response+=possibleRequest
            response+="</requestbuffer>"
        for controllerName in self.resource.getControllers():
            response+="<controller><name>%s</name>"%(controllerName)
            possibleControls=self.resource.getController(controllerName).getPossibleControlParameters()
            for possibleControl in possibleControls:
                response+=possibleControl
            response+="</controller>"
        if len(self.resource.getContainedResources())!=0:
            response+="<containedResources>"
            for containedResource in self.resource.getContainedResources():
                response+="<resource>%s</resource>"%(containedResource.getURL())
            response+="</containedResources>"
        return xmlEncapsulate(response)
    
    def history(self,parameters):
        '''
        Provide the historical data from database.
        parameter: during=value where value is the past time windows in minutes from the current time for which data are requested
        parameter: datasource=name specifies the datasource for which data are requested
        '''
        response=""
        duringInMinutes=24*60
        if 'during' in parameters:
            duringInMinutes=int(parameters['during'][0])
        fromDate=time.mktime(datetime.datetime.now().timetuple())-duringInMinutes*60
        if 'datasource' in parameters:
            datasourceNames=parameters['datasource']
            for datasourceName in datasourceNames:
                if datasourceName in self.resource.getDatasources():
                    dataList=self.resource.database.getData(self.resource.getURL()+'/'+datasourceName, fromDate)
                    if dataList!=None:
                        response+="<datasource><name>%s</name>"%(datasourceName)
                        for data in dataList:
                            response+="<data><time>%s</time><index>%s</index><value>%s</value></data>"%(data[0],data[1],data[2])
                        response+="</datasource>"
            return xmlEncapsulate(response)
        else:
            for datasourceName in self.resource.getDatasources():
                dataList=self.resource.database.getData(self.resource.getURL()+'/'+datasourceName, fromDate)
                if dataList!=None:
                    response+="<datasource><name>%s</name>"%(datasourceName)
                    for data in dataList:
                        response+="<data><time>%s</time><index>%s</index><value>%s</value></data>"%(data[0],data[1],data[2])
                    response+="</datasource>"
            return xmlEncapsulate(response)
        
    def data(self,parameters):
        '''
        provide the current values for all the related datasources or, for only the datasources provided as parameters
        parameter: datasource=name specifies the datasource for which data are requested
        '''
        response=""
        if 'datasource' in parameters:
            datasourceNames=parameters['datasource']
            for datasourceName in datasourceNames:
                if datasourceName in self.resource.getDatasources():
                    data=self.resource.getDatasource(datasourceName).getData()
                    if data!=None:
                        response+="<datasource><name>%s</name><time>%s</time><index>%s</index><value>%s</value></datasource>"%(datasourceName,data[0],data[1],data[2])
            return xmlEncapsulate(response)
        else:
            for datasourceName in self.resource.getDatasources():
                data=self.resource.getDatasource(datasourceName).getData()
                if data != None:
                    response+="<datasource><name>%s</name><time>%s</time><index>%s</index><value>%s</value></datasource>"%(datasourceName,data[0],data[1],data[2])
            return xmlEncapsulate(response)
        
    def register(self,parameters):
        '''
        register for all the related datasources or, for only the datasources provided as parameters. Once registered, a client identified by ip number, will be able
        to collect all the upcoming values from either the time it registered or from the time it has collected available values.
        parameter: datasource=name specifies the datasource for which data are registered
        '''
        response=""
        client=parameters['client']
        if 'datasource' in parameters:
            for datasourceName in parameters['datasource']:
                datasource=self.resource.getDatasource(datasourceName)
                if datasource!=None:
                    datasource.register(client)
                    response+="<notification>%s is registered with %s</notification>"%(client,datasourceName)
        else: #register to all available datasource
            for datasourceName in self.resource.getDatasources():
                self.resource.getDatasource(datasourceName).register(client)
                response+="<notification>%s is registered with %s</notification>"%(client,datasourceName)
        return xmlEncapsulate(response)
    
    def unregister(self,parameters):
        '''
        stop collecting upcoming values for all the related datasources or, for only the datasources provided as parameters
        parameter: datasource=name specifies the datasource for which data are unregistered
        '''
        response=""
        client=parameters['client']
        if 'datasource' in parameters:
            for datasourceName in parameters['datasource']:
                dataSource=self.resource.getDatasource(datasourceName)
                if dataSource!=None:
                    dataSource.unregister(client)
                    response+="<notification>%s is no longer registered with %s</notification>"%(client,datasourceName)
        else: #register to all available datasource
            for datasourceName in self.resource.getDatasources():
                self.resource.getDatasource(datasourceName).unregister(client)
                response+="<notification>%s is no longer registered with %s</notification>"%(client,datasourceName)
        return xmlEncapsulate(response)
    
    def collect(self,parameters):
        '''
        collect available values for the registered datasources
        parameter: datasource=name specifies the datasource for which data are collected
        '''
        response=""
        client=parameters['client']
        if 'datasource' in parameters:
            for datasourceName in parameters['datasource']:
                datasource=self.resource.getDatasource(datasourceName)
                if datasource!=None:
                    values=datasource.collect(client)
                    if values != None:
                        response+="<datasource><name>%s</name>"%(datasource.getName())
                        for value in values:
                            response+="<data><time>%i</time><index>%i</index><value>%s</value></data>"%(value)
                        response+="</datasource>"
        else:
            for datasourceName in self.resource.getDatasources():
                values=self.resource.getDatasource(datasourceName).collect(client)
                if values != None:
                    response+="<datasource><name>%s</name>"%(datasourceName)
                    for value in values:
                        response+="<value><time>%i</time><index>%i</index><data>%s</data></value>"%(value)
                    response+="</datasource>"
        return xmlEncapsulate(response)
    
    def request(self,parameters):
        '''
        collect available values for the registered requestBuffers
        parameter: requestbuffer=name specifies the requestbuffer for which data are requested
        parameters: other parameters specify the control request as <parameter>value</parameter>
        '''
        client=parameters['client']
        del(parameters['client'])
        if 'requestbuffer' in parameters:
            for requestBufferName in parameters['requestbuffer']:
                requestBuffer=self.resource.getRequestBuffer(requestBufferName)
                if requestBuffer!=None:
                    return xmlEncapsulate(requestBuffer.push(client,parameters))
                else:
                    return xmlEncapsulate("Unknown requestbuffer '%s'"%(requestBufferName))
        else:
            return xmlEncapsulate("A requestbuffer has to be specified")
        
    def control(self,parameters):
        '''
        collect available values for the registered actionSenders
        parameter: controller=name specifies the controller for which data are sent
        parameters: other parameters specify the control as <parameter>value</parameter>
        '''
        client=parameters['client']
        del(parameters['client'])
        if 'controller' in parameters:
            for controllerName in parameters['controller']:
                controller=self.resource.getController(controllerName)
                if controller!=None:
                    return xmlEncapsulate(controller.send(client,parameters))
                else:
                    return xmlEncapsulate("Unknown controller '%s'"%(controllerName))
        else:
            return xmlEncapsulate("A controller has to be specified")
                