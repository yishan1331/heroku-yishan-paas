# -*- coding: utf-8 -*-
#Department Module Description
"""
==============================================================================
created    : 03/20/2017
Last update: 02/08/2021
Developer: Wei-Chun Chang 
Lite Version 2 @Yishan08212019
API version 1.0
 
Filename: customizedHandle.py

Description: basically, all writes to the module will be opened to superuser only, for others, can only query data
    1. register a department
    2. query Department basic info.
    3. query Department members
    4. query Department sensors
Total = 6 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
#{{{
from sqlalchemy import *
from werkzeug.security import gen_salt
import subprocess #Yishan 05212020 subprocess 取代 os.popen
# import threading
#}}}

#=======================================================
# User level modules
#=======================================================
#{{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
#}}}

__all__ = ('trigger_specific_program','iot_redis_device_keys_init')

ACCESS_SYSTEM_LIST = ["IOT","CHUNZU"]

# # 建立 thread lock
# lock = threading.Lock()

#blueprint
CUSTOMIZED_API = Blueprint('CUSTOMIZED_API', __name__)

#{{{ def _list_iter(name)
def _list_iter(r,name):
    """
    自定义redis列表增量迭代
    :param name: redis中的name，即：迭代name对应的列表
    :return: yield 返回 列表元素
    """
    list_count = r.llen(name)
    for index in range(list_count):
        yield r.lindex(name, index)
#}}}

class TriggerProgramWorkerThread(threading.Thread):
    def __init__(self, pid, lock, func, cmd, SYSTEM, postHttp):
        threading.Thread.__init__(self)
        self.pid = pid
        self.func = func
        self.lock = lock
        self.cmd = cmd
        self.SYSTEM = SYSTEM
        self.postHttp = postHttp

    def run(self):
        # 取得 lock
        # self.lock.acquire()
        # print "@@@@@@@@@@@@@@@@@@@@@@@TriggerProgram@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        # print "------Lock-----",self.pid
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],self.pid
        # print "Lock acquired by pid %d" % self.pid
        # print "------threading detail------",os.getpid()
        # print threading.active_count() #用來查看目前有多少個線程
        # print threading.current_thread().name #可以用來查看你在哪一個執行緒當中

        self.func(self.cmd, self.SYSTEM, self.postHttp)

        # 釋放 lock
        # self.lock.release()
        # print "------released Lock-----",self.pid
        # print "Lock released by pid %d" % self.pid
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::],self.pid
        # print "------threading detail------",os.getpid()
        # print threading.active_count() #用來查看目前有多少個線程
        # print threading.current_thread().name #可以用來查看你在哪一個執行緒當中
        # print "@@@@@@@@@@@@@@@@@@@@@@@TriggerProgram end@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        # print 

#=======================================================
# subprocess_check_output_program
# Date: 12142020@Yishan
# Update: 05282021@Yishan
# https://www.coder.work/article/3210794
# https://stackoverflow.com/questions/31683320/suppress-stderr-within-subprocess-check-output
#=======================================================
# {{{ def subprocess_check_output_program(cmd)
def subprocess_check_output_program(cmd, SYSTEM, postHttp):
    try:
        if not postHttp:
            # print "------func------",os.getpid()
            # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
            # print cmd
            # process = subprocess.check_output(cmd,shell=False,stderr=subprocess.STDOUT)  
            # print os.getpid(),"~~~~subprocess_check_output_program~~~~",process
            # print "------------------"
            # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
            # print "======================="
            with open(os.devnull, 'w') as devnull:
                process = subprocess.check_output(cmd,shell=False,stderr=devnull)
                # with subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                # process = subprocess.Popen(cmd, shell=False, stdout=devnull, stderr=devnull)
                # result = process.stdout.readlines()
                # print "process.pid-> ",process.pid
                # print process
                # print "result-> ",result
        else:
            headers = {'Content-type': 'application/json'}
            import requests
            #05282021 Yishan 解決InsecureRequestWarning: Unverified HTTPS request is being made https://learningsky.io/python-requests-insecurerequestwarning/
            import requests.packages.urllib3
            requests.packages.urllib3.disable_warnings()
            process = requests.post("https://nginx_api:3687{}".format(cmd[0]), verify=False, data=cmd[1], headers=headers)

        return True,process,{"returncode":0}
    except subprocess.CalledProcessError as e:
        print "~~~~e~~~~"
        print e.__dict__
        return False,appPaaS.catch_exception(e,sys.exc_info(),SYSTEM),e.__dict__
    except Exception as e:
        print "~~~~Exception e~~~~"
        print e.__dict__
        return False,appPaaS.catch_exception(e,sys.exc_info(),SYSTEM),e.__dict__
# }}}

#=======================================================
# 列出/var/www/html/download/files內所有檔案
# Date: 12142020@Yishan
#=======================================================
# {{{ CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Show/DownloadFiles', methods = ['POST']),
@CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Show/DownloadFiles', methods = ['GET'])
def show_downloadfiles(selfUse=False):
    err_msg = "ok"
    FILEPATH = "/var/www/html/download/files"

    if not selfUse:
        dicRet = appPaaS.preProcessRequest(request,system="PaaS")

        uri_parameter = ["uid"]
        result, result_msg = check_uri_parameter_exist(request,uri_parameter)
        if not result:
            dicRet["Response"] = result_msg
            return jsonify( **dicRet)

    fileList = []
    try:
        fileList = [f for f in os.listdir(FILEPATH)]

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    if not selfUse:
        dicRet["FileList"] = fileList
        dicRet["Response"] = err_msg
        return jsonify( **dicRet)

    return fileList
# }}}

#=======================================================
# 提供使用者生成下載檔案列表之id & pwd (gen_salt)
# Date: 12142020@Yishan
#=======================================================
# {{{ CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Create/DownloadFiles/IdPwd', methods = ['POST']),
@CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Create/DownloadFiles/IdPwd', methods = ['POST'])
@decorator_check_content_type(request)
def create_downloadfiles_idpwd():
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    reqdataList = ConvertData().convert(json.loads(request.data))
    if not isinstance(reqdataList,list):
        dicRet["Response"] = "post data必須傳陣列"
        return jsonify( **dicRet)

    FILEPATH = "/var/www/html/download/files/"

    #檢查丟上來的data是否存在
    for i in reqdataList:
        if not isinstance(i,str):
            dicRet["Response"] = "'{}' 必須為字串".format(i)
            return jsonify( **dicRet)

        if not os.path.isfile(os.path.join(FILEPATH,i)):
            dicRet["Response"] = "{} 檔案不存在或路徑有誤".format(i)
            return jsonify( **dicRet)

    ID = gen_salt(24)
    PWD = gen_salt(48)

    recList = []
    try:
        dbRedis,_,result= appPaaS.getDbSessionType(system="PaaS",dbName=15,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        redis_key = ID+"_"+PWD

        #設立基準點過期時間為後天的00:30
        rederence_extime = int(time.mktime(time.strptime(str(date.today() + timedelta(days=2))+" 00:30:00", '%Y-%m-%d %H:%M:%S')))
        redishash_already_set_expireat = False

        #基準點若存在需判斷此次建立是否需增加基準點期限秒數(小於兩天：172800s，直接以今天為基準多加兩天)
        if dbRedis.exists("rederence_point"):
            if dbRedis.ttl("rederence_point") < 172800:
                dbRedis.expireat("rederence_point",rederence_extime)
                redishash_already_set_expireat = True
            # if dbRedis.hexists("rederence_point",redis_key): #正常情況下不可能會有重複ID&PWD，但若重複了，while重新建立一次
            #     status = True
            #     while status:
            #         redis_key = str(gen_salt(24))+"_"+str(gen_salt(48))
            #         status = dbRedis.hexists("rederence_point",redis_key)
            # else:
            #     dbRedis.hmset("rederence_point",{redis_key:json.dumps(reqdataList)})
        #不存在，建立基準點value為檔案列表，期限為兩天後 (hash)
        # else:
        #     dbRedis.hmset("rederence_point",{redis_key:json.dumps(reqdataList)})
        #     dbRedis.expireat("rederence_point",rederence_extime)

        # rederence_point : {"filename":[redis_key,.....]}

        #建立ID_PWD:reqdataList(list)
        if dbRedis.llen(redis_key) != 0:
            status = True
            while status:
                redis_key = str(gen_salt(24))+"_"+str(gen_salt(48))
                if dbRedis.llen(redis_key) == 0: status = False

        for i in reqdataList:
            dbRedis.lpush(redis_key, i)
            if dbRedis.hexists("rederence_point",i):
                this_list = json.loads(dbRedis.hget("rederence_point", i))
                this_list.append(redis_key)
                dbRedis.hmset("rederence_point",{i:json.dumps(this_list)})
            else:
                dbRedis.hmset("rederence_point",{i:json.dumps([redis_key])})
        dbRedis.expire(redis_key,86400)
        if not redishash_already_set_expireat:
            dbRedis.expireat("rederence_point",rederence_extime)

        dicRet["ID"] = ID
        dicRet["PWD"] = PWD
        dicRet["DownloadList"] = reqdataList
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
#}}}

#=======================================================
# 檢驗欲使用下載檔案功能之id & pwd合法性
# Date: 12142020@Yishan
#=======================================================
# {{{ CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Check/DownloadFiles/IdPwd', methods = ['POST']),
@CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Check/DownloadFiles/IdPwd', methods = ['POST'])
@decorator_check_content_type(request)
def check_downloadfiles_idpwd():
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)
    
    reqdataDict = ConvertData().convert(json.loads(request.data))

    post_parameter = ["Id","Pwd"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)
    
    Id = reqdataDict.get("Id").encode("utf8").strip()
    Pwd = reqdataDict.get("Pwd").encode("utf8").strip()

    recList = []
    try:
        dbRedis,_,result= appPaaS.getDbSessionType(system="PaaS",dbName=15,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        redis_key = Id+"_"+Pwd

        if not dbRedis.exists(redis_key):
            dicRet["Response"] = "帳號或密碼錯誤"
            return jsonify( **dicRet)
        
        download_List = []
        download_List = [item for item in _list_iter(dbRedis,redis_key)]

        dicRet["DownloadList"] = download_List
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
#}}}

#=======================================================
# 檢驗欲使用下載檔案的有效期限若超過則刪除
# Date: 12142020@Yishan
#=======================================================
# {{{ CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Check/Delete/DownloadFiles/Deadline/<CRONTAB>', methods = ['GET']),
@CUSTOMIZED_API.route('/api/PaaS/1.0/Customized/Check/Delete/DownloadFiles/Deadline/<CRONTAB>', methods = ['GET'])
def check_delete_downloadfiles_deadline(CRONTAB="DAY"):
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    FILEPATH = "/var/www/html/download/files/"

    try:
        dbRedis,_,result= appPaaS.getDbSessionType(system="PaaS",dbName=15,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        #此為每天的crontab要做的排程(00:45)
        #抓出redis hash : rederence_point內的檔案(key):[id&pwd(value)]，一一查看value是否exists in redis，不存在代表id&pwd已過期，即可移除此value；
        #when loop run over,len=0 => 此檔案無人要下載了，直接刪除 , else update new value
        if CRONTAB == "DAY":
            for key,value in dbRedis.hgetall("rederence_point").items():
                new_value = []
                for i in json.loads(value):
                    if dbRedis.exists(i):
                        new_value.append(i)
                else:
                    #新的value list沒有資料，將此檔案刪除，rederence_point hash key del
                    if not new_value:
                        if os.path.isfile(os.path.join(FILEPATH,key)): os.remove(os.path.join(FILEPATH,key))
                        dbRedis.hdel("rederence_point", key)
                    else:
                        dbRedis.hmset("rederence_point",{key:json.dumps(new_value)})
        #此為每個禮拜天的crontab要做的排程(Sunday 01:00)
        #先抓出所有檔案，再去redis看這些檔案(key)在hash : rederence_point是否存在，存在代表有id&pwd需要下載，不存在表示無人下載即可刪除
        elif CRONTAB == "WEEK":
            fileList = show_downloadfiles(True)
            for i in fileList:
                if i not in dbRedis.hkeys("rederence_point") and os.path.isfile(os.path.join(FILEPATH,i)): os.remove(os.path.join(FILEPATH,i))

        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
#}}}

#=======================================================
# 提供api觸發指定程式
# Date: 12142020@Yishan
# Update: 05272021@Yishan
#=======================================================
# {{{ CUSTOMIZED_API.route('/api/<SYSTEM>/1.0/Customized/Trigger/Specific/Program', methods = ['GET']),
@CUSTOMIZED_API.route('/api/<SYSTEM>/1.0/Customized/Trigger/Specific/Program', methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def trigger_specific_program(SYSTEM,selfUse=False,useThread=False,languages=None,programName=None,programData=None,postHttp=False,Temp=False):
    #{{{APIINFO
    '''
    {
        "API_application":"提供觸發指定程式",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "languages":{"type":"String","requirement":"required","directions":"欲觸發的程式語言類型","example":"php"},
                "programName":{"type":"String","requirement":"required","directions":"欲觸發的程式路徑加檔名","example":"/var/www/html/test.php"},
                "programData":{"type":"Unlimited","requirement":"optional","directions":"欲丟入觸發程式的參數資料","example":"test"}
            },
            "precautions":{
                "注意事項1":"languages目前只接受php語言",
                "注意事項2":"programName程式路徑必須存在"
            },
            "example":[
                {
                    "languages":"php",
                    "programName":"test.php",
                    "programData":"123"
                }
            ]
        },
        "API_message_parameters":{"GetProgramResponse":"Unlimited+取得觸發程式回傳的值"},
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/IOT/1.0/Customized/Trigger/Specific/Program",
            "OperationTime": "3.020",
            "BytesTransferred": 223,
            "System": "IOT",
            "GetProgramResponse": "test"
        }
    }
    '''
    #}}}
    err_msg = "error"

    languages_config = {
        "php":"/usr/bin/php",
        "c":""
    }
    default_dir = {
        "php":"/var/www/html",
        "c":""
    }

    if not selfUse:
        dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

        uri_parameter = ["uid"]
        result, result_msg = check_uri_parameter_exist(request,uri_parameter)
        if not result:
            dicRet["Response"] = result_msg
            return jsonify( **dicRet)

        if not VerifyDataStrLawyer(request.data).verify_json():
            dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
            return jsonify( **dicRet)

        reqdataDict = json.loads(request.data)
        if isinstance(reqdataDict,type(u"")):
            reqdataDict = json.loads(reqdataDict)

        post_parameter = ["languages","programName","programData"]
        if not check_post_parameter_exist(reqdataDict,post_parameter):
            dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
            return jsonify( **dicRet)
    
        languages = reqdataDict.get("languages")
        programName = reqdataDict.get("programName")
        programData = reqdataDict.get("programData")

        if reqdataDict.get("waitResponse") is not None and re.search(r'[Y|y][E|e][S|s]',reqdataDict.get("waitResponse")):
            useThread = True
    
        # print "~~~~useThread~~~~"
        # print useThread
        # print "~~~~languages~~~~"
        # print languages
        if languages not in languages_config.keys():
            dicRet["Response"] = "Currently only php and C programs can be executed"
            return jsonify( **dicRet)
        
        # print "~~~~programName~~~~"
        # print programName
        # print "~~~~programData~~~~"
        # print programData
        # print type(programData)
        if isinstance(programData,dict): programData = json.dumps(programData)
        # print "~~~~programData~~~~"
        # print programData

        if not os.path.isfile(programName):
            dicRet["Response"] = "{} 檔案不存在或路徑有誤".format(programName)
            return jsonify( **dicRet)
    else:
        if not postHttp and default_dir[languages] != "":
            programName = default_dir[languages]+programName

    cmd = [programName]
    if not postHttp:
        if isinstance(languages_config[languages],list):
            cmd += languages_config[languages]
        else:
            cmd.insert(0,languages_config[languages])
    if programData: cmd.append(programData)

    try:
        if useThread:
            # print "~~~~~trigger start~~~~~~"
            # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

            if Temp:
                from celeryApp.celeryTasks import celery_trigger_specific_program
                celery_trigger_specific_program.apply_async(args=(cmd,SYSTEM), routing_key='high', queue="H-queue1")
            else:
                worker = TriggerProgramWorkerThread(os.getpid(), lock, subprocess_check_output_program, cmd, SYSTEM, postHttp)
                worker.start()

            # print "~~~~~trigger over~~~~~~"
            # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
            err_msg = "ok"
            return
        else:
            if languages == "c": cmd.pop(0)
            # print "!!!!!!!!!!!!!!!!!"
            dicRet["StartProgramTime"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            process = subprocess_check_output_program(ConvertData().convert(cmd), SYSTEM, postHttp)
            # print "~~~~process~~~~"
            # print process
            # print "~~~~type process~~~~"
            # print type(process)
            dicRet["EndProgramTime"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # print "!!!!!!!!!!!!!!!!!"
            if process[0]:
                dicRet["GetProgramResponse"] = {"output":process[1],"returncode":0}
                err_msg = "ok"
            else:
                # print process[2]
                del process[2]["cmd"]
                dicRet["GetProgramResponse"] = process[2]
                err_msg = "error"

    except Exception as e:
        print "~~~Exception~~~"
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        print e
        print sys.exc_info()
    finally:
        if not selfUse:
            # dicRet["THISTIME"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
            dicRet["Response"] = err_msg
            return jsonify(**dicRet)
#}}}

#=======================================================
# Definition: Only For IoT-chunzu 初始化IoT所需的redis mes_device_status keys(hash) from mysql table:
# Date: 01122021@Yishan
#=======================================================
# {{{ CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Init/Redis/Device/Keys', methods = ['GET']),
@CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Init/Redis/Device/Keys', methods = ['GET'])
@decorator_check_legal_system(SYSTEM="CHUNZU")
def iot_redis_device_keys_init(selfUse=False):
    """
    {
        "API_application":"初始化IoT所需的redis mes_device_status keys(hash) from mysql table",
        "API_parameters":{"uid":"使用者帳號"},
        "API_example":{
            "Response": "ok",
            "APIS": "GET /api/CHUNZU/1.0/Customized/Init/Redis/Device/Keys",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "System": "CHUNZU"
        }
    } 
    """
    if not selfUse:
        dicRet = appPaaS.preProcessRequest(request,system="CHUNZU")
        
        uri_parameter = ["uid"]
        result, result_msg = check_uri_parameter_exist(request,uri_parameter)
        if not result:
            dicRet["Response"] = result_msg
            return jsonify( **dicRet)

    all_device = {}
    all_device_keys = []
    err_msg = "error"
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="CHUNZU")
        if DbSession is None:
            return

        sess = DbSession()
        
        queryTable = Table("preload" , metadata, autoload=True)

        for row in sess.query(queryTable).all():
            drow = AdjustDataFormat().format(row._asdict())
            # all_device[drow["main_key"]+"_"+drow["combine_key"]] = json.loads(drow["combine_list"])
            all_device[drow["combine_key"]] = [drow["main_key"],json.loads(drow["combine_list"])]
            all_device_keys.append(drow["main_key"]+"_"+drow["combine_key"])
        
        err_msg = "ok" #done successfully
        # http://stackoverflow.com/questions/4112337/regular-expressions-in-sqlalchemy-queries

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"CHUNZU")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()
    
        if err_msg != "ok":
            if selfUse: return 
            if not selfUse:
                dicRet["Response"] = err_msg
                return jsonify( **dicRet)

    err_msg = "error"
    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index("CHUNZU")
        dbRedis,_,_ = appPaaS.getDbSessionType(system="CHUNZU",dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            return
        
        trigger_php = False
        trigger_data = []
        print "------init_redis_key------"
        for key,value in all_device.items():
            _key = value[0]+"_"+key
            _value = value[1]
            #若key不存在，直接建立
            if not dbRedis.exists(_key):
                print "建立不存在的key->",_key
                dbRedis.hmset(_key, _value)
                trigger_php = True
                trigger_data.append({"combine_key":key})
            #若存在，比較_value物件的key，抓取不重複的建立
            else:
                #差集(舊的多的key，需刪除)
                fields_need_del = list(set(dbRedis.hkeys(_key)).difference(_value.keys()))
                if fields_need_del: print "刪除舊的多的key->",_key,"fields->",fields_need_del
                if fields_need_del: dbRedis.hdel(_key, *fields_need_del)
                #差集(新的多的key，需新增)
                fields_need_add = list(set(_value.keys()).difference(dbRedis.hkeys(_key)))
                if fields_need_add:
                    for value_key,value_value in _value.items():
                        if value_key in fields_need_add:
                            print "新增新的key->",_key,"fields/key->",value_key,"fields/value->",value_value
                            dbRedis.hset(_key, value_key, value_value)
                            trigger_php = True
                            trigger_data.append({"combine_key":key})
        
        #檢查mes_device_status_* keys是否需刪除(多的需刪除)
        keys_need_del = list(set(dbRedis.keys("mes_device_status_*")).difference(all_device_keys))
        if keys_need_del: print "刪除多的mes_device_status_* keys->",keys_need_del
        if keys_need_del: dbRedis.delete(*keys_need_del)
        err_msg = "ok"

        if trigger_php:
            programDir = SYSTEM
            #確定PaaS是否為container
            if globalvar.ISCONTAINER: programDir = globalvar.CONTAINER_API_HTML
            #觸發指定程式
            trigger_settime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
            trigger_obj = {"data":trigger_data,"upload_at":trigger_settime,"ip":request.host.split(":")[0]}
            trigger_specific_program("CHUNZU", selfUse=True, useThread=True, languages="php", programName="/{}/mes_modules/mes_timer/device_basic.php".format(programDir), programData=json.dumps(ConvertData().convert(trigger_obj)), postHttp=True)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e, sys.exc_info(), "CHUNZU")
    
    finally:
        if not selfUse:
            dicRet["Response"] = err_msg
            return jsonify( **dicRet)
#}}}

#=======================================================
# API: /api/CHUNZU/1.0/Customized/Sensor/Create/Default/Table
# Definition: 提供使用者註冊預設機台感測資料表 only for IOT-chunzu
# Date: 01122021@Yishan
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/CHUNZU/1.0/Customized/Sensor/Create/Default/Table', methods = ['POST']), 
@CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Sensor/Create/Default/Table',  methods = ['POST'])
@decorator_check_legal_system(SYSTEM="CHUNZU")
def create_default_sensor_table(serialID=None, devID=None, production_time=None, selfUse=False):
    #{{{APIINFO
    """
    {
        "API_application":"提供使用者註冊預設機台感測資料表",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "sensor_raw_table":{"type":"Array","requirement":"required","directions":"感測器資料表名稱列表","example":["work_code_use","mould_series_no_use","mould_series_no_abn","material_batch_no_use","material_batch_no_abn"]}
            },
            "precautions": {
                "注意事項1":"'sensor_raw_table'內的感測器資料表名稱必須存在"
            },
            "example":[
                {
                    "sensor_raw_table":["work_code_use","mould_series_no_use","mould_series_no_abn","material_batch_no_use","material_batch_no_abn"]
                }
            ]
        },
        "API_message_parameters":{
            "dbNames":"object",
            "DB":"string"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/CHUNZU/1.0/Customized/Sensor/Create/Default/Table",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MYSQL+POSTGRES",
            "System": "CHUNZU",
            "dbNames": {"work_code_use":"","mould_series_no_use":"","mould_series_no_abn":"","material_batch_no_use":"","material_batch_no_abn":""}
        }
    } 
    """
    #}}}
    err_msg = "error"

    try:
        if not selfUse:
            dicRet = appPaaS.preProcessRequest(request,system="CHUNZU")

            uri_parameter = ["uid"]
            result, result_msg = check_uri_parameter_exist(request,uri_parameter)
            if not result:
                dicRet["Response"] = result_msg
                return jsonify( **dicRet)
            
            if not VerifyDataStrLawyer(request.data).verify_json():
                dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
                return jsonify( **dicRet)

            reqdataDict = json.loads(request.data)
            if isinstance(reqdataDict,type(u"")):
                reqdataDict = json.loads(reqdataDict)

            #先將unicode data change to str
            reqdataDict = AdjustDataFormat().format(reqdataDict)

            # post_parameter = ["serialID","devID","production_time"]
            post_parameter = ["serialID","devID","production_time"]
            if not check_post_parameter_exist(reqdataDict,post_parameter):
                dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
                return jsonify( **dicRet)

            serialID = reqdataDict.get("serialID")
            devID = reqdataDict.get("devID")
            production_time = reqdataDict.get("production_time")

        #create 5 default device table
        from app.dbModel.iot import create_default_device_table
        print "=============@@@@@@@@@@@@@@@=============="
        status,err_msg = create_default_device_table(appPaaS,serialID)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"CHUNZU")

    if not selfUse:
        dicRet["Response"] = err_msg
        dicRet["DB"] = "MYSQL+POSTGRES"
        return jsonify(**dicRet)
    return err_msg
# }}}

#=======================================================
# API: /api/CHUNZU/1.0/Customized/Customer/Macro
# Date: 05142021 Yishan
# Definition: 刪除客戶資料一系列連動動作(customer,user,device_basic,preload,update redis) only for IOT-chunzu
#=======================================================
#{{{ CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Customer/Macro', methods = ['DELETE']), 
@CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Customer/Macro',  methods = ['DELETE'])
@decorator_check_legal_system(SYSTEM="CHUNZU")
def chunzu_delete_customer_macro():
    #{{{APIINFO
    """
    {
        "API_application":"刪除客戶資料一系列連動動作(customer,user,device_basic,preload,update redis)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "cus_id":{"type":"Integer","requirement":"required","directions":"欲刪除的客戶編號","example":1}
            },
            "example":[
                {
                    "cus_id":1
                }
            ]
        },
        "API_message_parameters":{
            "DB":"string",
            "Detail":"JSON"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "DELETE /api/CHUNZU/1.0/Customized/Customer/Macro",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MIXING",
            "System": "CHUNZU",
            "Detail":{}
        }
    } 
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system="CHUNZU")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    #先將unicode data change to str
    reqdataDict = AdjustDataFormat().format(reqdataDict)

    post_parameter = {"cus_id":[int]}
    if not check_post_parameter_exist_format(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    cus_id = reqdataDict.get("cus_id")
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="CHUNZU")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        update_value = {
            "delete_enable":"Y",
            "delete_at":datetime.now().strftime('%Y-%m-%d %H:%M:%S')[::]
        }
        #step1:註記customer delete_enable,delete_at
        Customer = Table("customer" , metadata, autoload=True)
        queryCust = sess.query(Customer).\
                    filter(getattr(Customer.c,"id") == func.binary(cus_id)).\
                    all()

        if len(queryCust) == 0:
            dicRet["Response"] = "Error: customer id : '{}' existed".format(cus_id)
            return jsonify( **dicRet)

        sess.execute(Customer.update().where(getattr(Customer.c,"id") == func.binary(cus_id))\
            .values(update_value))

        #step2:註記user delete_enable,delete_at
        User = Table("user" , metadata, autoload=True)
        sess.execute(User.update().where(getattr(User.c,"cus_id") == func.binary(cus_id))\
            .values(update_value))

        #step3:抓取預註記的機台編號列表，註記device_basic delete_enable,delete_at
        DeviceBasic = Table("device_basic" , metadata, autoload=True)
        device_list = []
        for row in sess.query(getattr(DeviceBasic.c,"id")).filter(getattr(DeviceBasic.c,"cus_id") == func.binary(cus_id)).all():
            drow = AdjustDataFormat().format(row._asdict())
            device_list.append(drow["id"])
        sess.execute(DeviceBasic.update().where(getattr(DeviceBasic.c,"cus_id") == func.binary(cus_id))\
            .values(update_value))

        #step4:以抓到的device_list去刪除preload
        Preload = Table("preload" , metadata, autoload=True)
        for i in device_list:
            print type(cus_id)
            print type(i)
            print "~~~cus_id+'_'+i~~~"
            print str(cus_id)+"_"+str(i)
            sess.execute(Preload.delete().where(getattr(Preload.c,"combine_key") == func.binary(str(cus_id)+"_"+str(i))))
        sess.commit()

        #step5:更新redis
        iot_redis_device_keys_init("CHUNZU",selfUse=True)
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"CHUNZU")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MIXING"
    return jsonify(**dicRet)
# }}}

#=======================================================
# API: /api/CHUNZU/1.0/Customized/Device/Macro
# Date: 05142021 Yishan
# Definition: 新增客戶機台一系列連動動作(device_basic,machine_sensor_list,machine_light_list,preload,update redis,postgres default tables) only for IOT-chunzu
#=======================================================
#{{{ CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Device/Macro', methods = ['POST']), 
@CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Device/Macro',  methods = ['POST'])
@decorator_check_legal_system(SYSTEM="CHUNZU")
def chunzu_register_device_macro():
    #{{{APIINFO
    """
    {
        "API_application":"新增客戶機台一系列連動動作(device_basic,machine_sensor_list,machine_light_list,preload,update redis,postgres default tables)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "cus_id":{"type":"Integer","requirement":"required","directions":"欲刪除的客戶編號","example":1}
            },
            "example":[
                {
                    "cus_id":1
                }
            ]
        },
        "API_message_parameters":{
            "DB":"string",
            "Detail":"JSON"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/CHUNZU/1.0/Customized/Device/Macro",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MIXING",
            "System": "CHUNZU",
            "Detail":{}
        }
    } 
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system="CHUNZU")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    #先將unicode data change to str
    reqdataDict = AdjustDataFormat().format(reqdataDict)

    post_parameter = {
        "device_basic":[dict],
        "machine_sensor_list":[list],
        "machine_light_list":[list],
        "preload":[dict]
    }
    if not check_post_parameter_exist_format(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    device_basic = reqdataDict.get("device_basic")
    machine_sensor_list = reqdataDict.get("machine_sensor_list")
    machine_light_list = reqdataDict.get("machine_light_list")
    preload = reqdataDict.get("preload")
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="CHUNZU")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #step1:檢查device_basic此次新增的機台cus_id&device_name不重複
        DeviceBasic = Table("device_basic" , metadata, autoload=True)
        queryDeviceBasic = sess.query(DeviceBasic).\
                    filter(getattr(DeviceBasic.c,"cus_id") == func.binary(device_basic["cus_id"]),\
                        getattr(DeviceBasic.c,"device_name") == func.binary(device_basic["device_name"])).\
                    all()

        if len(queryDeviceBasic) != 0:
            dicRet["Response"] = "機台編號已存在"
            return jsonify( **dicRet)
        
        #step2:新增device_basic
        sess.execute(DeviceBasic.insert().values(device_basic))
        sess.commit()
        
        device_id = None
        for row in sess.query(getattr(DeviceBasic.c,"id")).filter(getattr(DeviceBasic.c,"cus_id") == func.binary(device_basic["cus_id"]),\
            getattr(DeviceBasic.c,"device_name") == func.binary(device_basic["device_name"])).all():
            drow = AdjustDataFormat().format(row._asdict())
            device_id = drow["id"]
        print "~~~device_id~~~"
        print device_id

        #step3:新增machine_sensor_list
        #先將新增的device_id逐一加入machine_sensor_list
        MachineSensorList = Table("machine_sensor_list" , metadata, autoload=True)
        for i in machine_sensor_list:
            i["device_id"] = device_id
        sess.execute(MachineSensorList.insert().values(machine_sensor_list))
        sess.commit()

        #step4:新增machine_light_list
        #先將新增的device_id逐一加入machine_light_list
        MachineLightList = Table("machine_light_list" , metadata, autoload=True)
        for i in machine_light_list:
            i["device_id"] = device_id
        sess.execute(MachineLightList.insert().values(machine_light_list))
        sess.commit()

        #step5:新增preload
        preload["main_key"] = "mes_device_status"
        preload["combine_key"] = str(device_basic["cus_id"])+"_"+str(device_id) #客戶編號_機台編號
        preload["combine_list"]["device_id"] = device_id
        preload["combine_list"] = json.dumps(preload["combine_list"])
        Preload = Table("preload" , metadata, autoload=True)
        sess.execute(Preload.insert().values(preload))
        sess.commit()

        #step6:更新redis
        iot_redis_device_keys_init(selfUse=True)

        #step7:建立postgres預設感測資料表
        err_msg = create_default_sensor_table(serialID=str(device_basic["cus_id"])+"_"+str(device_id), selfUse=True)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"CHUNZU")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MIXING"
    return jsonify(**dicRet)
# }}}

#=======================================================
# API: /api/CHUNZU/1.0/Customized/Device/Macro
# Date: 05192021 Yishan
# Definition: 修改客戶機台一系列連動動作(device_basic,machine_sensor_list,machine_light_list) only for IOT-chunzu
#=======================================================
#{{{ CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Device/Macro', methods = ['PATCH']), 
@CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/Device/Macro',  methods = ['PATCH'])
@decorator_check_legal_system(SYSTEM="CHUNZU")
def chunzu_update_device_macro():
    #{{{APIINFO
    """
    {
        "API_application":"修改客戶機台一系列連動動作(device_basic,machine_sensor_list,machine_light_list)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "cus_id":{"type":"Integer","requirement":"required","directions":"欲刪除的客戶編號","example":1}
            },
            "example":[
                {
                    "cus_id":1
                }
            ]
        },
        "API_message_parameters":{
            "DB":"string",
            "Detail":"JSON"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/CHUNZU/1.0/Customized/Device/Macro",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MIXING",
            "System": "CHUNZU",
            "Detail":{}
        }
    } 
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system="CHUNZU")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    #先將unicode data change to str
    reqdataDict = AdjustDataFormat().format(reqdataDict)

    post_parameter = {
        "check_devID":[str,unicode],
        "device_basic":[dict],
        "machine_sensor_list":[list],
        "machine_light_list":[list]
    }
    if not check_post_parameter_exist_format(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    check_devID = reqdataDict.get("check_devID")
    device_basic = reqdataDict.get("device_basic")
    machine_sensor_list = reqdataDict.get("machine_sensor_list")
    machine_light_list = reqdataDict.get("machine_light_list")
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="CHUNZU")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        DeviceBasic = Table("device_basic" , metadata, autoload=True)
        if check_devID == "yes":
            #step1:檢查device_basic此次修改的機台cus_id&device_name不重複
            queryDeviceBasic = sess.query(DeviceBasic).\
                        filter(getattr(DeviceBasic.c,"cus_id") == func.binary(device_basic["cus_id"]),\
                            getattr(DeviceBasic.c,"device_name") == func.binary(device_basic["device_name"])).\
                        all()

            if len(queryDeviceBasic) != 0:
                dicRet["Response"] = "機台編號已存在"
                return jsonify( **dicRet)
        
        #step2:修改device_basic
        sess.execute(DeviceBasic.update().where(getattr(DeviceBasic.c,"id") == func.binary(device_basic["id"]))\
                            .values(device_basic))
        
        #step3:先刪除machine_sensor_list舊的，再新增
        MachineSensorList = Table("machine_sensor_list" , metadata, autoload=True)
        sess.execute(MachineSensorList.delete().where(getattr(MachineSensorList.c,"device_id") == func.binary(device_basic["id"])))

        #新增machine_light_list
        sess.execute(MachineSensorList.insert().values(machine_sensor_list))

        #step4:先刪除machine_light_list舊的，再新增
        MachineLightList = Table("machine_light_list" , metadata, autoload=True)
        sess.execute(MachineLightList.delete().where(getattr(MachineLightList.c,"device_id") == func.binary(device_basic["id"])))

        #新增machine_light_list
        sess.execute(MachineLightList.insert().values(machine_light_list))
        sess.commit()

        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"CHUNZU")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MIXING"
    return jsonify(**dicRet)
# }}}

#=======================================================
# API: /api/CHUNZU/1.0/Customized/DeviceType/Macro
# Date: 05192021 Yishan
# Definition: 修改機台型號資料一系列連動動作(model_sensor_list,model_light_list) only for IOT-chunzu
#=======================================================
#{{{ CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/DeviceType/Macro', methods = ['PATCH']), 
@CUSTOMIZED_API.route('/api/CHUNZU/1.0/Customized/DeviceType/Macro',  methods = ['PATCH'])
@decorator_check_legal_system(SYSTEM="CHUNZU")
def chunzu_update_devicetype_macro():
    #{{{APIINFO
    """
    {
        "API_application":"修改機台型號資料一系列連動動作(model_sensor_list,model_light_list) o",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "cus_id":{"type":"Integer","requirement":"required","directions":"欲刪除的客戶編號","example":1}
            },
            "example":[
                {
                    "cus_id":1
                }
            ]
        },
        "API_message_parameters":{
            "DB":"string",
            "Detail":"JSON"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/CHUNZU/1.0/Customized/Device/Macro",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MIXING",
            "System": "CHUNZU",
            "Detail":{}
        }
    } 
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system="CHUNZU")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    #先將unicode data change to str
    reqdataDict = AdjustDataFormat().format(reqdataDict)

    post_parameter = {
        "model_sensor_list":[list],
        "model_light_list":[list]
    }
    if not check_post_parameter_exist_format(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    model_sensor_list = reqdataDict.get("model_sensor_list")
    model_light_list = reqdataDict.get("model_light_list")
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="CHUNZU")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #step1:更新model_sensor_list
        ModelSensorList = Table("model_sensor_list" , metadata, autoload=True)
        for i in model_sensor_list:
            sess.execute(ModelSensorList.update().where(getattr(ModelSensorList.c,"id") == i["id"]).values(i))

        #step2:更新model_light_list
        ModelLightList = Table("model_light_list" , metadata, autoload=True)
        for i in model_light_list:
            sess.execute(ModelLightList.update().where(getattr(ModelLightList.c,"id") == i["id"]).values(i))

        sess.commit()
        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"CHUNZU")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MIXING"
    return jsonify(**dicRet)
# }}}