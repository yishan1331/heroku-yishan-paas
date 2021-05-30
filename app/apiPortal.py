# -*- coding: utf-8 -*-
#API Portal Description
"""
==============================================================================
created    : 03/23/2017

Last update: 03/31/2021

Developer: Wei-Chun Chang 

Lite Version 1 @Yishan08032019

Filename: apiPortal.py

Description: The script is the portal for the API requests from client apps

Total = 1 APIs
==============================================================================
"""
import sys
#=======================================================
# System level modules
#=======================================================
#{{{

from flask import render_template, make_response

from sqlalchemy import *
# from sqlalchemy.orm import scoped_session, sessionmaker
# from sqlalchemy.engine import create_engine

#Yishan 07302020忽略(sqlalchemy.exc.SAWarning)
import warnings
from sqlalchemy import exc as sa_exc
warnings.filterwarnings('ignore', category=sa_exc.SAWarning)

#Yishan 11102020 加入redis in-memory db to store Validity period data
import redis
import Queue #python2是import Queue，python3是import queue
#}}}

#=======================================================
# User-defined modules
#=======================================================
#{{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
#}}}

# #Yishan@07162020 added for logging module
# from paasLogging import applogger
# #服務啟動時就執行setting logging config，此時尚未有上下文所以須將app當參數帶過去
# applogger(appPaaS)

#==========================features==========================
#Yishan@08292019 added for transition databases management
from features.commonUse.transitionDBHandle import TRANSITIONDB_API
appPaaS.register_blueprint(TRANSITIONDB_API)

#Yishan@03262020 added for update data from remotedb management
from features.commonUse.remoteDBHandle import REMOTEDB_API
appPaaS.register_blueprint(REMOTEDB_API)

#Yishan@12172020 added for in memory databases management
from features.commonUse.inMemoryDBHandle import INMEMORYDB_API
appPaaS.register_blueprint(INMEMORYDB_API)

#Yishan@0326 added for multiple type of databases management
from features.commonUse.mixingDBHandle import MIXINGDB_API
appPaaS.register_blueprint(MIXINGDB_API)

#Wei@03232017 added for user management
from features.specificTable.userHandle import USER_API
appPaaS.register_blueprint(USER_API)

#Yishan@05282020 added for department management
from features.specificTable.departmentHandle import DEPARTMENT_API
appPaaS.register_blueprint(DEPARTMENT_API)
#=======================================================

#==========================APIDOC==========================
#Yishan@08292019 added for commonuse management
from APIDOC.commonuseHandle import COMMONUSE_APIDOC_API
appPaaS.register_blueprint(COMMONUSE_APIDOC_API)
#=======================================================

#==========================SOCKETIO==========================
#Yishan@09102020 added for socketio management
import features.socketHandle
#=======================================================

#==========================DASHBOARD==========================
#Yishan@010272020 added for dashboard modules
from features.dashboard import DASHBOARD_API
appPaaS.register_blueprint(DASHBOARD_API)
#=======================================================
#}}}

#====================================================
# 須等待celery初始化app後才能載入之modules
#====================================================
#Yishan@05282020 added for customized management 專門客製api
from features.customizedHandle import CUSTOMIZED_API,iot_redis_device_keys_init
appPaaS.register_blueprint(CUSTOMIZED_API)

#Wei@03232017 added for sensor management
from features.specificTable.sensorHandle import SENSOR_API
appPaaS.register_blueprint(SENSOR_API)

#Yishan@05282020 added for relatedpg management
from features.specificTable.relatedpgHandle import RELATEDPG_API
appPaaS.register_blueprint(RELATEDPG_API)

#Yishan@010272020 added for email modules
from features.emailHandle import EMAIL_API
appPaaS.register_blueprint(EMAIL_API)
# from features.emailHandle import EMAIL_API, check_todolist_deadline
#=======================================================

#=======================================================
# for a thread to check license every N seconds 
#=======================================================
# {{{ check_Lic(arg):A Thread for license check
import thread #Python3以後thread被廢棄，改為_thread或是使用threading
#wei@2017, use for license check
appPaaS.licCheck = 0 
#with schedule
def check_Lic(arg):
    #appPaaS.licCheck = os.system("/var/www/config/ezclient")
    while True:
        #appPaaS.licCheck = os.system("/var/www/config/ezclient")
        appPaaS.licCheck = 0
        print '\n[{}]:License checking result: {}\n'.format(time.ctime(),appPaaS.licCheck)
        time.sleep(arg)

appPaaS.check_Lic = check_Lic
#initiate a thread to do the job, check license every 12 hours
thread.start_new_thread(check_Lic, (43200, ))
#====================================================
# }}}

#=======================================================
# root URI, use to test API services are alive 
#=======================================================
# {{{ appPaaS.route("/")
@appPaaS.route("/")
def homePage():
    #print '\nIn sessionMgr, Lic: {}\n'.format(appPaaS.licCheck)
    dicRet = appPaaS.preProcessRequest(request, system="PaaS")
    print "*******dicRet********"
    print dicRet
    #reserved for user ID check
    #reUser_id = request.args.get("uid")
    mesg = "<h1 style='color:blue'>sapido-License check failed!</h1>"
    if appPaaS.licCheck == 0:
        mesg = "<h1 style='color:blue'>sapido-PaaS!</h1>"

    print "~~~~mesg~~~~"
    print mesg

    dicRet["message"] = mesg   
    dicRet["Response"] = "ok"
    print "$$$$$$dicRet$$$$$"
    print dicRet
    return jsonify( **dicRet)
# }}}
#=======================================================


@appPaaS.route("/test")
def homePage():
    dicRet = {}
    mesg = "<h1 style='color:blue'>sapido-PaaS!</h1>"

    dicRet["message"] = mesg   
    dicRet["Response"] = "ok"
    print "$$$$$$dicRet$$$$$"
    print dicRet
    return jsonify( **dicRet)

#test for queue
# my_queue = Queue.Queue()
# @appPaaS.route("/TestThreadQueue/<number>")
# def test_thread_queue(number):
#     import threading

#     # 建立 lock
#     lock = threading.Lock()

#     print "now queue size -> ",my_queue.qsize()
#     # global my_queue
#     for i in range(int(number)):
#         my_queue.put("Data %d" % i)

#     print "this pid -> ",os.getpid()
#     print "now queue size -> ",my_queue.qsize()

#     my_worker1 = _WorkerThreadQueue(my_queue, 1, lock, 3)
#     my_worker2 = _WorkerThreadQueue(my_queue, 2, lock, 2)

#     my_worker1.start()
#     my_worker2.start()

#     my_worker1.join()
#     my_worker2.join()
#     print "now queue size -> ",my_queue.qsize()
#     print "Done."

#     return jsonify( **{"test":"ok"})

#=======================================================
# special API to query time, 
#=======================================================
# {{{ appPaaS.route('/api/PaaS/1.0/CommonUse/Time', methods = ['GET']), 
@appPaaS.route('/api/PaaS/1.0/Time',  methods = ['GET'])
def get_time():
    #{{{APIINFO
    '''
    {
        "API_name":"GET /api/1.0/Time",
        "API_application":"查詢現在時間",
        "API_message_parameters":{"time":"string"},
        "API_example":{
            "OperationTime": "0.000",
            "BytesTransferred": 72,
            "time": "2019-08-08 10:21:40",
            "Response": "ok",
            "APIS": "GET /api/1.0/Time"
        }
    }
    '''
    #}}}
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request, system="PaaS")
    err_msg = dicRet["Response"]
    try:
        dicRet['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[::]
        err_msg = "ok" 

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
# }}}

#=======================================================
# Http Request preprocess and post process including 
# 1. first_time  
# 2. before each  
# 3. post process
#=======================================================
# {{{ def preProcessRequest(request,companyUuid=None,dappId=None)
def preProcessRequest(request,system=""):
    err_msg = "ok"
    print "..............................................................................................."
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
    # print "~~~~os.getpid()~~~~"
    # print os.getpid()
    targetApi = "{} {}".format(request.method,request.path)
    #logging.getLogger('fappYott').info("__[0824_request]: {}".format(request))

    #Wei@04132017 block for temperally not usage    
    #if companyUuid:
    #    #check special char in companyUUID
    #    ics = set('[`~!@#$%^&*()_+-={}<>,.?";:|\']+$').intersection(companyUuid)
    #    if ics:
    #        err_msg = "company_uuid={}, /w invalid chars {}".format(companyUuid,ics)

    #if dappId:
    #    #check special char in dappID
    #    ics = set('`~/\?%*:|"<> ').intersection(dappId)
    #    if ics:
    #        err_msg = "dapp_uuid={}, /w invalid chars {}".format(dappId,ics)

    #    #if err_msg == "ok":
    #    """ preflight requests issue, http://jiraccma.itri.org.tw:8080/browse/SAPIDOSYSTEM-23
    #    while handle DEL_BULKSAPIDOSYSTEM from javascript client code,
    #    flask found that `request.args` contained nothing,
    #    but expected values found at `request.form`
    #    and also `request.querystring` contain nothing
    #    """
    #W@03092017 block for testing new feature
    #if request.args:
    #    reqArgOk,err_msg = appPaaS.checkIfRequestArgsValid(request.args)
    #else:
    #    reqArgOk,err_msg = appPaaS.checkIfRequestArgsValid(request.form)
    #if err_msg == "ok":
    #reqSigOk,err_msg = appPaaS.verifyRequestSignature(request)

    dicRet = {}
    dicRet["APIS"] = targetApi
    dicRet["Response"] = err_msg
    dicRet["System"] = system
    return dicRet
# }}}
appPaaS.preProcessRequest = preProcessRequest

# {{{ @appPaaS.before_first_request
@appPaaS.before_first_request
def before_first_request():
    pass
# }}}

# {{{ @appPaaS.before_request
@appPaaS.before_request
def per_request_preprocess():
    if(appPaaS.licCheck != 0): #error
        print "Warning: License expired/License file missing......"
        return "License expired or failed"
    else:
        #if re.search('^\/v2\.\d+\/',request.path):
        #W@03092017, adding for all requests to include time cost
        setattr(request,"request_start_time_",time.time())
    # print "{} | {}".format(os.getpid(),datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::])
    #wei@03152017 test request
    #appPaaS.logging.error("In preProcess: request UID: {}".format(request.args.get("uid")))

    # http://stackoverflow.com/questions/8685678/cors-how-do-preflight-an-httprequest
    # This is to work for the preflight and 2-stage processing to pass the OPTIONs in the first flight
    #dicRet = { "Response" : "ok" }
    #Response = make_response(json.dumps(dicRet))
    #Response.headers.set('Access-Control-Allow-Origin', '*')
    #Response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS, GET, DELETE')
    #Response.headers.set('Access-Control-Allow-Headers',
    #            request.headers.get('Access-Control-Request-Headers', 'Authorization' ))

    if request.method == 'OPTIONS':
        dicRet = { "Response" : "ok" }
        Response = make_response(json.dumps(dicRet))
        Response.headers.set('Access-Control-Allow-Origin', '*')
        Response.headers['Access-Control-Allow-Credentials'] = 'true'
        Response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS, GET, DELETE')
        #wei@04282017 for LAN design
        Response.headers.set('Access-Control-Allow-Headers',
        request.headers.get('Access-Control-Request-Headers', 'Authorization' ))

        return Response
# }}}

# {{{ @appPaaS.teardown_appcontext
@appPaaS.teardown_appcontext
def teardown(exc=None):
    # print "@@@@@@@teardown_appcontext@@@@@"
    # print exc
    # if exc is None:
    #     dbSessionType.commit()
    # else:
    #     dbSessionType.rollback()
    # dbSessionType.remove()

    #在teardown_appcontext清空oauth2建立的db_session，以防session sleep a lot
    OAUTH2_SESS.close()
    OAUTH2_DbSESSION.remove()
    OAUTH2_ENGINE.dispose()
    OAUTH2_DEREDIS.connection_pool.disconnect()
#}}}

# {{{ @appPaaS.after_request
@appPaaS.after_request
def per_request_postprocess(Response):
    # this request is for returning testing string or pure string only APIs 
    # needs to define the key words to distinguish different APIs
    #if not re.search('^\/v2\.\d+\/',request.path):
    #    return Response
    try:
        dicRet = json.loads(Response.data)
        #wei@05022017 for CORS
        Response.headers.set('Access-Control-Allow-Origin', '*')
        #Response.headers['Access-Control-Allow-Credentials'] = 'true'
        Response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS, GET, DELETE')

        nowTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

        if hasattr(request,"request_start_time_"):
            timeCost = time.time()-request.request_start_time_
            dic = { "OperationTime": "{:.3f}".format(timeCost),
                    "THISTIME":nowTime,
                    "BytesTransferred":len(Response.data)}
            # http://stackoverflow.com/questions/22274137/how-do-i-alter-a-Response-in-flask-in-the-after-request-function
            dicRet.update(dic)
            Response.set_data(json.dumps(dicRet))

        if dicRet.has_key('Response') and dicRet.has_key('System'):
            if dicRet.get('Response') != "ok":
                threaddata = [dicRet.get('System'), request.method, request.path, "0", timeCost, nowTime]
            else:
                threaddata = [dicRet.get('System'), request.method, request.path, "1", timeCost, nowTime]

            #暫時先排除為PaaS的api
            # if (dicRet.get('System') != "PaaS" and dicRet.get('System') is not None):
            if dicRet.get('System') is not None:
                # pass
                # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

                #第一版
                # thread.start_new_thread(celery_post_api_count_record, (threaddata, ))

                #第二版 Yishan@12212020 修改thread寫法->threading
                # worker = ApiRecordWorkerThread(os.getpid(), lock, post_api_count_record, threaddata)
                # worker.start()

                #第三版
                from celeryApp.celeryTasks import celery_post_api_count_record
                celery_post_api_count_record.apply_async(args=(threaddata,), routing_key='low', queue="L-queue1")

                # print "@@@@@@@@@@@@@@@",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
                # print "Done.",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

            #traceback.print_exc(file=sys.stdout)

        # if hasattr(request,"request_start_time_"):
        #     apiTimeCost = time.time()-request.request_start_time_
        #     dic = { "OperationTime": "{:.3f}".format(apiTimeCost),
        #             "BytesTransferred":len(Response.data)}
        #     # http://stackoverflow.com/questions/22274137/how-do-i-alter-a-Response-in-flask-in-the-after-request-function
        #     dicRet.update(dic)
        #     Response.set_data(json.dumps(dicRet))

        #     # #Yishan 1220 記錄所有使用者使用API的情形(apipath,OperationTime,fail/success,usetime)
        #     # if dicRet.get('Response') != "ok":
        #     #     Status = "Fail"
        #     # else:
        #     #     Status = "Success"
        #     # thread.start_new_thread(Post_apirecord, ([Status,dicRet.get('APIS'),apiTimeCost], ))
        #     # divider = "================================================================================="
        #     # with open("/var/www/spdpaas/doc/apirecord.txt", "a") as apirecord:
        #     #     if dicRet.get('Response') != "ok":
        #     #         Status = "Fail"
        #     #     else:
        #     #         Status = "Success"
        #     #     apirecord.write("UseTime : {}({})\nAPI Path : {}\nOperationTime : {:.3f}\nStatus : {}\n{}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],int(round(time.time()* 1000)),dicRet.get('APIS'),apiTimeCost,Status,divider))

    except Exception as e:
        print request.path,Response.status_code,Response.status
        regexDict = {
            "APIDOC":r'edoc',
            "DASHBOARD":r'dashboard'
        }
        searchpathDict = {
            "APIDOC":False,
            "DASHBOARD":False
        }
        if Response.status != "404 NOT FOUND":
            for logtype in regexDict.keys():
                # print "~~~~logtype~~~~"
                # print logtype
                if re.search(regexDict[logtype],request.path):
                    searchpathDict[logtype] = True
            # print "~~~~searchpathDict~~~~"
            # print searchpathDict
            searchPath_faviconico = re.search(r'favicon.ico',request.path) #排除favicon.ico
            if searchPath_faviconico is None:
                if not (searchpathDict["APIDOC"] or searchpathDict["DASHBOARD"]):
                # if not searchPath_apidoc:
                    strExcInfo = "'{} {}' exception\n".format(request.method, request.path)
                    strExcInfo += "resp data: {}\n".format(Response.data)
                    strExcInfo += str(sys.exc_info())
                    for i in range(len(searchpathDict.values())):
                        # print "~~~~searchpathDict.values()[i]~~~~~"
                        # print searchpathDict.values()[i]
                        # print "~~~~searchpathDict.keys()[i]~~~~~"
                        # print searchpathDict.keys()[i]
                        if searchpathDict.values()[i]:
                            err_msg = appPaaS.catch_exception(e,sys.exc_info(),searchpathDict.keys()[i])

                    print "---------error----------"
                    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
                    print sys.stdout
                    print traceback
                    print request.path
                    print "=====threading detail=====",os.getpid()
                    print threading.active_count() #用來查看目前有多少個線程
                    # print threading.enumerate() #目前使用線程的資訊
                    print threading.current_thread().name #可以用來查看你在哪一個執行緒當中
                    print
                    traceback.print_exc(file=sys.stdout)
                    #thread.start_new_thread(celery_post_api_count_record, (threaddata, ))
    #wei@05022017 debug
    #appPaaS.logging.error("In post-request: {}".format(Response.headers))

    # print "~~~~~~Return.~~~~~~~",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
    return Response
# }}}

class ApiRecordWorkerThread(threading.Thread):
    def __init__(self, pid, lock, func, threadData):
        threading.Thread.__init__(self)
        self.pid = pid
        self.func = func
        self.lock = lock
        self.threadData = threadData

    def run(self):
        # 取得 lock
        self.lock.acquire()
        print "=====================ApiRecord====================="
        print "------Lock-----",self.pid
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],self.pid
        # print "Lock acquired by pid %d" % self.pid
        print "------threading detail------",os.getpid()
        print threading.active_count() #用來查看目前有多少個線程
        print threading.current_thread().name #可以用來查看你在哪一個執行緒當中

        # # 不能讓多個執行緒同時進的工作
        # print "Worker %d" % (self.num)
        # time.sleep(1)
        self.func(self.threadData)

        # 釋放 lock
        self.lock.release()
        print "------released Lock-----",self.pid
        # print "Lock released by pid %d" % self.pid
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],self.pid
        print "------threading detail------",os.getpid()
        print threading.active_count() #用來查看目前有多少個線程
        print threading.current_thread().name #可以用來查看你在哪一個執行緒當中
        print "=====================ApiRecord end====================="
        print 

class ApiRecordWorkerThread_(threading.Thread):
    def __init__(self, pid, lock, func):
        threading.Thread.__init__(self)
        self.pid = pid
        self.func = func
        self.lock = lock

    def run(self):
        # # 取得 lock
        # self.lock.acquire()
        # print "\n=====================ApiRecord====================="
        # print "------Lock-----",self.pid
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],self.pid
        # # print "Lock acquired by pid %d" % self.pid
        # print "------threading detail------",self.pid
        # print threading.active_count() #用來查看目前有多少個線程
        # print threading.current_thread().name #可以用來查看你在哪一個執行緒當中

        # # 不能讓多個執行緒同時進的工作
        # print "Worker %d" % (self.num)
        # time.sleep(1)
        self.func()

        # # 釋放 lock
        # self.lock.release()
        # print "------released Lock-----",self.pid
        # # print "Lock released by pid %d" % self.pid
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],self.pid
        # print "------threading detail------",self.pid
        # print threading.active_count() #用來查看目前有多少個線程
        # print threading.current_thread().name #可以用來查看你在哪一個執行緒當中
        # print "=====================ApiRecord end====================="
        # print 

#=======================================================
# 計算各api使用紀錄->apirecord.txt
# Date: Yishan 09082020 
#=======================================================
#{{{ def Post_apirecord(threaddata):
def Post_apirecord(threaddata):
    divider = "================================================================================="
    status = threaddata[0]
    apipath = threaddata[1]
    apiTimeCost = threaddata[2]
    with open("/var/www/spdpaas/doc/apirecord.txt", "a") as apirecord:
        apirecord.write("RecordTime : {}({})\nAPI Path : {}\nOperationTime : {:.3f}\nStatus : {}\n{}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],int(round(time.time()* 1000)),apipath,apiTimeCost,status,divider))
#}}}

#=======================================================
# Definition: 初始建立有關oauth2的資料表(存在mysql->paas_dashboard)
# Date: 12142020@Yishan
#=======================================================
#{{{ def oauth2_table_init()
def oauth2_table_init():
    from oauth2.models import Base
    try:
        DbSession,_,engine= appPaaS.getDbSessionType(system="PaaS")
        if DbSession is None:
            print "~~~~~db connect fail before_first_request~~~~"
            print engine
            return

        Base.metadata.create_all(engine)

    except Exception as e:
        print "~~~~Exception before_first_request~~~~"
        print e
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")
        print err_msg

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()
#}}}
if sys._getframe(1).f_globals.get('__name__') == "spdpaas":
    oauth2_table_init()

#==========================OAUTH2==========================
#Yishan@010272020 added for OAUTH2 modules
if sys._getframe(1).f_globals.get('__name__') == "spdpaas":
    from oauth2.routes import OAUTH2_API
    appPaaS.register_blueprint(OAUTH2_API)
    import oauth2.routes
    oauth2.routes.appPaaS = appPaaS
#=======================================================

#=======================================================
# Date: 12292020
# Yishan Tsai
# Only for IoT-chunzu system to do this action
#=======================================================
# if "CHUNZU" in globalvar.SYSTEMLIST[globalvar.SERVERIP] and sys._getframe(1).f_globals.get('__name__') == "spdpaas":
#     #create device init key
#     iot_redis_device_keys_init(selfUse=True)
#=======================================================

#=======================================================
# Date: 03302021
# Yishan Tsai
# 初始設定apirecord的hash numer(apirecord_hash_num)
#=======================================================
if sys._getframe(1).f_globals.get('__name__') == "spdpaas":
    from celeryApp.celeryTasks import apirecord_hash_num_init
    apirecord_hash_num_init()
#=======================================================

#=======================================================
# API /dashboard
# Date: 10162020
# Yishan Tsai
# PaaS Dashboard
#=======================================================
# {{{ appPaaS.route('/dashboard', methods = ['GET'])
@appPaaS.route('/dashboard', methods=['GET'])
def paas_dashboard():
    # print "~~~~os.getpid()~~~~"
    # print os.getpid()
    # if(appPaaS.licCheck == 0) and (system in globalvar.SYSTEMLIST[globalvar.SERVERIP]):
    #     return render_template('index.html',api_map=api_map(system),system=system)
    # else:
    #     return "Not Found"
    # return render_template('index.html')
    return render_template("index.html")
    # return render_template('index.html',api_map=api_map(0,"SAPIDOSYSTEM"))
#}}}

#=======================================================
# API /Dashboard/ApiMap/<SYSTEM>
# Date: 10162020
# Yishan Tsai
# PaaS Dashboard
#=======================================================
# {{{ appPaaS.route('/Dashboard/ApiMap/<SYSTEM>', methods = ['GET'])
@appPaaS.route('/Dashboard/ApiMap/<SYSTEM>', methods=['GET'])
def paas_dashboard_get_apimap(SYSTEM):
    if(appPaaS.licCheck == 0) and (SYSTEM in globalvar.SYSTEMLIST[globalvar.SERVERIP]):
        returndata = {"api_map":api_map(0,SYSTEM),"Response":"ok"}
    else:
        returndata = {"Response":"system:{} is illegal".format(SYSTEM)}
    return jsonify( **returndata)
#}}}

# #=======================================================
# # API /<system>/edoc
# # Date: 08162019
# # Yishan Tsai
# # 顯示所有api列表
# #=======================================================
# # {{{ appPaaS.route('/edoc', methods = ['GET'])
# @appPaaS.route('/apidocList', methods=['GET'])
# def get_apidoc_list(system):
#     if(appPaaS.licCheck == 0) and (system in globalvar.SYSTEMLIST[globalvar.SERVERIP]):
#         return render_template('index.html', api_map=api_map(system),system=system)
#     else:
#         return "Not Found"
# #}}}

#=======================================================
# API /edoc/<endpoint>
# Date: 08162019
# Yishan Tsai
# 返回apidoc
#=======================================================
# {{{ appPaaS.route('/edoc/<endpoint>', methods = ['GET'])
@appPaaS.route('/edoc/<endpoint>', methods=['GET'])
def docs(endpoint):
    # if(appPaaS.licCheck == 0) and (system in globalvar.SYSTEMLIST[globalvar.SERVERIP]):
    if(appPaaS.licCheck == 0):
        api = endpoint_api(endpoint)
        returndata = {"api":api,"Response":"ok"}
        return jsonify( **returndata)
    else:
        returndata = {"Response":"error"}
        return jsonify( **returndata)
#}}}

#=======================================================
# API /sandbox
# Date: 08162019
# Yishan Tsai
# 返回APIDOC sandbox環境測試api
#=======================================================
# {{{ appPaaS.route('/sandbox', methods = ['GET'])
@appPaaS.route('/sandbox', methods=['GET'])
def sandbox():
    # if(appPaaS.licCheck == 0) and (system in globalvar.SYSTEMLIST[globalvar.SERVERIP]):
    if(appPaaS.licCheck == 0):
        returndata = {"Response":"ok","api_map":api_map(2,"APIDOC")}
        return jsonify( **returndata)
    else:
        returndata = {"Response":"error"}
        return jsonify( **returndata)
#}}}

#{{{ edoc def
def api_map(level,SYSTEM=None):
    print "~~~~~SYSTEM~~~~~"
    print SYSTEM
    level_list = ["LEVEL1","LEVEL2","LEVEL3"]
    return [(x[0][1:], x[1], list(x[2].intersection(["GET", "POST", "PATCH", "PUT", "DELETE"]))[0], "/"+"/".join(x[0].split("/")[3:]), x[3]) for x in sorted(list(get_api_map(level_list[level],SYSTEM)))]

def endpoint_api(endpoint,onlydoc=False):
    api = {
        'endpoint': endpoint,
        'methods': [],
        'doc': '',
        'url': '',
        'name': ''
    }
    try:
        func = appPaaS.view_functions[endpoint]

        api['name'] = _get_api_name(func)
        api['doc'] = _get_api_doc(func)

        for rule in appPaaS.url_map.iter_rules():
            if rule.endpoint == endpoint:
                api['methods'] = list(set(rule.methods).intersection(["GET", "POST", "PATCH", "PUT", "DELETE"]))[0]
                api['url'] = "/".join(str(rule).split("/")[2:len(str(rule).split("/"))])
    except:
        api['doc'] = 'Invalid api endpoint: 「{}」!'.format(endpoint)

    if not onlydoc:
        return api
    if isinstance(api["doc"],dict):
        return api["doc"]["API_application"]
    # return api["doc"]
    return "api name: "+api['name']+" | api doc: "+api["doc"]

def _get_api_name(func):
    """e.g. Convert 'do_work' to 'Do Work'"""
    words = func.__name__.split('_')
    words = [w.capitalize() for w in words]
    return ' '.join(words)

def _get_api_doc(func):
    doc = func.__doc__
    if func.__doc__:
        if VerifyDataStrLawyer(doc).verify_json():
            doc_obj = json.loads(doc)
            return doc_obj
        return 'Invalid , API doc is illegal JSON!'
    else:
        return 'Invalid , No doc found for this API!'

def get_api_map(level,SYSTEM):
    """Search API from rules, if match the pattern then we said it is API."""
    level_config = {
        #最高權限(但不包含APIDOC)
        "LEVEL1":r'/api/(?!APIDOC)',
        #只能看到通用系統api
        "LEVEL2":r'/api/<SYSTEM>',
        #只看得到APIDOC
        "LEVEL3":r'/api/APIDOC'
    }
    # regexStr = r'/api/{}/+'.format(system)
    for rule in appPaaS.url_map.iter_rules():
        if re.search(level_config[level],str(rule)):
            func = appPaaS.view_functions[rule.endpoint]
            if (isinstance(_get_api_doc(func),dict) and \
                ((_get_api_doc(func).get("ACCESS_SYSTEM_LIST") is None) or \
                (_get_api_doc(func).get("ACCESS_SYSTEM_LIST") is not None and SYSTEM in _get_api_doc(func)["ACCESS_SYSTEM_LIST"]))\
                ) or (isinstance(_get_api_doc(func),str)):
                yield str(rule), rule.endpoint, rule.methods, endpoint_api(rule.endpoint,onlydoc=True)
#}}}

#=======================================================
# API /dbDetail
# Date: 05252020
# Yishan Tsai
# 顯示api schema table
#=======================================================
# {{{ appPaaS.route('/<SYSTEM>/dbDetail', methods = ['GET'])
@appPaaS.route('/<SYSTEM>/dbDetail', methods = ['GET'])
def dbDetail(SYSTEM):
    dbDict = {"my":"MYSQL","ms":"MSSQL","myps":"POSTGRESQL"}
    dbDetail = {}
    regexStr = r'/Schema/'
    if SYSTEM in globalvar.SYSTEMLIST[globalvar.SERVERIP]:
        for x in sorted(list(get_api_map("LEVEL2",SYSTEM))):
            if re.search(regexStr,str(x[0])):
                dbDetail[dbDict[x[0].split("/")[4]]] = x[0]
            
        returndata = {"Response":"ok","dbDetail":dbDetail}
    else:
        returndata = {"Response":"system:{} is illegal".format(SYSTEM)}

    return jsonify( **returndata)
#}}}

def testthread(arg):
    #appPaaS.licCheck = os.system("/var/www/config/ezclient")
    while True:
        #appPaaS.licCheck = os.system("/var/www/config/ezclient")
        print '\n[{}]:Test Thread'.format(time.ctime())
        time.sleep(arg)


#initiate a thread to do the job, check Table:todolist's over deadline data every 24 hours
# thread.start_new_thread(testthread, (10, ))
# thread.start_new_thread(check_todolist_deadline, (60, ))


# print "%%%%%%%%%%%%%"
# def set_timer():
#     print "~~~~start set_timer~~~~~"
#     print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
#     time.sleep(30)
#     print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
#     thread.start_new_thread(check_todolist_deadline, (86400, ))
#     print "~~~~end set_timer~~~~~"
#     print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

# thread.start_new_thread(set_timer, ())

if __name__ == "__main__":
    print "10"
    #isDebug=0
    #if len(sys.argv) == 2:
    #    if sys.argv[1] == "debug":
    #        isDebug = 1

    #from werkzeug.contrib.profiler import ProfilerMiddleware
    #appPaaS.wsgi_app = ProfilerMiddleware(appPaaS.wsgi_app)
    # appPaaS.run(host='0.0.0.0',port=65000,debug=isDebug)

    #Yishan 09092020 appPaaS.run -> socketio.run
    socketio.run(appPaaS,port=3687,debug=True)


