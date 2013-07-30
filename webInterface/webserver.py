#!/usr/local/bin/python3.2
'''
The webserver that collects information requests for living places
The websever is provided by the class HalHttpServer.
Possible requests that can be handled correspond to the methods of ResourceExposer (resource.py module).
HalHttpRequestHandler process GET and POST requests that correspond to the first parameter hal_serveur_url?request=XXXX
The living area model depicts by the description/home.py module to direct HAL user requests to the right resource.
The available commands are described in the ResourceExposer class from resource.py module.
Created on 14 juil. 2011
@author: stephane
'''
__version__ = "0.1"
__all__ = ["HalHTTPserver","HierarchicalResourceModel"]

import urllib, http.server #,threading,socket
import socketserver #, BaseHTTPServer
import inspect
import resources.resource
import description.home_predis

class HalThreadingHTTPServer (socketserver.ThreadingMixIn,http.server.HTTPServer):
##class HalHttpServer(http.server.HTTPServer,threading.Thread):
    '''
    Restful Webserver that publishes all the resources of a home
    '''
    def __init__(self, host, handler, hierarchicalResourceModel):
        http.server.HTTPServer.__init__(self, host, handler)
        self.hierarchicalResourceModel=hierarchicalResourceModel
        self.allowedRequests=list()
        for attribute in resources.resource.ResourceExposer.__dict__:
            isMethod=inspect.isfunction(resources.resource.ResourceExposer.__dict__[attribute])
            if isMethod and attribute != '__init__':
                self.allowedRequests.append(attribute)
        self.allowedRequests.sort()
        print("server can be connected at http://%s:%i?do=description" % host )

class HalHttpRequestHandler(http.server.BaseHTTPRequestHandler):
    '''
    HTTP request handler: process GET et PUT http requests
    '''
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        self.end_headers()
    def do_GET(self):
        self.computeRequest()
    def do_POST(self):
        self.computeRequest()
    def computeRequest(self):
        request=urllib.parse.urlparse(self.path,allow_fragments=False)
        if request.path!='/favicon.ico':
            resource=request.path
            parameters=urllib.parse.parse_qs(request.query)
            client=self.address_string()
            if 'do' in parameters and len(parameters['do'])==1 and (parameters['do'][0] in self.server.allowedRequests):
                command=parameters.get('do')[0]
                parameters.pop('do')
                parameters['client']=client
                responseBody=self.server.hierarchicalResourceModel.performResourceRequest(resource,command,parameters)
                if responseBody==None:
                    self.send_error(404)
                else:
                    self.respond(responseBody)
            else:
                message="<html><body><p>Available methods are:</p><ul>"
                for request in self.server.allowedRequests:
                    message+="<li> %s</li>"%(request)
                message+="</ul></body></html>"
                self.respond(message,"text/html")
    def respond(self,responseBody,contentType="text/xml"):
        length=0
        if responseBody!=None:
            length=len(responseBody)
        self.send_response(200)
        self.send_header("Content-type", "%s; charset=utf-8"%(contentType))
        self.send_header("Connection", "close")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header('Content-length', length)
        self.end_headers()
        self.wfile.write(bytes(responseBody,'UTF-8'))

class HierarchicalResourceModel(object):
    '''
    Create all the resources of the home and call the relevant resource exposer to process the do request.
    The method defined by the http parameter url?do=xxx&... is search in the corresponding resource exposer.
    The next parameter url?do=method&parameter1=xxx&parameter2=xxx are also transmitted.
    The response of the resource exposer method is returned.
    '''
    def __init__(self,database):
        self.home=description.home_predis.Home(database)
    def performResourceRequest(self,resourceName,command,parameters):
        pathToResource=list('')
        if resourceName!='/':
            pathToResource=resourceName.split('/')[1:]
        resource=self.home.getResource(pathToResource)
        if resource!=None:
            try:
                function=getattr(resource.getExposer(),command)
                response=function(parameters)
                return response
            except AttributeError as err:
                return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><message><status>bad</status><notification>Error during processing: %s</notification></message>"%(err)
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><message><status>bad</status><notification>Unknown resource %s</notification></message>"%(resourceName)

