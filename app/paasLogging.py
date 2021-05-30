# -*- coding: utf-8 -*-
#Description
"""
==============================================================================
created    : 07/16/2020

Last update: 07/17/2020

Developer: Yishan Tsai 

Lite Version 1 @Yishan05212020

Filename: logging.py

Description: set logging config
==============================================================================
"""
print "-----into paasLogging.py-----"
#=======================================================
# System level modules
#=======================================================
#{{{
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler

from sqlalchemy import *

from app import *
#Yishan@05212020 added for common modules
from app.modules import *
print "==========paasLogging======="
print "appPaaS-> ",appPaaS
#}}}

#=======================================================
# for logger processing from other API modules 
# Mesg Type: Info, Error, Warn, 
#=======================================================
# {{{ logger_handler('sapidoSystem',mesgType, message)
def logger_handler(system,mesgType, message,sysmessage):
    systems = globals()

    print "<datetime>: ",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]," | <system>: ",system," | <mesgType>: ",mesgType," | <message>: ",message," | <sysmessage>: ",sysmessage
    systems["loggingToPostgreSQLHandler"].set_system(system)

    if mesgType == 'Info':
        systems["logging{}".format(system)].info('{}\n'.format(message))
        systems["loggingToPostgreSQL"].info(sysmessage)
    if mesgType == 'Warning':
        systems["logging{}".format(system)].warning('{}\n'.format(message))
        systems["loggingToPostgreSQL"].warning(sysmessage)
    elif mesgType == 'Error':
        systems["logging{}".format(system)].error('{}\n'.format(message))
        systems["loggingToPostgreSQL"].error(sysmessage)
    else:
        systems["logging{}".format(system)].critical('{}\n'.format(message))
        systems["loggingToPostgreSQL"].critical(sysmessage)
    
    # if mesgType == 'Info':
    #     systems["system_logger"][system].info('{}\n'.format(message))
    # if mesgType == 'Warning':
    #     systems["system_logger"][system].warning('{}\n'.format(message))
    # elif mesgType == 'Error':
    #     systems["system_logger"][system].error('{}\n'.format(message))
    # else:
    #     systems["system_logger"][system].critical('{}\n'.format(message))

# }}}

#=======================================================
# for logger processing 
#=======================================================
# {{{ applogger()
def applogger(app):
    systems = globals()
    local_variables = locals()

    tempsystemlist = globalvar.SYSTEMLIST[globalvar.SERVERIP]
    #加入固定PaaS系統logging
    tempsystemlist.append("PaaS")

    # FORMAT = '[%(asctime)s] %(levelname)s %(name)s {%(filename)s:%(lineno)d} in (P:%(process)d T:%(thread)d) - %(message)s'
    FORMAT = '[%(asctime)s] %(levelname)s {%(filename)s:%(lineno)d} in (P:%(process)d T:%(thread)d) - %(message)s'

    # systems["system_logger"] = {}
    for i in tempsystemlist:
        local_variables["rotateLogFile_{}".format(i)] = os.path.join(ROOT_DIR,"log_%s"%(app.name))
        
        #不同系統建立不同logger
        systems["logging{}".format(i)] = logging.getLogger("logging{}".format(i))
        # #在golbal變數中存入system_logger以利後來抓取各系統的logger
        # systems["system_logger"][i] = logging.getLogger("logging{}".format(i))
        #Yishan 10082019 add use_gzip=True to compress
        local_variables["loghandler_".format(i)] = ConcurrentRotatingFileHandler(local_variables["rotateLogFile_{}".format(i)],\
                                maxBytes = 5*1024*1024,\
                                use_gzip = True,\
                                backupCount = 10) # keep 10 files each with max 5MB  
        local_variables["loghandler_".format(i)].setFormatter(logging.Formatter(FORMAT))
        local_variables["loghandler_".format(i)].setLevel(logging.WARNING)
        systems["logging{}".format(i)].addHandler(local_variables["loghandler_".format(i)])
        app.logger.addHandler(systems["logging{}".format(i)])

    #Yishan10222020 add 將logging計入寫入資料庫
    #https://stackoverflow.com/questions/54581554/logging-sqlalchemy-to-database
    #https://stackoverflow.com/questions/52728928/setting-up-a-database-handler-for-flask-logger
    systems["loggingToPostgreSQL"] = logging.getLogger("loggingToPostgreSQL")
    loggingToPostgreSQLHandler = DatabaseLoggingHandler()
    loggingToPostgreSQLHandler.set_system(None)
    loggingToPostgreSQLHandler.setFormatter(logging.Formatter(FORMAT))
    loggingToPostgreSQLHandler.setLevel(logging.WARNING)
    systems["loggingToPostgreSQLHandler"] = loggingToPostgreSQLHandler 
    systems["loggingToPostgreSQL"].addHandler(loggingToPostgreSQLHandler)
    app.logger.addHandler(systems["loggingToPostgreSQL"])
    print "^^^^^^^^^^^^^^^^^^"
    print app.logger.__dict__
    
    #  # http://stackoverflow.com/questions/33516408/python-singleton-logging-not-working-properly-duplicate-log-statements-in-the
    app.logger.propagate = False

    app.catch_exception = catch_exception
# }}}

def catch_exception(exception, sys_exc_info, system, doLoggerHandler=True):
    regexDict = {
        "Warning":r'Warning',
        "Error":r'Error',
        "Fatal":r'Fatal'
    }
    thislogtype = "Warning"
    error_class_name = exception.__class__.__name__ #取得錯誤類型
    for logtype in regexDict.keys():
        # 20210318@Yishan add re.IGNORECASE 忽略大小寫
        if re.search(regexDict[logtype],str(error_class_name),re.IGNORECASE):
            thislogtype = logtype
    print "~~~~exception.args~~~~~"
    print exception.args
    detail = exception.__dict__ #取得詳細內容
    if exception.args: detail = exception.args[0] #取得詳細內容
    exc_type, exc_value, exc_traceback_obj = sys_exc_info #取得Call Stack(依序為：異常類型，異常的值，traceback object)
    lastCallStack = traceback.extract_tb(exc_traceback_obj)[-1] #取得Call Stack的最後一筆資料
    fileName = lastCallStack[0] #取得發生的檔案名稱
    lineNum = lastCallStack[1] #取得發生的行號
    funcName = lastCallStack[2] #取得發生的函數名稱
    sysmessage = {
        "fileName":fileName,
        "lineNum":lineNum,
        "funcName":funcName,
        "errorType":error_class_name,
        "detail":detail
    }
    # print "~~~sysmessage~~"
    # print sysmessage
    try:
        # err_msg = "<{} {}>Unexpected error : File \"{}\", line {}, in {}: [{}] {}\n".format(request.method, request.path, fileName, lineNum, funcName, error_class_name, detail)
        err_msg = "<{} {}>Unexpected error : in {}: [{}] {}\n".format(request.method, request.path, funcName, error_class_name, detail)
        sysmessage["method"] = request.method 
        sysmessage["path"] = request.path 
    except:
        err_msg = "Unexpected error : File \"{}\", line {}, in {}: [{}] {}\n".format(fileName, lineNum, funcName, error_class_name, detail)
        sysmessage["method"] = "ERROR" 
        sysmessage["path"] = "ERROR"
    
    sysmessage = AdjustDataFormat().format(sysmessage)
    # print type(sysmessage)
    sysmessage = json.dumps(sysmessage)
    # print type(sysmessage)
    # print "~~~sysmessage~~"
    # print sysmessage

    if doLoggerHandler:
        #統一在此紀錄logging
        logger_handler(system,thislogtype, err_msg, sysmessage)
        
    return err_msg

# class DatabaseLoggingHandler(logging.StreamHandler):
class DatabaseLoggingHandler(logging.Handler):
    # def __init__(self):
    #     # super().__init__()
    #     FORMAT = '[%(asctime)s] %(levelname)s {%(filename)s:%(lineno)d} %(thread)d - %(message)s'
    #     self.setFormatter(logging.Formatter(FORMAT))
    #     self.setLevel(logging.WARNING)
    
    def set_system(self,system):
        self.system = system
        # print "==============="
        # print self.system

    def emit(self, record):
        try:
            seterror = False
            # print "==============="
            # print self.system
            if (self.system is None) or (self.system == ""):
                raise Exception("not set system")

            if not retrieve_database_exist(system=self.system,dbName=globalvar.PAAS_DASHBOARD_DBNAME["POSTGRES"],forRawData="postgres")[0]:
                create_database(self.system,globalvar.PAAS_DASHBOARD_DBNAME["POSTGRES"],forRawData="postgres")

            DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(dbName=globalvar.PAAS_DASHBOARD_DBNAME["POSTGRES"], system=self.system, forRawData="postgres")
            if not DbSessionRaw is None:
                sessRaw = DbSessionRaw()
                if self.system.lower() == "paas":
                    tableName = "paas_log_"+time.strftime("%Y%m", time.localtime())
                else:
                    tableName = self.system.lower()+"_paas_log_"+time.strftime("%Y%m", time.localtime())

                # print "~~~tableName~~~~"
                # print tableName

                table_attr = [
                    {"name":"acstime","type":"TIMESTAMP","length":"","primarykey":"","nullable":"false","comment":"Human-readable time when the LogRecord was created"},
                    {"name":"levelname","type":"VARCHAR","length":"10","primarykey":"","nullable":"","comment":"日誌的等級名稱"},
                    {"name":"filename","type":"VARCHAR","length":"128","primarykey":"","nullable":"","comment":"Filename portion of pathname"},
                    {"name":"lineno","type":"VARCHAR","length":"50","primarykey":"","nullable":"","comment":"Source line number where the logging call was issued"},
                    {"name":"process","type":"VARCHAR","length":"100","primarykey":"","nullable":"","comment":"Process ID"},
                    {"name":"thread","type":"VARCHAR","length":"100","primarykey":"","nullable":"","comment":"Thread ID"},
                    {"name":"message","type":"JSON","length":"","primarykey":"","nullable":"","comment":"錯誤訊息 {'method':'request method','path':'request path','fileName':'發生的檔案名稱','lineNum':'發生的行號','funcName':'發生的函數名稱','errorType':'錯誤類型','detail':'錯誤詳細內容'}"},
                ]

                if not retrieve_table_exist(metaRaw, tableName, self.system, doLoggerHandler=False):
                    resultRaw ,mesgRaw = create_table(table_name=tableName, dbName=globalvar.PAAS_DASHBOARD_DBNAME["POSTGRES"], attrList=table_attr, table_comment=self.system.lower()+"_PaaS API日誌",doLoggerHandler=False,system=self.system)
                    # print "~~~resultRaw~~~~"
                    # print resultRaw
                    # print "~~~mesgRaw~~~~"
                    # print mesgRaw
                    #建表失敗
                    if not resultRaw: seterror = True
                
                # print "~~~seterror~~~~"
                # print seterror

                if not seterror:
                    self.format(record)

                    log_time = datetime.strptime(record.__dict__['asctime'], "%Y-%m-%d %H:%M:%S,%f")

                    reqdataDict = {
                        # "upload_at":log_time,
                        "acstime":log_time,
                        "levelname":record.__dict__["levelname"],
                        "filename":record.__dict__["filename"],
                        "lineno":record.__dict__["lineno"],
                        "process":record.__dict__["process"],
                        "thread":record.__dict__["thread"],
                        "message":record.__dict__["message"]
                    }
                    
                    logTable = Table(tableName, metaRaw,  autoload=True)
                    # print "~~~logTable~~~~"
                    # print logTable
                    # print '~~~~record.__dict__["message"]~~~~'
                    # print record.__dict__["message"]
                    # print type(record.__dict__["message"])

                    sqlInsert = logTable.insert().values(reqdataDict)
                    sessRaw.execute(sqlInsert)
                    sessRaw.commit()

        except Exception as e:
            print "############"
            print e
            # err_msg = app.catch_exception(e,sys.exc_info(),self.system)
        
        finally:
            if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
                sessRaw.close()
                DbSessionRaw.remove()
                engineRaw.dispose()