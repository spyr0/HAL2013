'''
Created on 12 aout 2011

@author: stephane(sqlite), minh hoang le (mysql)
'''

__all__=['Database','OdbcMysqlDatabase','SqliteDatabase']

import threading

class Database():
    '''
    General interface to database.
    '''
    def __init__(self,name):
        self.name=name
        self.lock=threading.Lock()
        self.knownDatasources=[]
        self.database=None
        self.connect()
        self.cursor=self.database.cursor()
        self.cursor.execute("SELECT ID FROM datasources")
        records=self.cursor.fetchall()
        if len(records)!=0:
            for record in enumerate(records):
                self.knownDatasources.append(record[1][0])

    def connect(self):
        pass
                    
    def recordData(self,datasourceID,data):
        self.lock.acquire()
        if not datasourceID in self.knownDatasources:
            self.__addDatasource(datasourceID)
        try:
            self.cursor.execute("INSERT INTO data (datasourceID,time,dataIndex,value) VALUES ('%s','%i','%i','%s')"%(datasourceID,data[0],data[1],data[2]))
            self.database.commit()
        except Exception as err:
            print(str(err))
        self.lock.release()
        
    def getData(self,datasourceID,fromDate=0):
        if datasourceID in self.knownDatasources:
            self.lock.acquire()
            self.cursor.execute("SELECT time,dataIndex,value FROM data WHERE datasourceID='%s' AND time>='%i'"%(datasourceID,fromDate))
            records=self.cursor.fetchall()
            self.lock.release()
            return records
        else:
            return ""
        
    def __addDatasource(self,datasourceID):        
        try:
            self.cursor.execute("INSERT INTO datasources (ID) VALUES ('%s')"%(datasourceID))
        except:
            pass #datasource still exists
        self.knownDatasources.append(datasourceID)
        
    def close(self):
        self.database.commit()
        self.database.close()

class OdbcMysqlDatabase(Database):
    '''
    Interface to a sqlite3 database.
    '''
    def __init__(self,name):
        Database.__init__(self,name)

    def connect(self):
        pyodbc = __import__("pyodbc",globals(),locals(),fromlist=['*'])
        self.database=pyodbc.connect("DRIVER={MySQL ODBC 5.1 Driver};SERVER=localhost;DATABASE=%s;UID=root;PWD=root"%(self.name))
        self.cursor=self.database.cursor()
        self.cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'hal' AND table_name = 'datasources'")
        datasourcesExists=int(self.cursor.fetchall()[0][0])

        self.cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'hal' AND table_name = 'data'")
        dataExists=int(self.cursor.fetchall()[0][0])

        if (datasourcesExists==0 & dataExists==0):
            print("Please create database "+self.name+" yourself:")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS datasources (ID VARCHAR(255) PRIMARY KEY UNIQUE NOT NULL)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS data (datasourceID VARCHAR(255) NOT NULL, time INTEGER NOT NULL, dataIndex INTEGER NOT NULL, value VARCHAR(20), PRIMARY KEY (datasourceID,time), FOREIGN KEY (datasourceID) REFERENCES datasources(ID))")
            self.cursor.execute("CREATE UNIQUE INDEX timeData ON data (datasourceID ASC, time ASC)")
            #quit(-1)

class SqliteDatabase(Database):
    '''
    Interface to a sqlite3 database.
    '''
    def __init__(self,name):
        Database.__init__(self,name)

    def connect(self):
        sqlite3 = __import__("sqlite3",globals(),locals(),fromlist=['*'])
        ospath = __import__("os.path",globals(),locals(),fromlist=['exists'])

        databaseExists=ospath.exists(self.name)
        self.database=sqlite3.connect(self.name,check_same_thread=False)
        self.cursor=self.database.cursor()

        if not databaseExists:
            self.cursor.execute("CREATE TABLE datasources (ID TEXT PRIMARY KEY UNIQUE NOT NULL)")
            self.cursor.execute("CREATE TABLE data (datasourceID TEXT NOT NULL, time INTEGER NOT NULL, dataIndex INTEGER NOT NULL, value VARCHAR(20), PRIMARY KEY (datasourceID,time), FOREIGN KEY (datasourceID) REFERENCES datasources(ID))")
            self.cursor.execute("CREATE UNIQUE INDEX timeData ON data (datasourceID ASC, time ASC)")
            self.database.commit()
