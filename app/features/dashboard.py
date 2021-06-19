# coding=utf-8 
#Description
"""
==============================================================================
created    : 11/13/2020

Last update: 03/31/2021

Developer: Yishan Tsai 

Lite Version 1 @Yishan11132020

Filename: dashboard.py

Description: dashboard modules

Total = 7 APIs
==============================================================================
"""
from sqlalchemy import *

from app import *
#Yishan@05212020 added for common modules
from app.modules import *
print "=====dashboard.py======"
print globalvar.LOGFILELIST

#blueprint
DASHBOARD_API = Blueprint('DASHBOARD_API', __name__)

def _file_content_list_iter(file):
    """
    將檔案內容列表增量迭代
    :param file: 路徑+檔名
    :return: yield 返回 列表元素
    """
    # https://blog.gtwang.org/programming/python-data-compression-archiving-gzip-bz2-zip-tar/
    # https://blog.csdn.net/zhangchilei/article/details/46313315
    import gzip
    print "~~~file~~~"
    print file
    try:
        with gzip.open(file, 'rb') as f:
            for line in f:
                yield line
    except IOError:
        try:
            with open(file, "r") as r:
                for line in r:
                    yield line
        except Exception as e:
            print "~~~e~~~"
            print e

#=======================================================
# 抓取PaaS內有記錄的log檔列表(uwsgi、api)
# Date: 01xx2021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/ps/ApiCountedTable/<SYSTEM>', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/sysps/LogType/<SYSTEM>', methods=['GET'])
def get_logtype(SYSTEM):
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    print '~~~~request.args.get("GetLogFilesList")~~~~'
    print request.args.get("GetLogFilesList")
    GetLogFilesList = False
    if request.args.get("GetLogFilesList"):
        print re.search(r'[Y|y][E|e][S|s]',request.args.get("GetLogFilesList"))
        if re.search(r'[Y|y][E|e][S|s]',request.args.get("GetLogFilesList")):
            GetLogFilesList = True
    
    print "~~~~GetLogFilesList~~~~"
    print GetLogFilesList

    #檢查此SYSTEM api log資料表是否已存在
    File = []
    FileList = {}
    try:
        for key,value in globalvar.LOGFILELIST.items():
            FileList[key] = []
            if key == "PaaS_LOG":
                DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(dbName=globalvar.PAAS_DASHBOARD_DBNAME["POSTGRES"],forRawData="postgres",system=SYSTEM)
                if DbSessionRaw is None:
                    #表示連接資料庫有問題
                    dicRet["Response"] = engineRaw
                    return jsonify( **dicRet)
                
                metaRaw.reflect()
                tableList = ConvertData().convert(metaRaw.tables.keys())
                print "~~~tableList~~~"
                print tableList
                for i in tableList:
                    if re.search(r'^'+SYSTEM.lower(),i):
                        print "~~~i~~~"
                        print i
                        FileList[key].append(i)
                else:
                    File.append(key)

                # if retrieve_table_exist(metaRaw,SYSTEM.lower()+"_paas_log_"+time.strftime("%Y%m", time.localtime()),SYSTEM): File.append(key)
            else:
                File.append(key)
                if GetLogFilesList:
                    FileList[key] = show_uWSGU_logfiles(selfUse=True)

        err_msg = "ok"
        dicRet["FileType"] = File
        dicRet["FileList"] = FileList

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    return jsonify(**dicRet)
#}}}

#=======================================================
# 抓取所有api計次表列表
# Date: 01xx2021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/ps/ApiCountedTable/<SYSTEM>', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/ps/ApiCountedTable/<SYSTEM>', methods=['GET'])
def get_apicountedtable(SYSTEM):
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")
    if SYSTEM not in globalvar.SYSTEMLIST[globalvar.SERVERIP]:
        dicRet["Response"] = "system:{} has no privillege to use this API".format(SYSTEM)
        return jsonify( **dicRet)

    dbName = "sapidoapicount_"+SYSTEM.lower()
    try:
        # if not retrieve_database_exist(SYSTEM, dbName=dbName, forRawData="postgres"):
        #     dicRet["Response"] = "此系統:{} 尚未有api counted table".format(SYSTEM)
        #     return jsonify( **dicRet)

        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(dbName=dbName,forRawData="postgres",system="PaaS")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)

        metaRaw.reflect()
        tableList = ConvertData().convert(metaRaw.tables.keys())
        dicRet["ApiCountedTable"] = tableList
        err_msg = 'ok'
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    return jsonify(**dicRet)
#}}}

#=======================================================
# 抓取指定api計次表的資料
# Date: 01xx2021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/ps/ApiCountedTableData/<TableName>', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/ps/ApiCountedTableData/<TableName>', methods=['GET'])
def get_apicountedtabledata(TableName):
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")

    SYSTEM = TableName.split("_")[1]
    if SYSTEM not in globalvar.SYSTEMLIST[globalvar.SERVERIP]:
        dicRet["Response"] = "system:{} has no privillege to use this API".format(SYSTEM)
        return jsonify( **dicRet)

    dbName = "sapidoapicount_"+SYSTEM.lower()
    recList = []
    try:
        # if not retrieve_database_exist(SYSTEM, dbName=dbName, forRawData="postgres"):
        #     dicRet["Response"] = "此系統:{} 尚未有api counted table".format(SYSTEM)
        #     return jsonify( **dicRet)

        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(dbName=dbName, forRawData="postgres", system="PaaS")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()
        
        TableName = TableName.lower()
        #check table existed or not
        if not retrieve_table_exist(metaRaw,TableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(TableName)
            return jsonify( **dicRet)

        #Yishan 10172019 改變方式
        query_table = Table(TableName , metaRaw, autoload=True)
        for row in sessRaw.query(query_table):
            drow = AdjustDataFormat().format(row._asdict())
            recList.append(drow)

        dicRet['ApiCountedTableData'] = recList
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    return jsonify(**dicRet)
#}}}

#=======================================================
# 列出/var/log/uwsgi內有關spdpaas_uwsgi.log檔案
# Date: 01272021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/sys/Show/uWSGILogFiles', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/sys/Show/uWSGILogFiles', methods = ['GET'])
def show_uWSGU_logfiles(selfUse=False):
    err_msg = "ok"
    FILEPATH = "/var/log/uwsgi"

    if not selfUse:
        dicRet = appPaaS.preProcessRequest(request,system="PaaS")

        uri_parameter = ["uid"]
        result, result_msg = check_uri_parameter_exist(request,uri_parameter)
        if not result:
            dicRet["Response"] = result_msg
            return jsonify( **dicRet)

    fileList = []
    try:
        for f in os.listdir(FILEPATH):
            if re.search(r".uwsgi\.log\-\d*($|.gz$)", f):
                # print "@@ ",f
                # print os.path.getsize(os.path.join(FILEPATH,f))
                fileList.append(f)
            # else:
            #     print "## ",f

        # fileList = [f for f in os.listdir(FILEPATH)]

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    if not selfUse:
        dicRet["FileList"] = fileList
        dicRet["Response"] = err_msg
        return jsonify( **dicRet)

    return fileList
# }}}

#=======================================================
# 讀取/var/log/uwsgi內指定spdpaas_uwsgi.log檔案或指定postgresql log資料表內容
# Date: 01282021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/sysps/LogContent/<LogName>', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/sysps/LogContent/<LogName>', methods = ['GET'])
def unzip_uWSGU_logfiles(LogName,selfUse=False):
    err_msg = "ok"
    FILEPATH = "/var/log/uwsgi/"

    if not selfUse:
        dicRet = appPaaS.preProcessRequest(request,system="PaaS")

        uri_parameter = ["uid"]
        result, result_msg = check_uri_parameter_exist(request,uri_parameter)
        if not result:
            dicRet["Response"] = result_msg
            return jsonify( **dicRet)

    try:
        dicRet["FileContent"] = [{"data":item} for item in _file_content_list_iter(os.path.join(FILEPATH,LogName))]

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    if not selfUse:
        dicRet["Response"] = err_msg
        return jsonify( **dicRet)

    return fileList
# }}}

#=======================================================
# 每日定時由apirecord加總和api次數
# Date: 03032021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/rdps/Daily/Calculate/Aggregately/Apirecords', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/rdps/Daily/Calculate/Aggregately/Apirecords', methods = ['GET'])
def daily_calculate_aggregately_apirecords():
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")

    try:
        dbRedis,_,result= appPaaS.getDbSessionType(system="PaaS",dbName=15,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        #前一天的所有系統redis key(包含PaaS)
        tempsystemlist = globalvar.SYSTEMLIST[globalvar.SERVERIP]
        if "PaaS" not in tempsystemlist:
            tempsystemlist.append("PaaS")
        print "~~~tempsystemlist~~~"
        print tempsystemlist
        for i in tempsystemlist:
            yesterday = datetime.today() + timedelta(-1)
            print yesterday
            # 03112021@Yishan 增加分流api record keys
            yesterday_redis_keys = "api_"+i.lower()+"_"+yesterday.strftime('%Y%m%d')+"*"
            print yesterday_redis_keys
            print dbRedis.keys(yesterday_redis_keys)
            for yesterday_redis_key in dbRedis.keys(yesterday_redis_keys):
                if dbRedis.exists(yesterday_redis_key):
                    success_counts = dbRedis.hget(yesterday_redis_key,"success_counts")
                    success_averagetime = dbRedis.hget(yesterday_redis_key,"success_averagetime")
                    fail_counts = dbRedis.hget(yesterday_redis_key,"fail_counts")
                    upload_time = dbRedis.hget(yesterday_redis_key,"upload_time")
                    print "~~~this count~~~"
                    print success_counts,fail_counts,success_averagetime,upload_time

                    dbName = "sapidoapicount_"+i.lower()
                    print "~~~dbName~~~"
                    print dbName
                    try:
                        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system="PaaS",dbName=dbName,forRawData="postgres")
                        if DbSessionRaw is None:
                            #表示連接資料庫有問題
                            dicRet["Response"] = engineRaw
                            return jsonify( **dicRet)
                        
                        sessRaw = DbSessionRaw()

                        yesterday_api_count_table = Table("api_"+i.lower()+"_"+yesterday.strftime('%Y%m') , metaRaw, autoload=True)

                        print "~~~~old counts~~~~"
                        print sessRaw.query(yesterday_api_count_table).all()

                        updateSql = "update {yesterday_api_count_table} set success_counts=(select success_counts+{success_counts} from {yesterday_api_count_table}),\
                            success_averagetime=(SELECT CASE WHEN success_counts = 0 THEN round({success_averagetime}::numeric,3) \
                                ELSE round(((success_counts*success_averagetime+{success_averagetime})/(success_counts+{success_counts}))::numeric,3) END from {yesterday_api_count_table}),\
                            fail_counts=(select fail_counts+{fail_counts} from {yesterday_api_count_table}),\
                            upload_time='{upload_time}'".format(yesterday_api_count_table=yesterday_api_count_table, success_counts=success_counts, fail_counts=fail_counts, success_averagetime=success_averagetime, upload_time=upload_time)
                        print "~~~~updateSql~~~~"
                        print updateSql

                        sessRaw.execute(updateSql)
                        sessRaw.commit()

                        print "~~~~new counts~~~~"
                        print sessRaw.query(yesterday_api_count_table).all()
                        
                        err_msg = "ok"

                    except Exception as e:
                        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")
                        
                    finally:
                        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
                            sessRaw.close()
                            DbSessionRaw.remove()
                            engineRaw.dispose()
        
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
#}}}

#=======================================================
# monitor processes and system resource usage on Linux
# use psutil
# 監控CPU&RAM
# Date: 03112021@Yishan
#=======================================================
# {{{ DASHBOARD_API.route('/api/PaaS/1.0/sys/Monitor/Server/Processes/Usage', methods = ['GET']),
@DASHBOARD_API.route('/api/PaaS/1.0/sys/Monitor/Server/Processes/Usage', methods = ['GET'])
def monitor_server_processes_usage():
    import psutil
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="PaaS")

    try:
        #單位都是bytes
        MB = 1024*1024 #1MB
        information = {}
        
        #CPU
        cpu_logical = psutil.cpu_count() # CPU逻辑数量
        cpu_physical = psutil.cpu_count(logical=False) # CPU物理核心
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True) #CPU使用率 percpu=True->各cpu
        cpu_times = psutil.cpu_times()
        cpu_times = {
            "user":cpu_times.user,
            "nice":cpu_times.nice,
            "system":cpu_times.system,
            "idle":cpu_times.idle
        }

        #Memory
        memory_virtual = psutil.virtual_memory()
        memory_virtual = {
            "total":memory_virtual.total/MB,
            "available":memory_virtual.available/MB,
            "percent":memory_virtual.percent,
            "used":memory_virtual.used/MB,
            "free":memory_virtual.free/MB,
            "active":memory_virtual.active/MB,
            "inactive":memory_virtual.inactive/MB,
            "buffers":memory_virtual.buffers/MB,
            "cached":memory_virtual.cached/MB,
            "shared":memory_virtual.shared/MB,
            "slab":memory_virtual.slab/MB,
        }

        memory_swap = psutil.swap_memory() #swap memory
        memory_swap = {
            "total":memory_swap.total/MB,
            "used":memory_swap.used/MB,
            "free":memory_swap.free/MB,
            "percent":memory_swap.percent,
            "sin":memory_swap.sin/MB,
            "sout":memory_swap.sout/MB,
        }

        #Disk
        disk_partitions = psutil.disk_partitions() #磁盘分区信息
        disk_usage = {}
        for part in disk_partitions:
            usage = psutil.disk_usage(part.mountpoint)
            disk_usage[part.mountpoint] = {
                "total":usage.total/MB,
                "used":usage.used/MB,
                "free":usage.free/MB,
                "percent":usage.percent,
            }

        server_boottime = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S") #開機時間

        information = {
            "cpu_logical":cpu_logical,
            "cpu_physical":cpu_physical,
            "cpu_usage":cpu_usage,
            "cpu_times":cpu_times,
            "memory_virtual":memory_virtual,
            "memory_swap":memory_swap,
            "disk_partitions":disk_partitions,
            "disk_usage":disk_usage,
            "server_boottime":server_boottime
        }

        dicRet["Information"] = information

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"PaaS")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
#}}}
