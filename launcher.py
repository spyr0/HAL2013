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
__all__ = []
import configparser
import utils.database;
import webInterface.webserver

if __name__ == '__main__':
    '''
    main launcher to start the Home Abstraction Layer
    '''
    config = configparser.ConfigParser()
    config.read('hal.cfg')
    SERVER_IP_INTERFACE = config['MAIN']['SERVER_IP_INTERFACE']
    SERVER_PORT = int(config['MAIN']['SERVER_PORT'])
    DATABASE = config['MAIN']['DATABASE']
    if DATABASE == 'sqlite':
        DATABASE = utils.database.SqliteDatabase('hal.sqlite')
    elif DATABASE == 'mysql':
        DATABASE = utils.database.OdbcMysqlDatabase('hal')
    else:
        print('Unknwon database in config.py: "',DATABASE,'"')
        exit(1)

    hierarchicalResourceModel=webInterface.webserver.HierarchicalResourceModel(DATABASE)
    httpd = webInterface.webserver.HalThreadingHTTPServer((SERVER_IP_INTERFACE,SERVER_PORT),webInterface.webserver.HalHttpRequestHandler, hierarchicalResourceModel)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    DATABASE.close()
