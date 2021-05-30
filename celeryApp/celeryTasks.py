# -*- coding: utf-8 -*-
"""
==============================================================================
created    : 02/17/2021
Last update: 02/17/2021
Developer: Yishan Tsai
Lite Version 2 @Yishan08212019
API version 1.0

Filename: celeryTasks.py

Description: for celery tasks
==============================================================================
"""
#=======================================================
# System level modules
#=======================================================
#{{{
import subprocess #Yishan 05212020 subprocess 取代 os.popen
import resource
from celery import Task
import redis
from sqlalchemy import *
#}}}

#=======================================================
# User level modules
#=======================================================
#{{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
from .celeryConfig import readConfig
#}}}

class DBTask(Task):
    # _session = None
    # _sess = None
    # _metadata = None
    # _dbEngine = None
    _system = None
    _systemSess = {}
    print "~~~~DBTask~~~~"

    def after_return(self, *args, **kwargs):
        print "~~~~~after_return~~~~~"
        print self._system
        print self._systemSess
        print self._systemSess[self._system]
        if self._systemSess[self._system] is not None:
            print "^^^^^^^^^^^^^^^^"
            self._systemSess[self._system][0].close()
            self._systemSess[self._system][3].remove()
            self._systemSess[self._system][2].dispose()
            print "vvvvvvvvvvvvvvvv"

    # @property
    def session(self, system):
        # print "$$$$$$$$$$$$$$$$"
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        # print system
        try:
            self._system = system
            print "self._systemSess -> ",self._systemSess
            print "system -> ",system

            # 03172021@Yishan 將不同system的db session存入dict，避免建立新的連接
            if (not self._systemSess.has_key(self._system)):
                from sqlalchemy.orm import scoped_session, sessionmaker
                from sqlalchemy.engine import create_engine
                
                dbUri = "postgresql+psycopg2://{}:{}@{}:{}/{}".format( \
                            dicConfig.get("DBPOSTGRESUser"),   \
                            dicConfig.get("DBPOSTGRESPassword"),   \
                            dicConfig.get("DBPOSTGRESIp"), \
                            dicConfig.get("DBPOSTGRESPort"),  \
                            "sapidoapicount_"+self._system.lower())
                print "@@@@@@dbUri@@@@@@@@"
                print dbUri
                _dbEngine = create_engine(dbUri,encoding='utf-8')
                print "111111111111111"

                _metadata = MetaData(bind=_dbEngine)
                print "222222222222222"
                _session = scoped_session(sessionmaker(autocommit=False, \
                                            autoflush=False, \
                                            bind=_dbEngine))
                print "333333333333333"

                check_status,check_result = check_dbconnect_success(_session, self._system)
                print "444444444444444"
                if not check_status: return None,None,check_result
                
                _sess = _session()
                self._systemSess[self._system] = [_sess,_metadata,_dbEngine,_session]

            return self._systemSess[self._system]
            # return self._sess,self._metadata,self._dbEngine
            
        except Exception as e:
            err_msg = appPaaS.catch_exception(e,sys.exc_info(),system)
            return None,None,err_msg

def print_mem():
    print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

@celery.task(base=DBTask, bind=True)
def celery_post_api_count_record(self, threaddata):
    threaddata = ConvertData().convert(threaddata)
    print "~~~~threaddata~~~~"
    print self.request.id,datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
    print threaddata
    system = threaddata[0]
    if threaddata[0] == "test": system = "IOT"
    dbName = "sapidoapicount_"+system.lower()

    apimethod = threaddata[1]
    apipath = threaddata[2]
    status = 0 if threaddata[3] == "0" else 1
    apiTimeCost = threaddata[4]
    apicompletiontime = threaddata[5]

    # if system not in globalvar.SYSTEMLIST[globalvar.SERVERIP]: return
    
    tbName_count = "api_"+system.lower()+"_"+time.strftime("%Y%m", time.localtime())
    redis_count_key = "api_"+system.lower()+"_"+time.strftime("%Y%m%d", time.localtime())
    if not retrieve_database_exist(system, dbName=dbName, forRawData="postgres", _appPaaS=appPaaS)[0]:
        create_database(system, dbName, forRawData="postgres", _appPaaS=appPaaS)
        
    sessionResult = self.session(system)
    sessRaw = sessionResult[0]
    metaRaw = sessionResult[1]
    engineRaw = sessionResult[2]
    # sessRaw,metaRaw,engineRaw = self.session(system)
    # print "&&&&&&&&&&&&&&&&&&&&&&&&"
    print sessRaw,metaRaw,engineRaw
    # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
    # print "&&&&&&&&&&&&&&&&&&&&&&&&"
    if not sessRaw is None:
        try:
            dbRedis,_,_ = appPaaS.getDbSessionType(system=system,dbName=15,forRawData="redis")
            if dbRedis is None:
                return

            apirecord_hash_num = int(dbRedis.get("apirecord_hash_num"))

            checkexistedResult = checkexisted_api_count_record_table(sessRaw, metaRaw, dbName, tbName_count, system, dbRedis)
        
            if checkexistedResult:
                this_api_record_table = Table(tbName_count+"_record" , metaRaw, autoload=True)
                sessRaw.execute(this_api_record_table.insert().values({"method":apimethod,"apipath":apipath,"status":bool(status),"operation_time":apiTimeCost,"completion_time":apicompletiontime}))
                sessRaw.commit()

                with dbRedis.pipeline() as pipe:
                    count = 0
                    hash_num = 0
                    while True:
                        try:
                            # print "====start redis pipe while===="
                            # print self.request.id,datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
                            # 監聽redis api today key 
                            pipe.watch(redis_count_key)

                            success_counts = int(pipe.hget(redis_count_key,"success_counts"))
                            fail_counts = int(pipe.hget(redis_count_key,"fail_counts"))
                            success_averagetime = float(pipe.hget(redis_count_key,"success_averagetime"))

                            # 开始事务
                            pipe.multi()
                            # 执行操作
                            if not status:
                                pipe.hincrby(redis_count_key, "fail_counts", amount=1)
                            else:
                                success_totaltime = (success_averagetime * success_counts)+apiTimeCost
                                this_averagetime = success_totaltime/(success_counts+1)
                                # this_averagetime = float('%.4f' % (success_totaltime/(success_counts+1)))
                                pipe.hmset(redis_count_key,{"success_counts":success_counts+1,"success_averagetime":this_averagetime,"upload_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                            # 执行事务
                            pipe.execute()
                            break
                        except redis.WatchError:
                            # 事务执行过程中，如果数据被修改，则抛出异常，程序可以选择重试或退出
                            print "====redis pipe error===="
                            print self.request.id,datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
                            count += 1
                            print count
                            if count == 5:
                                count = 0

                                redis_count_key = "_".join(redis_count_key.split("_")[0:3])
                                if hash_num < apirecord_hash_num:
                                    hash_num += 1
                                    redis_count_key += "_"+"#"*hash_num
                                else:
                                    hash_num = 0

                                print "@@@@@@@@@@redis_count_key@@@@@@@@@@"
                                print redis_count_key

                                if not dbRedis.exists(redis_count_key):
                                    dbRedis.hmset(redis_count_key,{"success_counts":0,"fail_counts":0,"success_averagetime":0,"upload_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                                    dbRedis.expire(redis_count_key,88200) #設定過期秒數1天又30分鐘
                            continue
                        finally:
                            # 取消对键的监视
                            pipe.unwatch()
                            # 因为 redis-py 在执行 WATCH 命令期间，会将流水线与单个连接进行绑定
                            # 所以在执行完 WATCH 命令之后，必须调用 reset() 方法将连接归还给连接池
                            pipe.reset() # 重置管道，为重试做准备
                    # print "====after redis pipe while===="
                    # print self.request.id,datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

        except Exception as e:
            err_msg = appPaaS.catch_exception(e, sys.exc_info(), system)
            print "~~~~err_msg~~~~"
            print err_msg

        finally:
            print_mem()
        #     sessRaw.close()
        #     DbSessionRaw.remove()
        #     engineRaw.dispose()
    
    else:
        #Yishan 02062020 當postgresql連線數超過時先寫入txt
        with open("/var/www/spdpaas/doc/offlinemode_apirecord.txt",'r+') as x:
            fileaString = x.read()
            txt_success = int(fileaString[8])
            txt_fail =  int(fileaString[15])
            if not status:
                txt_fail += 1
                x.seek(15,0)
                x.write(txt_fail)
            else:
                txt_success +=1
                x.seek(8,0)
                x.write(txt_success)
#}}}

#=======================================================
# 觸發指定程式
# Date: 01252020@Yishan
#=======================================================
@celery.task()
def celery_trigger_specific_program(cmd,SYSTEM):
    try:        
        with open(os.devnull, 'w') as devnull:
            process = subprocess.check_output(cmd,shell=False,stderr=devnull)
    except Exception as e:
        print '~~~~~~celery_trigger_specific_program Exception~~~~~'
        print e
    
    # print_mem()

#=======================================================
# 發送郵件
# Date: 01252020@Yishan
#=======================================================
@celery.task()
def celery_send_email(selfUse, which, emailData):
    from app.features.emailHandle import SapidoSystemTodoListEmailConfig, CommonUseEmailConfig
    if which == "todolist":
        send = SapidoSystemTodoListEmailConfig(selfUse)
        msg_ok = "To-do notification email sent successfully"
        msg_error = "To-do notification email delivery failed"
    elif which == "commonuse":
        send = CommonUseEmailConfig()
        msg_ok = "CommonUse email sent successfully"
        msg_error = "CommonUse email delivery failed"
    #發送成功
    if send.sendemail(emailData):
        print("[{}] ".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]),msg_ok)
    #發送失敗
    else:
        print("[{}] ".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]),msg_error)

#=======================================================
# Definition: 初始設定apirecord的hash numer(apirecord_hash_num)
# Date: 03302021@Yishan
#=======================================================
# {{{def apirecord_hash_num_init()
def apirecord_hash_num_init():
    try:
        dbRedis,_,_ = appPaaS.getDbSessionType(system="PaaS",dbName=15,forRawData="redis")
        if dbRedis is None:
            return
        
        #若key不存在，直接建立
        if not dbRedis.exists("apirecord_hash_num"):
            dbRedis.set("apirecord_hash_num", 10)

    except Exception as e:
        print "@@@@@apirecord_hash_num_init@@@@@"
        print apirecord_hash_num_init
        appPaaS.catch_exception(e, sys.exc_info(), "PaaS")

#=======================================================
# 建立新的countapitimes Table(年月為單位)
# Date: Yishan 09272019
#=======================================================
# {{{ def create_api_count_record_table(sessRaw, metaRaw, tbName, system, which, dbRedis=None):
def create_api_count_record_table(sessRaw, metaRaw, tbName, system, which, dbRedis=None):
    try:
        if which == "count":
            if dbRedis is not None:
                dbRedis.hmset(tbName,{"success_counts":0,"fail_counts":0,"success_averagetime":0,"upload_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                print "~~~~tbName~~~~"
                print tbName
                dbRedis.expire(tbName,88200) #設定過期秒數1天又30分鐘
            else:
                new_table = Table(tbName, metaRaw, 
                    Column("success_counts",Integer),
                    Column("fail_counts",Integer),
                    Column("success_averagetime",Float),
                    Column("upload_time", TIMESTAMP(timezone=False),server_default=func.current_timestamp(6)) 
                )
                addData = {"success_counts":0,"fail_counts":0,"success_averagetime":0,"upload_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        else:
            new_table = Table(tbName, metaRaw, 
                Column("method", VARCHAR(10),nullable=False), 
                Column("apipath", VARCHAR(256),nullable=False), 
                Column("status", Boolean,nullable=False), 
                Column("operation_time", Float,nullable=False),
                Column("completion_time", TIMESTAMP(timezone=False)),
                Column("upload_time", TIMESTAMP(timezone=False),server_default=func.current_timestamp(6)) 
            )

        if dbRedis is None:
            new_table.create()
            metaRaw.create_all()

            if which == "count":
                sessRaw.execute(new_table.insert().values(addData))
                sessRaw.commit()
        
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),system)
# }}}

#=======================================================
# 檢查countapitimes Table是否存在
# Date: Yishan 09272019
#=======================================================
#{{{ def checkexisted_api_count_record_table(sessRaw, metaRaw, dbName, tbName_count, system, dbRedis=None):
def checkexisted_api_count_record_table(sessRaw, metaRaw, dbName, tbName_count, system, dbRedis=None):
    from sqlalchemy.exc import InvalidRequestError
    # successcounts = 0
    # failcounts = 0
    # success_averagetime = 0
    tbName_record = tbName_count+"_record"

    try:
        if dbRedis is not None:
            redis_api_key = "api_"+system.lower()+"_"+time.strftime("%Y%m%d", time.localtime())
            if not dbRedis.exists(redis_api_key):
                create_api_count_record_table(sessRaw, metaRaw, redis_api_key, system, "count", dbRedis)

        try:
            #Yishan 10182019 check table existed with metaRaw.reflect()
            metaRaw.reflect(only=[tbName_count])
        
        except InvalidRequestError as error:
            print "~~~~error~~~~"
            print error
            if not re.search(r'Could not reflect',str(error)):
                appPaaS.catch_exception(e,sys.exc_info(),system)
                return False

            create_api_count_record_table(sessRaw, metaRaw, tbName_count, system, "count")
        
        try:
            #Yishan 10182019 check table existed with metaRaw.reflect()
            metaRaw.reflect(only=[tbName_record])
        
        except InvalidRequestError as error:
            print "~~~~error~~~~"
            print error
            if not re.search(r'Could not reflect',str(error)):
                appPaaS.catch_exception(e,sys.exc_info(),system)
                return False

            create_api_count_record_table(sessRaw, metaRaw, tbName_record, system, "record")
                
        return True
    except Exception as e:
        appPaaS.catch_exception(e,sys.exc_info(),system)
        return False
#}}}

__all__ = [
    'celery_post_api_count_record', 'celery_trigger_specific_program',
    'celery_send_email', 'apirecord_hash_num_init'
]
