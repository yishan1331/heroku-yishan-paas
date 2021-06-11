# -*- coding: utf-8 -*-
#sensor Module Description
"""
==============================================================================
created    : 03/20/2017
Last update: 03/31/2021
Developer: Wei-Chun Chang 
Lite Version 2 @Yishan08212019
API Version 1.0
 
Filename: sensorHandle.py
Description: basically, all writes to the module will be opened to users who has authorized 
    1. register a sensor
    2. query a sensor's basic info.
    3. query sensor raw data
       queryFirst/queryLast/queryRows
    4. post sensor raw data
Total = 22 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
#{{{ 
from sqlalchemy import *
import subprocess #Yishan 05212020 subprocess 取代 os.popen
#}}}

#=======================================================
# User level modules
#=======================================================
#{{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
from app.features.customizedHandle import trigger_specific_program
from app.dbModel.iot import Sensor
#}}}

__all__ = ('SENSOR_API', 'retrieve_table')

ACCESS_SYSTEM_LIST = ["IOT","CHUNZU","YS"]

#blueprint
SENSOR_API = Blueprint('SENSOR_API', __name__)

#=======================================================
# Definition: 檢查mysql sensor表內是否有此sensor資料，若有就表示postgresql會有此表
#=======================================================
# {{{ def retrieve_table()
def retrieve_table(SYSTEM,sensor_raw_table):
    status = True
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            status = False
            result = engine
            return
        
        sess = DbSession()

        result = []
        for row in sess.query(Sensor.noumenon_id, \
                Sensor.noumenon_type, \
                Sensor.sensor_raw_table).\
                filter(Sensor.sensor_raw_table == sensor_raw_table).  \
                all():
            drow = AdjustDataFormat().format(row._asdict())
            result.append(drow)
        
        if len(result) == 0:
            status = False
            result = "'{}' ID isn't exist".format(sensor_raw_table)
        else:
            thisid_existed,catch_dbname = retrieve_noumenon_dbname(metadata,sess,result[0]["noumenon_type"],result[0]["noumenon_id"])
            if not thisid_existed:
                status = False
                result = "this : 'noumenon_type' : '{}' & 'noumenon_id' : '{}' doesn't existed".format(result[0]["noumenon_type"],result[0]["noumenon_id"])
            else:
                result[0]["db_name"] = catch_dbname
                result = result[0]
    
    except Exception as e:
        status = False
        result = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

        return status,result
#}}}

#=======================================================
# Definition: To retrieve sensor raw table name and other info.
# reserve for future usage
# return queryRec[] = [noumenon_id, noumenon_type, sensor_raw_table, db_name]
#=======================================================
# {{{ def _retrieve_senrawtable(sensor_raw_table)
def _retrieve_senrawtable(sess,metadata,sensor_raw_table):
    status = True
    result = []
    for row in sess.query(Sensor.noumenon_id, \
            Sensor.noumenon_type, \
            Sensor.sensor_raw_table).\
            filter(Sensor.sensor_raw_table == sensor_raw_table).  \
            all():
        drow = AdjustDataFormat().format(row._asdict())
        result.append(drow)
    
    if len(result) == 0:
        result = "'{}' ID isn't exist".format(sensor_raw_table)
    else:
        thisid_existed,catch_dbname = retrieve_noumenon_dbname(metadata,sess,result[0]["noumenon_type"],result[0]["noumenon_id"])
        if not thisid_existed:
            status = False
            result = "this : 'noumenon_type' : '{}' & 'noumenon_id' : '{}' doesn't existed".format(result[0]["noumenon_type"],result[0]["noumenon_id"])
        else:
            result[0]["db_name"] = catch_dbname
            result = result[0]

    return status,result
# }}}

#=======================================================
# Definition: to desc mysql table
# Date: 09172019@sandy
#=======================================================
#{{{def _desc_table(SYSTEM,sqlfilename,quarter,setquery)
def _desc_table(SYSTEM,metaRaw,senTableName):
    fieldList = []
    prikeyisTime = False
    schemaDict = {}
    try:
        #Yishan@12262019 add param only for反射指定表
        metaRaw.reflect(only=[senTableName])

        for table in metaRaw.tables.values():
            if table.name == senTableName:
                for column in table.c:
                    fieldList.append(column.name)
                    if check_user_defined_type(column):
                        schemaDict[column.name] = str(column.type)
                    else:
                        schemaDict[column.name] = "UserDefinedType"
                    if (column.primary_key) and (str(column.type) == "TIMESTAMP WITHOUT TIME ZONE"):
                        prikeyisTime = True
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
        
    finally:
        return err_msg,fieldList,schemaDict,prikeyisTime
#}}}

#=======================================================
# Definition: 刪除備份好的postgresql table data
# Date: 09202019@Yishan
#=======================================================
#{{{def del_backup_tabledata(SYSTEM,senTableName,start_year,end_year,temporarytable)
def del_backup_tabledata(SYSTEM,sessRaw,senTableName,start_year,end_year,temporarytable):
    try:
        sqlStr1 = 'DELETE from {} where {} between \'{}\' and \'{}\';'.format(senTableName,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"],start_year,end_year)
        sqlStr2 = 'DROP TABLE IF EXISTS "{}";'.format(temporarytable)
        sessRaw.execute(sqlStr1)
        sessRaw.execute(sqlStr2)
        sessRaw.commit()
        err_msg = "ok"
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    return err_msg
#}}}

#=======================================================
# Definition: postgresql 先查詢後刪除temporary backup table data
# Date: 09202019@Yishan
#=======================================================
#{{{def qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,quarter,setquery)
def qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,quarter,setquery):
    recList = []
    err_msg = ""
    sqlfile_year = sqlfilename.split("_")
    sqlfile_year = sqlfile_year[1]
    DAYSTART = "01 00:00:00"
    set_quarter = ["",1,4,7,10]
    set_days30or31 = ["","31 23:59:59","30 23:59:59","30 23:59:59","31 23:59:59"]

    try:
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName="iot",forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            err_msg = engineRaw
            return
        
        sessRaw = DbSessionRaw()

        if not retrieve_table_exist(metaRaw,sqlfilename,SYSTEM):
            err_msg = "Table '{}' doesn't exist".format(sqlfilename)
            return

        backuptable = Table(sqlfilename , metaRaw, autoload=True)
        query_field = getattr(backuptable.c, globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"])

        if setquery:
            if quarter == 0:
                result = sessRaw.query(backuptable).all()
            else:
                if quarter != "":
                    yearmonthStart = sqlfile_year+"-"+str(set_quarter[quarter])+"-"
                    yearmonthEnd = sqlfile_year+"-"+str((set_quarter[quarter]+2))+"-"
                    whereStart = yearmonthStart + DAYSTART
                    whereEnd = yearmonthEnd + set_days30or31[quarter]
                    result = sessRaw.query(backuptable).filter(query_field.between(whereStart,whereEnd)).all()

            for row in result:
                drow = AdjustDataFormat().format(row._asdict())
                recList.append(drow)

            if len(recList) == 0:
                err_msg = "There is no matching data for your query"
            else:
                err_msg = "ok"
        else:
            backuptable.drop()
            err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

        return recList,err_msg
#}}}

#=======================================================
# Definition: 檢查redis是否有此senID key，若無則建立，有則直接返回dbName to postgresql
# Date: 12022020@Yishan
#=======================================================
#{{{def get_redis_sensor_IDKEY_ornot_create(SYSTEM,sensorID)
def get_redis_sensor_IDKEY_ornot_create(SYSTEM,sensorID):
    """
    建立redis connect檢查redis是否有此senID key，若無則建立(期限86400s)，有則直接返回dbName

    Args:
        SYSTEM: this SYSTEM
        sensorID: this sensorID

    Returns:
        dbName
    """
    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result = appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            return False,result

        if dbRedis.exists(sensorID):
            dbName = dbRedis.get(sensorID)
        else:
            #查詢mysql-sensor該ID是否存在
            thisIDexisted,sensorDict = retrieve_table(SYSTEM,sensorID)
            if not thisIDexisted:
                return False,sensorDict
            
            dbName = sensorDict["db_name"]
            #sensorID:dbName資訊更新至Redis，並設定期限一天86400s
            dbRedis.setex(sensorID, 86400, dbName)

        return True,dbName
    except Exception as e:
        print "~~~eee~~~~"
        print e
        return False,appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
#}}}

#=======================================================
# API: /api/<SYSTEM>/1.0/myps/Sensor/NoumenonIDs
# Definition: 提供使用者抓取不同感測器的NoumenonID
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/NoumenonIDs', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/NoumenonIDs',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_get_noumenonIDs(SYSTEM):
    #{{{APIINFO
    """
    {
        "API_application":"提供使用者抓取不同感測器的NoumenonID",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
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
            "APIS": "POST /api/IOT/1.0/myps/Sensor/NoumenonIDs",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MYSQL+POSTGRES",
            "System": "IOT",
            "dbNames": {"work_code_use":"","mould_series_no_use":"","mould_series_no_abn":"","material_batch_no_use":"","material_batch_no_abn":""}
        }
    } 
    """
    #}}}
    err_msg = "error"
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

    #先將unicode data change to str
    reqdataDict = AdjustDataFormat().format(reqdataDict)

    post_parameter = ["sensor_raw_table"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    sensor_raw_table = reqdataDict.get("sensor_raw_table")

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)

        dbNames = {}
        for tableName in sensor_raw_table:
            #查詢該ID是否存在
            thisIDexisted,sensorDict = retrieve_table(SYSTEM,tableName)
            if not thisIDexisted:
                dicRet["Response"] = sensorDict
                return jsonify(**dicRet)

            dbName = sensorDict["db_name"]
            dbNames[tableName] = dbName
        else:
            dicRet["dbNames"] = dbNames
            err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"
    return jsonify(**dicRet)
# }}}

#=======================================================
# API: /api/<SYSTEM>/1.0/myps/Sensor 
# Definition:
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_register(SYSTEM):
    #{{{APIINFO
    """
    {
        "API_application":"提供註冊mysql一感測器基本資料服務，並在postgresql建立感測器資料表",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "name":{"type":"String","requirement":"required","directions":"感測器名稱，亦為postgresql資料表描述說明","example":"test"},
                "sensor_type":{"type":"Boolean","requirement":"required","directions":"感測器類別(0=非實體,1=實體)","example":0},
                "noumenon_type":{"type":"String","requirement":"required","directions":"隸屬類別(dep/site/pla/dev)","example":"dev"},
                "noumenon_id":{"type":"Integer","requirement":"required","directions":"隸屬編號","example":"dev"},
                "sensor_raw_table":{"type":"String","requirement":"required","directions":"資料表名稱，","example":"test"},
                "sensor_attr":{
                    "type":"Array",
                    "requirement":"required",
                    "directions":[
                        "建立postgresql資料表的屬性，詳細內容格式請看'Show Details'",
                        {
                            "name":{"說明":"欄位名稱(string)"},
                            "type":{
                                "說明":"欄位屬性(string)",
                                "備註":"可放以下sql屬性：INTEGER(postgresql不支援指定長度，若需指定長度改用NUMERIC)/BOOLEAN/VARCHAR/JSON/NUMERIC/TIMESTAMP",
                                "注意事項":"若欲使用INTEGER當主鍵且為auto-increment值，primarykey設為true_autoinc，即可"
                            },
                            "primarykey":{"說明":"欄位主鍵(string)","備註":"true/true_autoinc/false"},
                            "length":{"說明":"欄位長度(string)"},
                            "default":{"說明":"欄位預設值(string)","備註":"若無預設值則不用放此參數"},
                            "nullable":{"說明":"欄位nullable(string)","備註":"true/false"},
                            "comment":{"說明":"欄位備註說明(string)"}
                        }
                    ],
                    "example":[
                        {"name":"machine_detail","type":"JSON","length":"","primarykey":"","nullable":"","comment":"測試JSON"}
                    ]
                },
                "note":{"type":"String","requirement":"required","directions":"備註說明","example":"test"},
                "creator":{"type":"Integer","requirement":"required","directions":"建立者","example":1},
                "modifier":{"type":"Integer","requirement":"required","directions":"修改者","example":1}
            },
            "precautions": {
                "注意事項1":"'sensor_attr' 目前尚未提供foreign key，固定欄位會有upload_at",
                "注意事項2":"'sensor_raw_table' 系統會自動變小寫，不得重複",
                "注意事項3":"'noumenon_id' 須已註冊的元件，不可為空"
            },
            "example":[
                {
                    "name":"test",
                    "sensor_type":1,
                    "noumenon_type":"site",
                    "noumenon_id":1,
                    "sensor_raw_table":"test",
                    "sensor_attr":[
                        {"name":"machine_detail","type":"JSON","length":"","primarykey":"","nullable":"","comment":"測試JSON"}
                    ],
                    "note":"",
                    "creator":1,
                    "modifier":1
                }
            ]
        },
        "API_message_parameters":{
            "dbName":"string",
            "DB":"string"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/IOT/1.0/myps/Sensor",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MYSQL+POSTGRES",
            "System": "IOT",
            "dbName": "site2"
        }
    } 
    """
    #}}}
    err_msg = "error"
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

    post_parameter = ["name","sensor_type","noumenon_type","noumenon_id","sensor_raw_table","sensor_attr","note","creator","modifier"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    name = reqdataDict.get("name").encode('utf8').strip()
    sensor_type = reqdataDict.get("sensor_type")
    noumenon_type = reqdataDict.get("noumenon_type").encode('utf8').strip()
    noumenon_id = reqdataDict.get("noumenon_id")
    sensor_raw_table = reqdataDict.get("sensor_raw_table").encode('utf8').strip()
    sensor_attr = reqdataDict.get("sensor_attr")
    note = reqdataDict.get("note").encode('utf8').strip()
    creator = reqdataDict.get("creator")
    modifier = reqdataDict.get("modifier")

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #-----------------------------------------------------------
        # Need to add process to collect DB name from upper Noumenon
        #-----------------------------------------------------------
        if noumenon_type not in ("dep","site","pla","dev"):
            dicRet["Response"] = "'noumenon_type' : '{}' 必須是下面4個其一('dep','site','pla','dev')".format(noumenon_type)
            return jsonify( **dicRet)

        thisid_existed,dbName = retrieve_noumenon_dbname(metadata,sess,noumenon_type,noumenon_id)
        if not thisid_existed:
            dicRet["Response"] = "this : 'noumenon_type' : '{}' & 'noumenon_id' : '{}' doesn't existed".format(noumenon_type,noumenon_id)
            return jsonify( **dicRet)

        senRawTable = sensor_raw_table.lower()
        if dbName is not None:
            retrieve_status,retrieve_result = retrieve_database_exist(SYSTEM, dbName=dbName, forRawData="postgres")
            if not retrieve_status:
                dicRet["Response"] = retrieve_result
                return jsonify( **dicRet)

            check_data_existed = False
            for row in sess.query(Sensor.id,Sensor.sensor_raw_table).filter(Sensor.sensor_raw_table == senRawTable).all():
                check_data_existed = True
            
            if check_data_existed:
                dicRet["Response"] = "sensor_raw_table : '{}' existed".format(senRawTable)
                return jsonify( **dicRet)

            sensor_attrnameList = []
            #判斷sensor_attr格式正確性
            post_parameter = ["name","type","length","primarykey","nullable","comment"]
            for i in sensor_attr:
                sensor_attrnameList.append(i["name"])
                if not check_post_parameter_exist(i,post_parameter):
                    dicRet["Response"] = " sensor_attr '{}' Missing post parameters : '{}'".format(i,post_parameter)
                    return jsonify( **dicRet)

            #若sensor_attr的長度跟抓到的name長度不同，表示有重複的name，回覆error
            if len(sensor_attr) != len(list(set(sensor_attrnameList))):
                dicRet["Response"] = "sensor_attr fields 'name' : '{}' is duplicate".format(sensor_attrnameList)
                return jsonify( **dicRet)

            #先至mysql新增資料，新增成功再去postgresql建表
            newSenRec = Sensor(name = name, \
                sensor_type = sensor_type, \
                noumenon_type = noumenon_type, \
                noumenon_id = noumenon_id, \
                sensor_raw_table = senRawTable, \
                sensor_attr = sensor_attr, \
                note = note, \
                creator = creator, \
                modifier = modifier)

            sess.add(newSenRec)
            sess.commit()
            err_msg = "ok"
            dicRet["dbName"] = dbName

            if err_msg == "ok":
                #create a raw data table for a sensor , tableName-dbName-attribute list in json K-V pairs
                resultRaw ,mesgRaw = create_table(table_name=senRawTable, dbName=dbName, attrList=sensor_attr, table_comment=name, system=SYSTEM)
                #建表失敗，刪除mysql sensor data
                if not resultRaw:
                    sess.query(Sensor.sensor_raw_table).filter(Sensor.sensor_raw_table == senRawTable).delete()
                    sess.commit()
                    #reset raw table name to null due to the failure of raw table creation
                    senRawTable=""
                    err_msg = mesgRaw
        else:
            err_msg = "No DB found"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"
    return jsonify(**dicRet)
# }}}

#=======================================================
# API: /api/<SYSTEM>/1.0/myps/Sensor/Rows/<sensorID>
# Definition: use single dictionary to pack data
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Rows/<sensor_raw_table>', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Rows/<sensor_raw_table>',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_post_rows(SYSTEM,sensor_raw_table):
    #{{{APIINFO
    """
    {
        "API_application":"新增一筆或多筆postgresql串流資料記錄",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sensor_raw_table":"感測器資料表名稱"},
        "API_postData":{
            "bodytype":"Array",
            "資料表所有欄位":{"type":"依資料屬性","requirement":"required","directions":"資料表所有欄位值","example":"value1"},
            "precautions":{
                "注意事項1":"資料表所有欄位全部組成一個物件Object，要新增幾筆就傳入幾筆物件以陣列Array包起來",
                "注意事項2":"若為JSON欄位值，可以JSON物件或JSON字串方式傳入但key必須以雙引號包起來",
                "注意事項3":"各表必輸入的所有資料欄位(若可為null可以不放，時間欄位可以不放)"
            },
            "example":[
                [
                    {"machine_detail":{"power_light":1,"in_lube":1,"overload":0,"fnt_sf_pin":0,"sf_door":0}},
                    {"machine_detail":{"power_light":1,"in_lube":1,"overload":0,"fnt_sf_pin":0,"sf_door":2}}
                ]
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{"DB":"string"},
        "API_example":{
            "APIS": "POST /api/IOT/1.0/myps/Sensor/Rows/MCW1000",
            "OperationTime": "2.878",
            "Response": "ok",
            "BytesTransferred": 204,
            "DB":"MYSQL+POSTGRES"
        }
    }
    """
    #}}}
    err_msg = "error"
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

    #查詢該ID是否存在
    thisIDexisted,sensorDict = retrieve_table(SYSTEM,sensor_raw_table)
    if not thisIDexisted:
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensor_raw_table

    try: 
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        reqdataDict = ConvertData().convert(reqdataDict)
        #檢查postdata格式是否為陣列
        if not isinstance(reqdataDict,list):
            dicRet["Response"] = "Error type of postData : '{}', it must be an Array".format(reqdataDict)
            return jsonify( **dicRet)
        
        SensorTable = Table(senTableName, metaRaw,  autoload=True)

        desc_table_status,_,schemaDict,prikeyisTime = _desc_table(SYSTEM,metaRaw,senTableName)
        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        if not prikeyisTime:
            sqlInsert = SensorTable.insert().values(reqdataDict)
            sessRaw.execute(sqlInsert)
            sessRaw.commit()
        else:
            for i in reqdataDict:
                sqlInsert = SensorTable.insert().values(i)
                sessRaw.execute(sqlInsert)
                sessRaw.commit()
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
        
    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"
    return jsonify(**dicRet) 
# }}}

#=======================================================
# API: /api/<SYSTEM>/1.0/myps/Sensor/Rows/<sensorID>
# Definition: use single dictionary to pack data
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Rows/<sensor_raw_table>', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Rows/<sensor_raw_table>',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_post_rows_v2(SYSTEM,sensor_raw_table):
    #{{{APIINFO
    """
    {
        "API_application":"新增一筆或多筆postgresql串流資料記錄，redis DB會期效性(一天)的紀錄dbName(隸屬資料庫名稱)，當redis有此table key則直接抓取value，減少mysql、postgresql依賴性",
        "API_parameters":{"uid":"使用者帳號","trigger_php":"是否觸發指定php程式yes/no(預設觸發，若沒丟此參數為觸發)"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sensor_raw_table":"感測器資料表名稱"},
        "API_postData":{
            "bodytype":"Array",
            "bodyschema":[],
            "資料表所有欄位":{"type":"依資料屬性","requirement":"required","directions":"資料表所有欄位值","example":"value1"},
            "precautions":{
                "注意事項1":"資料表所有欄位全部組成一個物件Object，要新增幾筆就傳入幾筆物件以陣列Array包起來",
                "注意事項2":"若為JSON欄位值，可以JSON物件或JSON字串方式傳入但key必須以雙引號包起來",
                "注意事項3":"各表必輸入的所有資料欄位(若可為null可以不放，時間欄位可以不放)"
            },
            "example":[
                [
                    {"machine_detail":{"power_light":1,"in_lube":1,"overload":0,"fnt_sf_pin":0,"sf_door":0}},
                    {"machine_detail":{"power_light":1,"in_lube":1,"overload":0,"fnt_sf_pin":0,"sf_door":2}}
                ]
            ]
        },
        "API_message_parameters":{"DB":"string"},
        "API_example":{
            "APIS": "POST /api/IOT/2.0/myps/Sensor/Rows/MCW1000",
            "OperationTime": "2.878",
            "Response": "ok",
            "BytesTransferred": 204,
            "DB":"MYSQL+POSTGRES"
        }
    }
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    
    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    trigger_php = False
    if request.args.get("trigger_php") is None:
        trigger_php = True
    else:
        if request.args.get("trigger_php") == "yes": trigger_php = True

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)
        
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    senTableName = sensor_raw_table

    #先去檢查Redis是否有此key:senTableName
    status,result = get_redis_sensor_IDKEY_ornot_create(SYSTEM,senTableName)
    if not status:
        dicRet["Response"] = result
        return jsonify( **dicRet)
    dbName = result

    try: 
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        reqdataDict = ConvertData().convert(reqdataDict)
        #檢查postdata格式是否為陣列
        if not isinstance(reqdataDict,list):
            dicRet["Response"] = "Error type of postData : '{}', it must be an Array".format(reqdataDict)
            return jsonify( **dicRet)
        
        SensorTable = Table(senTableName, metaRaw,  autoload=True)

        desc_table_status,_,schemaDict,prikeyisTime = _desc_table(SYSTEM,metaRaw,senTableName)
        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        if not prikeyisTime:
            sqlInsert = SensorTable.insert().values(reqdataDict)
            sessRaw.execute(sqlInsert)
            sessRaw.commit()
        else:
            for i in reqdataDict:
                sqlInsert = SensorTable.insert().values(i)
                sessRaw.execute(sqlInsert)
                sessRaw.commit()
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
        
    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()
    
    if trigger_php and err_msg == "ok":
        programDir = SYSTEM
        #確定PaaS是否為container
        if globalvar.ISCONTAINER: programDir = globalvar.CONTAINER_API_HTML
        trigger_settime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        # print "~~~~trigger_specific_program~~~~~"
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        trigger_obj = {"table":senTableName,"data":reqdataDict,"upload_at":trigger_settime,"ip":request.host.split(":")[0]}
        trigger_specific_program(SYSTEM, selfUse=True, useThread=True, languages="php", programName="/{}/mes_modules/mes_modules.php".format(programDir), programData=json.dumps(ConvertData().convert(trigger_obj)), postHttp=True)
        # print "~~~~trigger_specific_program over~~~~~"
        # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"
    # print "~~~~~sensor post end~~~~~~"
    # print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
    return jsonify(**dicRet) 
# }}}

@SENSOR_API.route('/testtimer/<sensor_raw_table>',  methods = ['POST'])
def testtimerPost(sensor_raw_table):
    funcstart = time.time()
    print request.args.get("flag"),"| Step2:API Server收到請求後將請求傳入新增function裡的花費時間:{:.6f}".format(funcstart-request.request_start_time_)
    print request.args.get("flag"),"|",datetime.fromtimestamp(funcstart).strftime("%Y-%m-%d %H:%M:%S.%f")
    dicRet = appPaaS.preProcessRequest(request,system="IOT")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    times = request.args.get("times")

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)
        
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    #查詢該ID是否存在
    thisIDexisted,sensorDict = retrieve_table(SYSTEM,sensor_raw_table)
    if not thisIDexisted:
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensor_raw_table

    try:
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system="IOT",dbName="site2",forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        reqdataDict = ConvertData().convert(reqdataDict)
        #檢查postdata格式是否為陣列
        if not isinstance(reqdataDict,list):
            dicRet["Response"] = "Error type of postData : '{}', it must be an Array".format(reqdataDict)
            return jsonify( **dicRet)
        
        SensorTable = Table(sensor_raw_table, metaRaw,  autoload=True)

        sqlInsert = SensorTable.insert().values(reqdataDict)
        sessRaw.execute(sqlInsert)
        sessRaw.commit()
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"IOT")
        
    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()
    
    dicRet["Response"] = err_msg
    dicRet["flag"] = request.args.get("flag")

    funcend = time.time()
    setattr(request,"funcend",funcend)
    print request.args.get("flag"),"| Step3:新增function執行的花費時間:{:.6f}".format(funcend-funcstart)
    print request.args.get("flag"),"|",datetime.fromtimestamp(funcend).strftime("%Y-%m-%d %H:%M:%S.%f")

    return jsonify(**dicRet) 

#=======================================================
# API: '/api/<SYSTEM>/1.0/myps/Sensor/SingleRow/First/<serialID>', 
#      '/api/<SYSTEM>/1.0/myps/Sensor/SingleRow/Last/<serialID>'
# Definition:
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/SingleRow/<querySingle>/<sensor_raw_table>', methods = ['GET']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/SingleRow/<querySingle>/<sensor_raw_table>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_single_row(SYSTEM,querySingle, sensor_raw_table):
    #{{{APIINFO
    """
    {
        "API_application":"提供查詢postgresql單一感測器感測資料服務(最新一筆或第一筆)",
        "API_path_parameters":{
            "SYSTEM":"合法的系統名稱",
            "querySingle":"First(取得第一筆資料)/Last(取得最後一筆資料)",
            "sensor_raw_table":"感測器資料表名稱"
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{
            "RowData":"JSON",
            "DB":"string"
        },
        "API_example":{
            "APIS": " GET /api/IOT/1.0/myps/Sensor/SingleRow/Last/weight",
            "BytesTransferred": 329,
            "OperationTime": "0.129",
            "Response": "ok",
            "RowData":[{
                "upload_at": "2019-08-06 11:43:58",
                "weight": 46.0,
                "seq": 7966
            }],
            "DB":"MYSQL+POSTGRES"
        }
    }
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    #查詢該ID是否存在
    thisIDexisted,sensorDict = retrieve_table(SYSTEM,sensor_raw_table)
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensor_raw_table
    
    try: 
        DbSessionRaw,_,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        recLast = []
        #wei@04192017, doing double check for single query first/last
        if (querySingle == "First"):
            sqlStr = 'select * from "{}" order by {} asc limit 1;'.format(senTableName,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"])
            dicStr = 'FirstRowData'
        elif (querySingle == "Last"):
            sqlStr = 'select * from "{}" order by {} desc limit 1;'.format(senTableName,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"])
            dicStr = 'LastRowData'

        for row in sessRaw.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recLast.append(drow)

        dicRet["QueryTableData"] = recLast
        err_msg = "ok" 
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"
    
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/2.0/myps/Sensor/SingleRow/First/<serialID>', 
#      '/api/<SYSTEM>/2.0/myps/Sensor/SingleRow/Last/<serialID>'
# Definition:
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/SingleRow/<querySingle>/<sensor_raw_table>', methods = ['GET']), 
@SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Singleow/<querySingle>/<sensor_raw_table>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_single_row_v2(SYSTEM,querySingle, sensor_raw_table):
    #{{{APIINFO
    """
    {
        "API_application":"提供查詢postgresql單一感測器感測資料服務(最新一筆或第一筆)，不經過mysql直接抓取postgresql",
        "API_path_parameters":{
            "SYSTEM":"合法的系統名稱",
            "querySingle":"First(取得第一筆資料)/Last(取得最後一筆資料)",
            "sensor_raw_table":"感測器資料表名稱"
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{
            "RowData":"JSON",
            "DB":"string"
        },
        "API_example":{
            "APIS": " GET /api/IOT/2.0/myps/Sensor/SingleRow/Last/weight",
            "BytesTransferred": 329,
            "OperationTime": "0.129",
            "Response": "ok",
            "RowData":[{
                "upload_at": "2019-08-06 11:43:58",
                "weight": 46.0,
                "seq": 7966
            }],
            "DB":"MYSQL+POSTGRES"
        }
    }
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    senTableName = sensor_raw_table

    #先去檢查Redis是否有此key:senTableName
    status,result = get_redis_sensor_IDKEY_ornot_create(SYSTEM,senTableName)
    if not status:
        dicRet["Response"] = result
        return jsonify( **dicRet)
    dbName = result
    
    try: 
        DbSessionRaw,_,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        recLast = []
        #wei@04192017, doing double check for single query first/last
        if (querySingle == "First"):
            sqlStr = 'select * from "{}" order by {} asc limit 1;'.format(senTableName,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"])
            dicStr = 'FirstRowData'
        elif (querySingle == "Last"):
            sqlStr = 'select * from "{}" order by {} desc limit 1;'.format(senTableName,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"])
            dicStr = 'LastRowData'

        for row in sessRaw.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recLast.append(drow)

        dicRet["QueryTableData"] = recLast
        err_msg = "ok" 
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"
    
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/1.0/myps/Sensor/Interval/<sensor_raw_table>'
# Definition:
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Interval/<sensor_raw_table>', methods = ['GET']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Interval/<sensor_raw_table>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_multirows(SYSTEM,sensor_raw_table):
    #{{{APIINFO
    """
    {
        "API_application":"提供查詢postgresql感測器資料內容的一個範圍",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sensor_raw_table":"感測器資料表名稱"},
        "API_parameters":{
            "uid":"使用者帳號",
            "attr":"資料屬性名稱",
            "valueStart":"欲查詢資料起始值",
            "valueEnd":"欲查詢資料終端值"
        },
        "API_message_parameters":{
            "QueryMultiRows":"JSON",
            "DB":"string"
        },
        "API_example":{
            "APIS": " GET /api/IOT/1.0/myps/Sensor/Interval/weight",
            "BytesTransferred": 265,
            "OperationTime": "0.044",
            "Response": "ok",
            "DB":"MYSQL+POSTGRES",
            "QueryMultiRows":[{"upload_at": "2019-07-03 16:00:00","weight": 0.1,"seq": 1}, {"upload_at": "2019-07-25 16:00:00", "weight": 0.003, "seq": 2}]
        }
    }
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid","attr","valueStart","valueEnd"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    attr   = request.args.get("attr")
    valueStart   = request.args.get("valueStart")
    valueEnd   = request.args.get("valueEnd") 

    #查詢該ID是否存在
    thisIDexisted,sensorDict = retrieve_table(SYSTEM,sensor_raw_table)
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensor_raw_table

    try: 
        DbSessionRaw,_,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        sqlStr = 'SELECT column_name, data_type from information_schema.columns where table_name=\'{}\';'.format(senTableName)
        attrList = []
        attrFound = False

        for row in sessRaw.execute(sqlStr):
            attrList.append(row)
        attrDict = dict(attrList)

        for key, value in attrDict.items():
            if (attr == key):
                attrFound = True
                attrType = value

        if attrFound:
            recLast = []
            if attrType == "json":
                sqlStr = 'select * from "{}" where "{}" ::text between \'"{}"\' and \'"{}"\';'.format(senTableName,attr,valueStart,valueEnd)
            else:
                sqlStr = 'select * from "{}" where "{}" between \'{}\' and \'{}\';'.format(senTableName,attr,valueStart,valueEnd)

            for row in sessRaw.execute(sqlStr):
                drow = AdjustDataFormat().format(dict(row.items()))
                recLast.append(drow)

            dicRet['QueryTableData'] = recLast
            err_msg = "ok" 
        else:
            err_msg = "<{} {}>Unexpected error: Attribute name is not correct".format(request.method,request.path)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES" 

    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/2.0/myps/Sensor/Interval/<sensor_raw_table>'
# Definition:
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Interval/<sensor_raw_table>', methods = ['GET']), 
@SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Interval/<sensor_raw_table>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_multirows_v2(SYSTEM,sensor_raw_table):
    #{{{APIINFO
    """
    {
        "API_application":"提供查詢postgresql感測器資料內容的一個範圍，不經過mysql直接抓取postgresql",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sensor_raw_table":"感測器資料表名稱"},
        "API_parameters":{
            "uid":"使用者帳號",
            "attr":"資料屬性名稱",
            "valueStart":"欲查詢資料起始值",
            "valueEnd":"欲查詢資料終端值"
        },
        "API_message_parameters":{
            "QueryMultiRows":"JSON",
            "DB":"string"
        },
        "API_example":{
            "APIS": " GET /api/IOT/1.0/myps/Sensor/Interval/weight",
            "BytesTransferred": 265,
            "OperationTime": "0.044",
            "Response": "ok",
            "DB":"MYSQL+POSTGRES",
            "QueryMultiRows":[{"upload_at": "2019-07-03 16:00:00","weight": 0.1,"seq": 1}, {"upload_at": "2019-07-25 16:00:00", "weight": 0.003, "seq": 2}]
        }
    }
    """
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid","attr","valueStart","valueEnd"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    attr   = request.args.get("attr")
    valueStart   = request.args.get("valueStart")
    valueEnd   = request.args.get("valueEnd") 
    senTableName = sensor_raw_table

    #先去檢查Redis是否有此key:senTableName
    status,result = get_redis_sensor_IDKEY_ornot_create(SYSTEM,senTableName)
    if not status:
        dicRet["Response"] = result
        return jsonify( **dicRet)
    dbName = result

    try: 
        DbSessionRaw,_,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        sqlStr = 'SELECT column_name, data_type from information_schema.columns where table_name=\'{}\';'.format(senTableName)
        attrList = []
        attrFound = False

        for row in sessRaw.execute(sqlStr):
            attrList.append(row)
        attrDict = dict(attrList)

        for key, value in attrDict.items():
            if (attr == key):
                attrFound = True
                attrType = value

        if attrFound:
            recLast = []
            if attrType == "json":
                sqlStr = 'select * from "{}" where "{}" ::text between \'"{}"\' and \'"{}"\';'.format(senTableName,attr,valueStart,valueEnd)
            else:
                sqlStr = 'select * from "{}" where "{}" between \'{}\' and \'{}\';'.format(senTableName,attr,valueStart,valueEnd)

            for row in sessRaw.execute(sqlStr):
                drow = AdjustDataFormat().format(dict(row.items()))
                recLast.append(drow)

            dicRet['QueryTableData'] = recLast
            err_msg = "ok" 
        else:
            err_msg = "<{} {}>Unexpected error: Attribute name is not correct".format(request.method,request.path)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES" 

    return jsonify( **dicRet)
# }}}

#=======================================================
# select sql syntax to postgres
# FOR MYSQL+POSTGRES
#=======================================================
# {{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/SqlSyntax/<sensor_raw_table>', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/SqlSyntax/<sensor_raw_table>',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_sqlsyntax(SYSTEM,sensor_raw_table):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢sensor postgres資料表資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sensor_raw_table":"感測器資料表名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "precautions": {
                "注意事項":"where條件不支援json欄位",
                "注意事項2":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項3)",
                "注意事項3":{"where":{"combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]}},
                "注意事項4":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}"
            },
            "parameters":{
                "purpose":{"type":"String","requirement":"required","directions":"欲查詢select方式；只接受3種參數(query|query_or|query_like)","example":"query"},
                "fields":{"type":"Array","requirement":"required","directions":"查詢欄位名稱參數","example":"['id','name','z',......]"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；若是使用query_or，物件裡的value以array型態post，若有特殊or需求請看注意事項2,3,4","example":"{'key':'value',.....}"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','id','name','z',.....]"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，如需查詢所有資料使用['ALL'],若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；value只有「equal(=) | notequal(!=) | greater(>) | less(<)」這四種運算子，且key必須與where的key相同，使用purpose->query時，才需使用此參數，其他皆放''即可","example":"{key:'equal',...}"},
                "intervaltime":{"type":"Object","requirement":"required","directions":"查詢指定間段時間；key必為時間屬性欄位，value若只放1個字串系統會自動抓取該時間到系統現在時間區間資料，無需使用此參數放''即可","example":"{'key':['2020-07-09 15:55:55','2020-07-09 18:00:00']}"}
            },
            "example":[
                {
                    "purpose":"query",
                    "fields":["name","id"],
                    "where":{"id":1},
                    "limit":[0,5],
                    "symbols":{"id":"equal"},
                    "orderby":["desc","id"],
                    "intervaltime":""
                },
                {
                    "purpose":"query_like",
                    "fields":"",
                    "where":{"runcard_code":"test","project_id":1},
                    "orderby":"",
                    "limit":["ALL"],
                    "symbols":"",
                    "intervaltime":""
                },
                {
                    "purpose":"query_or",
                    "fields":"",
                    "where":{"id":[1,3,5],"created_at":["2020-06-09 17:30:16","2020-06-09 17:26:19"]},
                    "limit":"",
                    "symbols":"",
                    "orderby":"",
                    "intervaltime":""
                },
                {
                    "purpose":"query_or",
                    "fields":"",
                    "where":{"combine":[{"sensor_type":[0],"sensor_raw_table":["work_code_use","mould_series_no_use"]},{"sensor_type":[1],"sensor_raw_table":["f12","test"]}]},
                    "limit":"",
                    "symbols":"",
                    "orderby":"",
                    "intervaltime":""
                }
            ]
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " POST /api/IOT/1.0/myps/Sensor/SqlSyntax/workorderuse",
            "BytesTransferred": 50810,
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "user",
            "QueryTableData":[{
                "last_updatetime": "2018-11-07 16:49:40",
                "create_time": "2018-10-31 16:33:03",
                "uid":"e"
            }],
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    #查詢該ID是否存在
    thisIDexisted,sensorDict = retrieve_table(SYSTEM,sensor_raw_table)
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensor_raw_table

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    post_parameter = ["purpose","fields","where","orderby","limit","symbols","intervaltime"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    #post data 需要以下參數
    #Yishan 10072019 增加symbols，用於比較運算子，包含=(equal),!=(notequal),>(greater),<(less))
    parameter = ["purpose","fields","where","orderby","limit","symbols","intervaltime"]
    #post data 參數必須是以下型態
    parametertype = [unicode,list,dict,list,list,dict,dict]
    #若post data型態錯誤，返回message(轉換datatype格式)
    datatype = {unicode:"String",list:"Array",dict:"Object"}
    #if type error,return error and correct type,put in errpostdatatype
    errpostdatatype = []
    for i in range(len(parameter)):
        #不為""
        if reqdataDict.get(parameter[i]) != "":
            #檢查格式是否正確
            if not isinstance(reqdataDict.get(parameter[i]),parametertype[i]):
                err_msg = "Error type of \'{}\',it must be a {}".format(parameter[i],datatype[parametertype[i]])
                errpostdatatype.append(err_msg)
    #如果有errpostdatatype，表示格式有錯誤，返回error停止def
    if len(errpostdatatype) != 0:
        dicRet["Response"] = errpostdatatype
        return jsonify( **dicRet)

    purpose = reqdataDict.get("purpose").encode("utf8").strip()
    fields = reqdataDict.get("fields")
    where = reqdataDict.get("where")
    orderby = reqdataDict.get("orderby")
    limit = reqdataDict.get("limit")
    symbols = reqdataDict.get("symbols")
    intervaltime = reqdataDict.get("intervaltime")

    #Yishan@09122019 select methods
    #判斷是不是這3種參數 query|query_like|query_or
    if purpose != "query" and purpose != "query_like" and purpose != "query_or":
        if purpose == "":
            err_msg = "purpose can't Null"
        else:
            err_msg = "Error purpose : {}".format(purpose)
        dicRet["Response"] = err_msg
        return jsonify( **dicRet)

    recList = []
    try:
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()
    
        query_table = Table(senTableName , metaRaw, autoload=True)

        #desc table schema
        desc_table_status,fieldList,schemaDict,_ = _desc_table(SYSTEM,metaRaw,senTableName)
        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        #---------------------------------------------------------
        # field
        #---------------------------------------------------------
        #{{{
        fieldcolumnList = []
        if fields != "":
            if len(fields) == 0:
                dicRet["Response"] = "error parameter input {}, can't Null" .format(fields)
                return jsonify( **dicRet)

            #判斷fields是不是table的schema
            if len(fields) != len(list(set(fieldList).intersection(set(fields)))):
                fieldsnomatch = map(str,list(set(fields).difference(set(fieldList))))
                #如果difference()出來是空的，表示fields是符合schema但重複輸入，返回error
                if len(fieldsnomatch) != 0:
                    err_msg = "Unknown column \'{}\' in 'field list'".format(fieldsnomatch)
                else:
                    err_msg = "fields {} is duplicate".format(fields)
                dicRet["Response"] = err_msg
                return jsonify( **dicRet)
            else:
                fieldcolumnList = ["{}".format(getattr(query_table.c,fields[i]))for i in range(len(fields))]
                finalselect = text(",".join(fieldcolumnList))
        else:
            finalselect = query_table
        #}}}
        #---------------------------------------------------------
        # where
        #---------------------------------------------------------
        #{{{
        wheredictforqueryLike = {}
        wherelistforqueryLike = []
        wheredictforquery = {}
        whereorList = []
        wherecombineList = []

        if where != "":
            if len(where) == 0:
                dicRet["Response"] = "error parameter input {}, can't Null" .format(where)
                return jsonify( **dicRet)

            if purpose == "query":
                if symbols == "":
                    dicRet["Response"] = "error 'symbols' parameter input, can't Null"
                    return jsonify( **dicRet)
                else:
                    if len(symbols) != len(where):
                        dicRet["Response"] = "The number of {} data does not match {}" .format(symbols,where)
                        return jsonify( **dicRet)

            #比較運算子轉換
            operator = {"equal":"=","notequal":"!=","greater":">","less":"<"}
            operatorList = ["equal","notequal","greater","less"]
            #unicode dict change to str dict
            wheretoStrDict = ConvertData().convert(where)
            symbolstoStrDict = ConvertData().convert(symbols)
            #unicode dict change to str dict
            for key,value in wheretoStrDict.items():
                if key !="combine":
                    #判斷where進來的key是否與資料表欄位相符
                    if not key in fieldList:
                        dicRet["Response"] = "Unknown column \'{}\' in 'field list'".format(key)
                        return jsonify( **dicRet)

                    #判斷where進來的key是否為JSON欄位
                    if schemaDict[key] == "JSON": 
                        dicRet["Response"] = "where condition does not support json field '{}'".format(key)
                        return jsonify( **dicRet)

                #只有purpose為query_or時，value才能為list，否則return
                if purpose != "query_or" and isinstance(value,list):
                    dicRet["Response"] = "error type of input {}, it must be a string".format(value)
                    return jsonify( **dicRet)

                if purpose == "query_like":
                    #postgresql時間與數字欄位無法直接模糊查詢，需轉成::text才能查詢
                    if schemaDict[key] == "TIMESTAMP WITHOUT TIME ZONE" or schemaDict[key] == "INTEGER":
                        wherelistforqueryLike.append("{} ::text LIKE '%{}%'".format(key,value))
                    else:
                        wheredictforqueryLike[key] = "%{}%".format(value)
                elif purpose == "query_or":
                    if not isinstance(value,list):
                        dicRet["Response"] = "error type of input {}, it must be a list".format(value)
                        return jsonify( **dicRet)

                    if len(value) == 0:
                        dicRet["Response"] = "error 'where' parameter input {},can't be a Null Array".format(value)
                        return jsonify( **dicRet)

                    #判斷是否有使用combine參數
                    if key != "combine":
                        whereor = or_(*(getattr(query_table.c,key) == value[o]for o in range(len(value))))
                        whereorList.append(whereor)
                    else:
                        for i in value:
                            whereorcombineList = []
                            for combine_key,combine_value in i.items():
                                whereorcombine = or_(*(getattr(query_table.c,combine_key) == combine_value[o]for o in range(len(combine_value))))
                                whereorcombineList.append(whereorcombine)
                            else:
                                wherecombine = and_(*(ii for ii in whereorcombineList))
                            wherecombineList.append(wherecombine)
                else:
                    if symbolstoStrDict.get(key) is None:
                        dicRet["Response"] = "The symbol key \'{}\' does not match {}" .format(symbolstoStrDict.keys(),key)
                        return jsonify( **dicRet)

                    if not isinstance(symbolstoStrDict[key],str):
                        dicRet["Response"] = "error 'symbols value {}' parameter must be a string".format(symbolstoStrDict[key])
                        return jsonify( **dicRet)

                    if symbolstoStrDict[key] not in operatorList:
                        dicRet["Response"] = "error 'symbols' parameter input \'{}\', not in {}" .format(symbolstoStrDict[key],operatorList) 
                        return jsonify( **dicRet)

                    wheredictforquery[key] = [operator[symbolstoStrDict[key]],value]
        else:
            finalquerywhere = ""
        #}}}
        #---------------------------------------------------------
        # order by
        #---------------------------------------------------------
        #{{{
        errpostorderbyparameter = []
        orderbyAY = []
        orderbyDA = ""
        if orderby != "":
            if len(orderby) == 0:
                dicRet["Response"] = "error 'orderby' parameter input, can't Null"
                return jsonify( **dicRet)

            if str(orderby[0]) != "asc" and str(orderby[0]) != "desc":
                err_msg = "error 'orderby' parameter input \'{}\',must be asc or desc".format(orderby[0])
                errpostorderbyparameter.append(err_msg)
            else:
                orderbyDA = orderby[0]
                for i in range(1,len(orderby)):
                    if orderby[i] in fieldList:
                        orderbyAY.append(orderby[i])
                    else:
                        err_msg = "Unknown column \'{}\' in 'field list'".format(orderby[i])
                        errpostorderbyparameter.append(err_msg)
                    orderbyAY = ConvertData().convert(orderbyAY)

            if len(errpostorderbyparameter) != 0:
                dicRet["Response"] = errpostorderbyparameter
                return jsonify( **dicRet)

            #以fieldList與orderby[1]，intersection()比較有無相同，且數量是否相等
            if len(orderbyAY) != len(list(set(fieldList).intersection(set(orderbyAY)))):
                #如果difference()出來是空的，表示orderby是符合schema但重複輸入，返回error
                orderbynomatch = map(str,list(set(orderbyAY).difference(set(fieldList))))
                if len(orderbynomatch) != 0:
                    err_msg = "orderby fields {} does not existed".format(orderbynomatch)
                else:
                    err_msg = "orderby fields {} is duplicate".format(orderby)
                dicRet["Response"] = err_msg
                return jsonify( **dicRet)

            if orderbyDA == "desc":
                finalorderby = (getattr(query_table.c,orderbyAY[hh]).desc()for hh in range(len(orderbyAY)))
            else:
                finalorderby = (getattr(query_table.c,orderbyAY[hh]).asc()for hh in range(len(orderbyAY)))
        else:
            finalorderby = ""
        #}}}
        #---------------------------------------------------------
        # limit
        #---------------------------------------------------------
        #{{{
        if limit != "":
            #檢查post limit length是否為2
            if len(limit) == 2:
                #判斷limit[0],limit[1]皆為正整數，且[0]<[1]
                try:
                    if int(limit[0]) >= 0 and int(limit[1]) >= 0:
                        limitStart = int(limit[0])
                        limitEnd = int(limit[1])
                    else:
                        dicRet["Response"] = "limit number {} is must be a Positive Integer and limit[0] need smaller than limit[1]".format(limit)
                        return jsonify( **dicRet)

                except ValueError:
                    dicRet["Response"] = "limit number {} is must be a Positive Integer".format(limit)
                    return jsonify( **dicRet)

            else:
                if limit[0] != "ALL":
                    dicRet["Response"] = "error length of limit number {}".format(limit)
                    return jsonify( **dicRet)

                #欲查詢全部->0~99999999筆
                limitStart = 0
                limitEnd = 99999999
        else:
            limitStart = 0
            #若無限制預設查100筆
            limitEnd = 100
        #}}}
        #---------------------------------------------------------
        # intervaltime
        #---------------------------------------------------------
        #{{{
        wherentervaltime = {}
        if intervaltime != "":
            intervaltimetoStrDict = intervaltime
            for timekey,timevalue in intervaltimetoStrDict.items():
                if schemaDict[timekey] != "TIMESTAMP WITHOUT TIME ZONE":
                    dicRet["Response"] = "error 'intervaltime' parameter input '{}' schema is not TIMESTAMP or DATETIME".format(timekey)
                    return jsonify( **dicRet)
                
                if not isinstance(timevalue,list):
                    dicRet["Response"] = "error 'intervaltime' parameter input, '{}' it must be an Array".format(timevalue)
                    return jsonify( **dicRet)
                
                if timevalue[0] == "":
                    dicRet["Response"] = "error 'intervaltime' parameter input, can't Null"
                    return jsonify( **dicRet)

                #判斷timevalue[0],timevalue[1]皆為合法時間字串
                for timestr in timevalue:
                    if not VerifyDataStrLawyer(timestr).verify_date():
                        dicRet["Response"] = "error 'intervaltime' parameter input, date str '{}' is illegal".format(timestr)
                        return jsonify( **dicRet)

                #檢查post intervaltime timevalue length是否為2
                if len(timevalue) == 2:
                    if datetime.strptime(timevalue[1], "%Y-%m-%d %H:%M:%S") < datetime.strptime(timevalue[0], "%Y-%m-%d %H:%M:%S"):
                        dicRet["Response"] = "error 'intervaltime' parameter input, start date str '{}' need smaller than end date str '{}'".format(startdate,enddate)
                        return jsonify( **dicRet)

                    startdate = timevalue[0]
                    enddate = timevalue[1]
                else:
                    #欲查詢指定日期到今天
                    enddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')[::]
                    startdate = timevalue[0]

                wherentervaltime[timekey] = [startdate,enddate] 
        #}}}
        #---------------------------------------------------------
        # sess.execute(sqlStr)
        #---------------------------------------------------------
        if purpose == "query_like":
            finalquerywhere = and_(and_(*(text(wherelistforqueryLike[i])for i in range(len(wherelistforqueryLike)))),
                            and_(*((between(getattr(query_table.c,key),value[0],value[1]))for key,value in wherentervaltime.items())),
                            *((getattr(query_table.c,key).like(value))for key,value in wheredictforqueryLike.items())\
                        )

        elif purpose == "query_or":
            finalquerywhere =  and_(or_(*(i for i in wherecombineList)),
                                    and_(*(i for i in whereorList)),
                                    and_(*((between(getattr(query_table.c,key),value[0],value[1]))for key,value in wherentervaltime.items()))\
                                )
            #https://stackoverflow.com/questions/17006641/single-line-nested-for-loops
        else:
            finalquerywhere = and_(and_(*((between(getattr(query_table.c,key),value[0],value[1]))for key,value in wherentervaltime.items())),
                                *(case(
                                    [\
                                        (literal(value[0] == "="),getattr(query_table.c,key) == value[1]),
                                        (literal(value[0] == "!="),getattr(query_table.c,key) != value[1]),
                                        (literal(value[0] == ">"),getattr(query_table.c,key) > value[1]),
                                    ],\
                                    else_=getattr(query_table.c,key) < value[1]
                                )for key,value in wheredictforquery.items())\
                            )

        sqlStr = select([finalselect]).\
                    select_from(query_table).\
                    where(finalquerywhere).\
                    order_by(*finalorderby).\
                    limit(limitEnd).offset(limitStart)

        for row in sessRaw.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recList.append(drow)

        dicRet['QueryTableData'] = recList
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["Table"] = sensor_raw_table
    dicRet["DB"] = "MYSQL+POSTGRES" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# to set select sql syntax 
# FOR MYSQL+POSTGRES
#=======================================================
# {{{ SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/SqlSyntax', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/SqlSyntax',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_sqlsyntax_v2(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢sensor postgres資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "parameters":{
                "table":{"type":"String","requirement":"required","directions":"欲查詢的資料表名稱","example":"sensor"},
                "fields":{"type":"Array","requirement":"required","directions":"查詢欄位名稱參數","example":"['id','name','z',......]"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；物件中的key皆以and來查詢，物件裡的value皆以array型態post，若有特殊or需求請看注意事項5,6,7；若需使用子查詢請看注意事項8,9","example":"{'field':['value',....],.....}"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','id','name','z',.....]"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，如需查詢所有資料使用['ALL'],若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；物件裡的value皆以array型態post，value只有「equal(=) | notequal(!=) | greater(>) | less(<) | leftlike | notleftlike | like | notlike | rightlike | notrightlike | in | notin 」這12種運算子(此為預設運算子若有其他需求請看注意事項3、4)，且key必須與where的key相同，若使用有in的運算子其where value必須為陣列(其值都以and相連查詢)","example":"{key:['equal',....],...}"},
                "intervaltime":{"type":"Object","requirement":"required","directions":"查詢指定間段時間；key必為時間屬性欄位，value為陣列，陣列內有幾個時間條件陣列(格式為['起始時間','結束時間'])以or方式連接查詢，不同時間條件以and方式連接查詢；無需使用此參數放''即可","example":"{'created_at':[['2020-07-09 15:55:55','2020-07-09 18:00:00'],[],....],'updated_at':[['2020-07-28 10:00:00','2020-07-28 12:00:00'],[],...],....}"},
                "subquery":{"type":"Object","requirement":"required","directions":"子查詢條件；key必需與where條件的子查詢value對應，value為物件，即為一個新的SqlSyntax api，無需使用此參數放''即可","example":"{'condition_1':{'table':'sensor','fields':['id','name','noumenon_type','noumenon_id'],'where':{'sensor_raw_table':['f12','test'],'noumenon_id':[1]},'limit':'','symbols':{'sensor_raw_table':['equal','equal'],'noumenon_id':['equal']},'orderby':'','intervaltime':''}}"},
                "union":{"type":"Array","requirement":"required","directions":"聯合查詢條件；陣列只會有兩個值array[0]必須與parameters內的key相對應，array[1]為boolean，true代表(允許重複的值)，false則相反，無需使用此參數放''即可","example":"{'condition_2':true}"}
            },
            "precautions": {
                "注意事項1":"parameters內的固定格式key為：condition_x，其中的x為數字(1~x)，至少必須有condition_1；若有聯合查詢(UNION)，parameters內的key繼續往下新增",
                "注意事項2":"where value條件不支援json欄位但提供子查詢",
                "注意事項3":"symbols 同一個key條件中的所有運算子預設皆為or前一個value，若需指定or或and，直接_or或_and即可，example:in_or、equal_and...等，故此陣列內的value順序會影響where條件順序，詳例查看example11",
                "注意事項4":"symbols中的有關like、leftlike、rightlike這三種運算子皆可加in、notin，故可衍生出9種樣式，也能運用注意事項3的_or、_and。example:likein、leftlikenotin...等，詳例查看example11",
                "注意事項5":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項6)",
                "注意事項6":{"where":{"combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]}},
                "注意事項7":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}",
                "注意事項8":"where若有子查詢需求，value必須為subcondition_x,ex:({'where':{'key':['subcondition_1']},'symbol':{'key':['in']}})，詳例查看example4,5,6,7",
                "注意事項9":"where子查詢查詢回來的欄位必須只有一個",
                "注意事項10":"where子查詢的symbol只可以為['in'='in_and','notin'='notin_and','in_or','notin_or']",
                "注意事項11":"This version of MariaDB doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'",
                "注意事項12":"若有聯合查詢需求，可使用union參數，但須遵守：每個SELECT必須選擇相同的列數，相同數目的列表達式，相同的數據類型，並讓它們以相同的順序，但它們不必具有相同的長度，若有差異則以condition_1為主，詳例查看example8"
            },
            "example":[
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "sensor_raw_table":["f12","test"],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "sensor_raw_table":["equal","equal"],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":"",
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"sensor_type":[0],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":"",
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"push_msg_content",
                            "fields":"",
                            "where":"",
                            "limit":"",
                            "symbols":"",
                            "orderby":"",
                            "intervaltime":{
                                "timestamp":[["2020-07-28 09:00:00","2020-07-28 10:00:00"],["2020-07-28 13:00:00","2020-07-28 15:00:00"]],
                                "created_at":[["2020-07-28 09:00:00","2020-07-28 10:00:00"],["2020-07-28 13:00:00","2020-07-28 15:00:00"]]
                            }
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":["subcondition_1"],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":["in_and"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":{
                                "subcondition_1":
                                    {
                                        "table":"site",
                                        "fields":["site_id"],
                                        "where":{
                                            "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                            "site_id":[1]
                                        },
                                        "limit":"",
                                        "symbols":{
                                            "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                            "site_id":["equal"]
                                        },
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":"",
                                        "union":""
                                    }
                            },
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":["subcondition_1"],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":["subcondition_2"]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":["in_and"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}],
                                "noumenon_id":["in_and"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":{
                                "subcondition_1":
                                    {
                                        "table":"site",
                                        "fields":["site_id"],
                                        "where":{
                                            "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                            "site_id":[1]
                                        },
                                        "limit":"",
                                        "symbols":{
                                            "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                            "site_id":["equal"]
                                        },
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":"",
                                        "union":""
                                    },
                                "subcondition_2":
                                    {
                                        "table":"department",
                                        "fields":["department_id"],
                                        "where":"",
                                        "limit":"",
                                        "symbols":"",
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":"",
                                        "union":""
                                    }
                            },
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":["subcondition_1"],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":["in"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal]"]}],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":{
                                "subcondition_1":
                                    {
                                        "table":"site",
                                        "fields":["site_id"],
                                        "where":{
                                            "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                            "site_id":["subcondition_1"]
                                        },
                                        "limit":"",
                                        "symbols":{
                                            "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                            "site_id":["in"]
                                        },
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":{
                                            "subcondition_1":
                                                {
                                                    "table":"department",
                                                    "fields":["department_id"],
                                                    "where":"",
                                                    "limit":"",
                                                    "symbols":"",
                                                    "orderby":"",
                                                    "intervaltime":"",
                                                    "subquery":"",
                                                    "union":""
                                                }
                                        },
                                        "union":""
                                    }
                            },
                            "union":""
                        }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "creatorID": [
                                "subcondition_1"
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "creatorID": [
                                "in"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": {
                            "subcondition_1": {
                                "table": "user",
                                "fields": [
                                    "uID"
                                ],
                                "where": {
                                    "uID": [
                                        2493,
                                        2496
                                    ],
                                    "noumenonID": [
                                        "subcondition_1"
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "lastUpdateTime"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "uID": [
                                        "equal",
                                        "equal"
                                    ],
                                    "noumenonID": [
                                        "in"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": {
                                    "subcondition_1": {
                                        "table": "department",
                                        "fields": [
                                            "depID"
                                        ],
                                        "where": {
                                            "depID": [
                                                "1003"
                                            ]
                                        },
                                        "orderby": [
                                            "desc",
                                            "lastUpdateTime"
                                        ],
                                        "limit": [
                                            "ALL"
                                        ],
                                        "symbols": {
                                            "depID": [
                                                "equal"
                                            ]
                                        },
                                        "intervaltime": "",
                                        "subquery": ""
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": [
                            "condition_2",
                            true
                        ]
                    },
                    "condition_2": {
                        "table": "todoListComplt",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": ""
                    }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": [
                            "condition_2",
                            true
                        ]
                    },
                    "condition_2": {
                        "table": "todoListComplt",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ],
                            "creatorID": [
                                "subcondition_1"
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ],
                            "creatorID": [
                                "in"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": {
                            "subcondition_1": {
                                "table": "user",
                                "fields": ["uID"],
                                "where": {
                                    "uID": [
                                        2496
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "uID"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "uID": [
                                        "equal"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": "",
                                "union": ""
                            }
                        },
                        "union": ""
                    }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": [
                            "condition_2",
                            true
                        ]
                    },
                    "condition_2": {
                        "table": "todoListComplt",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ],
                            "creatorID": [
                                "subcondition_1"
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ],
                            "creatorID": [
                                "in"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": {
                            "subcondition_1": {
                                "table": "user",
                                "fields": [
                                    "creatorID"
                                ],
                                "where": {
                                    "creatorID": [
                                        2496
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "creatorID"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "creatorID": [
                                        "equal"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": "",
                                "union": [
                                    "condition_3",
                                    true
                                ]
                            },
                            "condition_3": {
                                "table": "department",
                                "fields": [
                                    "creatorID"
                                ],
                                "where": {
                                    "creatorID": [
                                        2496
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "creatorID"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "creatorID": [
                                        "equal"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": "",
                                "union": ""
                            }
                        },
                        "union": ""
                    }
                },
                {
                    "condition_1": {
                        "orderby": [
                            "asc",
                            "upload_at"
                        ],
                        "table": "runcard",
                        "fields": "",
                        "limit": [
                            "ALL"
                        ],
                        "intervaltime": "",
                        "union": "",
                        "subquery": {
                            "subcondition_1": {
                                "orderby": [
                                    "desc",
                                    "upload_at"
                                ],
                                "symbols": {
                                    "runcard_code": [
                                        "equal",
                                        "notrightlike"
                                    ],
                                    "device_name": [
                                        "notequal"
                                    ],
                                    "upload_at": [
                                        "equal",
                                        "likenotin"
                                    ]
                                },
                                "table": "runcard_thread_hist",
                                "fields": [
                                    "runcard_code"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "intervaltime": "",
                                "union": "",
                                "subquery": "",
                                "where": {
                                    "runcard_code": [
                                        "test",
                                        "F07109A0004"
                                    ],
                                    "device_name": [
                                        "R05"
                                    ],
                                    "upload_at": [
                                        "2020-12-18 11:23:58",
                                        [
                                            "2020-12-18 11:23:58",
                                            "2020-12-18 11:23:58"
                                        ]
                                    ]
                                }
                            }
                        },
                        "symbols": {
                            "project_id": [
                                "equal"
                            ],
                            "runcard_code": [
                                "equal_and",
                                "notin_or",
                                "like_and"
                            ],
                            "upload_at": [
                                "rightlikein"
                            ]
                        },
                        "where": {
                            "project_id": [
                                5
                            ],
                            "runcard_code": [
                                "F12109A0045-01",
                                "subcondition_1",
                                "F12109A0045"
                            ],
                            "upload_at": [
                                [
                                    "2020-12-17 11:23:58",
                                    "2020-12-17 11:23:58"
                                ]
                            ]
                        }
                    }
                }
            ]
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " POST /api/IOT/1.0/myps/Sensor/SqlSyntax",
            "BytesTransferred": 50810,
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "user",
            "QueryTableData":[{
                "updated_at": "2018-11-07 16:49:40",
                "created_at": "2018-10-31 16:33:03",
                "uid":"e"
            }],
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","getSqlSyntax"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)
    
    #至少要有condition_1
    if reqdataDict.get("condition_1") is None:
        dicRet["Response"] = "'request.data' missing key : 'condition_1'"
        return jsonify( **dicRet)
    
    #先查key:condition_1的條件
    action_status,action_result = ApiSqlsyntaxActions({"request_data":reqdataDict["condition_1"],"isjoin":False}).check_post_parameter()
    if not action_status:
        dicRet["Response"] = action_result
        return jsonify( **dicRet)
    
    #需要先檢查此sensor id是否存在並抓取dbName
    thisIDexisted,sensorDict = retrieve_table(SYSTEM,action_result["table"])
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)
    
    dbName = sensorDict["db_name"]
    
    try:
        DbSessionRaw,metaRaw,engineRaw= appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        sqlsyntax_actions_status,sqlsyntax_actions_result = sqlsyntax_params_actions(action_result, "condition_1", reqdataDict, sessRaw, metaRaw, "postgres", False, SYSTEM)
        if not sqlsyntax_actions_status:
            dicRet["Response"] = sqlsyntax_actions_result
            return jsonify( **dicRet)
        
        if request.args.get("getSqlSyntax") == "yes":
            dicRet['SqlSyntax'] = str(sqlsyntax_actions_result[1].compile(compile_kwargs={"literal_binds": True}))

        dicRet['QueryTableData'] = sqlsyntax_actions_result[0]
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# to set select sql syntax 
# FOR MYSQL+POSTGRES
#=======================================================
# {{{ SENSOR_API.route('/api/<SYSTEM>/2.5/myps/Sensor/SqlSyntax', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/2.5/myps/Sensor/SqlSyntax',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_qry_sqlsyntax_v2_5(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢sensor postgres資料表資料服務，不經過mysql直接抓取postgresql",
        "API_parameters":{"uid":"使用者帳號","dbName":"隸屬資料庫名稱","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "precautions": {
                "注意事項1":"parameters內的固定格式key為：condition_x，其中的x為數字(1~x)，至少必須有condition_1；若有聯合查詢(UNION)，parameters內的key繼續往下新增",
                "注意事項2":"where value條件不支援json欄位但提供子查詢",
                "注意事項3":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項3)",
                "注意事項4":{"where":{"combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]}},
                "注意事項5":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}",
                "注意事項6":"where若有子查詢需求，value必須為subcondition_x,ex:({'where':{'key':['subcondition_1']},'symbol':{'key':['in']}})，詳例查看example4,5,6,7",
                "注意事項7":"where子查詢查詢回來的欄位必須只有一個",
                "注意事項8":"where子查詢的symbol可以為['in'='in_and','notin'='notin_and','in_or','notin_or']",
                "注意事項9":"This version of MariaDB doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'",
                "注意事項10":"若有聯合查詢需求，可使用union參數，但須遵守：每個SELECT必須選擇相同的列數，相同數目的列表達式，相同的數據類型，並讓它們以相同的順序，但它們不必具有相同的長度，若有差異則以condition_1為主，詳例查看example8"
            },
            "parameters":{
                "table":{"type":"String","requirement":"required","directions":"欲查詢的資料表名稱","example":"sensor"},
                "fields":{"type":"Array","requirement":"required","directions":"查詢欄位名稱參數","example":"['id','name','z',......]"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；物件裡的value皆以array型態post(預設以query_or查詢)，若有特殊or需求請看注意事項3,4,5；若需使用子查詢請看注意事項6,7","example":"{'field':['value',....],.....}"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','id','name','z',.....]"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，如需查詢所有資料使用['ALL'],若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；物件裡的value皆以array型態post，value只有「equal(=) | notequal(!=) | greater(>) | less(<) | leftlike(left-like) | like(like) | rightlike(right-like) | in(in) | notin(notin)」這七種運算子，且key必須與where的key相同","example":"{key:['equal',....],...}"},
                "intervaltime":{"type":"Object","requirement":"required","directions":"查詢指定間段時間；key必為時間屬性欄位，value為陣列，陣列內有幾個時間條件陣列(格式為['起始時間','結束時間'])以or方式連接查詢，不同時間條件以and方式連接查詢；無需使用此參數放''即可","example":"{'created_at':[['2020-07-09 15:55:55','2020-07-09 18:00:00'],[],....],'updated_at':[['2020-07-28 10:00:00','2020-07-28 12:00:00'],[],...],....}"},
                "subquery":{"type":"Object","requirement":"required","directions":"子查詢條件；key必需與where條件的子查詢value對應，value為物件，即為一個新的SqlSyntax api，無需使用此參數放''即可","example":"{'condition_1':{'table':'sensor','fields':['id','name','noumenon_type','noumenon_id'],'where':{'sensor_raw_table':['f12','test'],'noumenon_id':[1]},'limit':'','symbols':{'sensor_raw_table':['equal','equal'],'noumenon_id':['equal']},'orderby':'','intervaltime':''}}"},
                "union":{"type":"Array","requirement":"required","directions":"聯合查詢條件；陣列只會有兩個值array[0]必須與parameters內的key相對應，array[1]為boolean，true代表(允許重複的值)，false則相反，無需使用此參數放''即可","example":"{'condition_2':true}"}
            },
            "example":[
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "sensor_raw_table":["f12","test"],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "sensor_raw_table":["equal","equal"],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":"",
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"sensor_type":[0],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":"",
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"push_msg_content",
                            "fields":"",
                            "where":"",
                            "limit":"",
                            "symbols":"",
                            "orderby":"",
                            "intervaltime":{
                                "timestamp":[["2020-07-28 09:00:00","2020-07-28 10:00:00"],["2020-07-28 13:00:00","2020-07-28 15:00:00"]],
                                "created_at":[["2020-07-28 09:00:00","2020-07-28 10:00:00"],["2020-07-28 13:00:00","2020-07-28 15:00:00"]]
                            }
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":["subcondition_1"],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":["in_and"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":{
                                "subcondition_1":
                                    {
                                        "table":"site",
                                        "fields":["site_id"],
                                        "where":{
                                            "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                            "site_id":[1]
                                        },
                                        "limit":"",
                                        "symbols":{
                                            "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                            "site_id":["equal"]
                                        },
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":"",
                                        "union":""
                                    }
                            },
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":["subcondition_1"],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":["subcondition_2"]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":["in_and"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}],
                                "noumenon_id":["in_and"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":{
                                "subcondition_1":
                                    {
                                        "table":"site",
                                        "fields":["site_id"],
                                        "where":{
                                            "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                            "site_id":[1]
                                        },
                                        "limit":"",
                                        "symbols":{
                                            "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                            "site_id":["equal"]
                                        },
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":"",
                                        "union":""
                                    },
                                "subcondition_2":
                                    {
                                        "table":"department",
                                        "fields":["department_id"],
                                        "where":"",
                                        "limit":"",
                                        "symbols":"",
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":"",
                                        "union":""
                                    }
                            },
                            "union":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":["subcondition_1"],"sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":["in"],"sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal]"]}],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":"",
                            "subquery":{
                                "subcondition_1":
                                    {
                                        "table":"site",
                                        "fields":["site_id"],
                                        "where":{
                                            "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                            "site_id":["subcondition_1"]
                                        },
                                        "limit":"",
                                        "symbols":{
                                            "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                            "site_id":["in"]
                                        },
                                        "orderby":"",
                                        "intervaltime":"",
                                        "subquery":{
                                            "subcondition_1":
                                                {
                                                    "table":"department",
                                                    "fields":["department_id"],
                                                    "where":"",
                                                    "limit":"",
                                                    "symbols":"",
                                                    "orderby":"",
                                                    "intervaltime":"",
                                                    "subquery":"",
                                                    "union":""
                                                }
                                        },
                                        "union":""
                                    }
                            },
                            "union":""
                        }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "creatorID": [
                                "subcondition_1"
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "creatorID": [
                                "in"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": {
                            "subcondition_1": {
                                "table": "user",
                                "fields": [
                                    "uID"
                                ],
                                "where": {
                                    "uID": [
                                        2493,
                                        2496
                                    ],
                                    "noumenonID": [
                                        "subcondition_1"
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "lastUpdateTime"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "uID": [
                                        "equal",
                                        "equal"
                                    ],
                                    "noumenonID": [
                                        "in"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": {
                                    "subcondition_1": {
                                        "table": "department",
                                        "fields": [
                                            "depID"
                                        ],
                                        "where": {
                                            "depID": [
                                                "1003"
                                            ]
                                        },
                                        "orderby": [
                                            "desc",
                                            "lastUpdateTime"
                                        ],
                                        "limit": [
                                            "ALL"
                                        ],
                                        "symbols": {
                                            "depID": [
                                                "equal"
                                            ]
                                        },
                                        "intervaltime": "",
                                        "subquery": ""
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": [
                            "condition_2",
                            true
                        ]
                    },
                    "condition_2": {
                        "table": "todoListComplt",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": ""
                    }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": [
                            "condition_2",
                            true
                        ]
                    },
                    "condition_2": {
                        "table": "todoListComplt",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ],
                            "creatorID": [
                                "subcondition_1"
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ],
                            "creatorID": [
                                "in"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": {
                            "subcondition_1": {
                                "table": "user",
                                "fields": ["uID"],
                                "where": {
                                    "uID": [
                                        2496
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "uID"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "uID": [
                                        "equal"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": "",
                                "union": ""
                            }
                        },
                        "union": ""
                    }
                },
                {
                    "condition_1": {
                        "table": "todoList",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": "",
                        "union": [
                            "condition_2",
                            true
                        ]
                    },
                    "condition_2": {
                        "table": "todoListComplt",
                        "fields": "",
                        "where": {
                            "assignTo": [
                                2493
                            ],
                            "creatorID": [
                                "subcondition_1"
                            ]
                        },
                        "orderby": [
                            "desc",
                            "seq"
                        ],
                        "limit": [
                            "ALL"
                        ],
                        "symbols": {
                            "assignTo": [
                                "equal"
                            ],
                            "creatorID": [
                                "in"
                            ]
                        },
                        "intervaltime": "",
                        "subquery": {
                            "subcondition_1": {
                                "table": "user",
                                "fields": [
                                    "creatorID"
                                ],
                                "where": {
                                    "creatorID": [
                                        2496
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "creatorID"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "creatorID": [
                                        "equal"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": "",
                                "union": [
                                    "condition_3",
                                    true
                                ]
                            },
                            "condition_3": {
                                "table": "department",
                                "fields": [
                                    "creatorID"
                                ],
                                "where": {
                                    "creatorID": [
                                        2496
                                    ]
                                },
                                "orderby": [
                                    "desc",
                                    "creatorID"
                                ],
                                "limit": [
                                    "ALL"
                                ],
                                "symbols": {
                                    "creatorID": [
                                        "equal"
                                    ]
                                },
                                "intervaltime": "",
                                "subquery": "",
                                "union": ""
                            }
                        },
                        "union": ""
                    }
                }
            ]
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " POST /api/IOT/2.5/myps/Sensor/SqlSyntax",
            "BytesTransferred": 50810,
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "user",
            "QueryTableData":[{
                "updated_at": "2018-11-07 16:49:40",
                "created_at": "2018-10-31 16:33:03",
                "uid":"e"
            }],
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","dbName","getSqlSyntax"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)
    
    #至少要有condition_1
    if reqdataDict.get("condition_1") is None:
        dicRet["Response"] = "'request.data' missing key : 'condition_1'"
        return jsonify( **dicRet)
    
    #先查key:condition_1的條件
    action_status,action_result = ApiSqlsyntaxActions({"request_data":reqdataDict["condition_1"],"isjoin":False}).check_post_parameter()
    if not action_status:
        dicRet["Response"] = action_result
        return jsonify( **dicRet)
    
    dbName  = request.args.get("dbName").encode('utf-8')
    try:
        DbSessionRaw,metaRaw,engineRaw= appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        sqlsyntax_actions_status,sqlsyntax_actions_result = sqlsyntax_params_actions(action_result, "condition_1", reqdataDict, sessRaw, metaRaw, "postgres", False, SYSTEM)
        if not sqlsyntax_actions_status:
            dicRet["Response"] = sqlsyntax_actions_result
            return jsonify( **dicRet)
        
        if request.args.get("getSqlSyntax") == "yes":
            dicRet['SqlSyntax'] = str(sqlsyntax_actions_result[1].compile(compile_kwargs={"literal_binds": True}))

        dicRet['QueryTableData'] = sqlsyntax_actions_result[0]
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# select sql syntax join
# FOR MYSQL+POSTGRES
#=======================================================
# {{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/SqlSyntax/JoinMultiTable', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def commonuse_qry_joinmultitable(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢postgres join資料表資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "precautions": {
                "注意事項1":"為避免多表join後有些欄位名稱一樣被覆蓋掉，系統統一將資料查詢結果回傳值的key訂為'table$column'",
                "注意事項2":"where條件與join條件不支援json欄位",
                "注意事項3":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項3)",
                "注意事項4":{"where":{"tablename":{"combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]}}},
                "注意事項5":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}"
            },
            "parameters":{
                "purpose":{"type":"String","requirement":"required","directions":"欲查詢select方式；只接受3種參數(query|query_or|query_like)","example":"query"},
                "fields":{"type":"Object","requirement":"required","directions":"查詢欄位名稱參數","example":"{'table':['table_column1','table_column2',....]}"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；若是使用query_or，物件裡的value以array型態post，若有特殊or需求請看注意事項3,4,5","example":"{'table':{'table_column':'value'},.....}"},
                "jointype":{"type":"String","requirement":"required","directions":"欲sql join方式(inner|left，只接受這2種參數)","example":"inner"},
                "join":{"type":"Object","requirement":"required","directions":"join多表表達式；最多只能有一個主表且若是使用left join，放入的順序會影響查詢結果","example":"{'主表':[{'欲JOIN的表(表1)':{'主表column1':'欲JOIN表的column1', '主表column2':'欲JOIN表的column2', 'JOIN':{'欲與表1JOIN的表(表2)':{'表1column':'表2cloumn'}}......}},.......]}"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，如需查詢所有資料使用['ALL'],若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；value只有「equal(=) | notequal(!=) | greater(>) | less(<)」這四種運算子，且key必須與where的key相同，使用purpose->query時，才需使用此參數，其他皆放''即可","example":"{'table':{'table_column':'equal'},.....}"},
                "tables":{"type":"Array","requirement":"required","directions":"需要join的所有資料表名稱","example":"['table1','table2',.....]"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','table','column','table2','column',.....]"}
            },
            "example":[
                {
                    "purpose":"query",
                    "fields":"",
                    "where":{"test":{"workid":"F12106A0048"} },
                    "join":{"workhour":[{"test":{"workid":"workid"} }]},
                    "jointype":"inner",
                    "limit":"",
                    "tables": ["workhour","test"],
                    "symbols":{"test":{"workid":"equal"} },
                    "orderby":""
                },
                {
                    "purpose":"query_like",
                    "fields":"",
                    "where":{"sensor":{"id":1} },
                    "join":{"site":[{"sensor":{"id":"noumenon_id"} }]},
                    "jointype":"inner",
                    "limit":"",
                    "tables": ["site","sensor"],
                    "symbols":"",
                    "orderby":""
                },
                {
                    "purpose":"query_or",
                    "fields":"",
                    "where":{"sensor":{"id":[1,3,5,7,12,13],"sensor_type":[1]} },
                    "join":{"site":[{"sensor":{"id":"noumenon_id"} }]},
                    "jointype":"inner",
                    "limit":"",
                    "tables": ["site","sensor"],
                    "symbols":"",
                    "orderby":""
                },
                {
                    "purpose":"query_or",
                    "fields":"",
                    "where":{"sensor":{"combine":[{"id":[1,12,13],"sensor_type":[1,0]}]} },
                    "join":{"site":[{"sensor":{"id":"noumenon_id"} }]},
                    "jointype":"inner",
                    "limit":"",
                    "tables": ["site","sensor"],
                    "symbols":"",
                    "orderby":""
                }
            ]
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " POST /api/IOT/1.0/myps/Sensor/query/SqlSyntax/JoinMultiTable",
            "BytesTransferred": 50810,
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "user",
            "QueryTableData":[{
                "last_updatetime": "2018-11-07 16:49:40",
                "create_time": "2018-10-31 16:33:03",
                "uid":"e"
            }],
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
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

    post_parameter = ["purpose","fields","where","join","jointype","limit","tables","symbols","orderby"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    #post data 需要以下參數
    #Yishan 10072019 增加symbols，用於比較運算子，包含=(equal),!=(notequal),>(greater),<(less))
    parameter = ["purpose","fields","where","join","jointype","limit","tables","symbols","orderby"]
    #post data 參數必須是以下型態
    parametertype = [unicode,dict,dict,dict,unicode,list,list,dict,list]
    #若post data型態錯誤，返回message(轉換datatype格式)
    datatype = {unicode:"String",list:"Array",dict:"Object"}
    #if type error,return error and correct type,put in errpostdatatype
    errpostdatatype = []
    for i in range(len(parameter)):
        #不為""
        if reqdataDict.get(parameter[i]) != "":
            #檢查格式是否正確
            if not isinstance(reqdataDict.get(parameter[i]),parametertype[i]):
                err_msg = "Error type of \'{}\',it must be a {}".format(parameter[i],datatype[parametertype[i]])
                errpostdatatype.append(err_msg)
    #如果有errpostdatatype，表示格式有錯誤，返回error停止def
    if len(errpostdatatype) != 0:
        dicRet["Response"] = errpostdatatype
        return jsonify( **dicRet)

    purpose = reqdataDict.get("purpose").encode("utf8").strip()
    fields = reqdataDict.get("fields")
    where = reqdataDict.get("where")
    join = reqdataDict.get("join")
    jointype = reqdataDict.get("jointype").encode("utf8").strip()
    limit = reqdataDict.get("limit")
    tables = reqdataDict.get("tables")
    symbols = reqdataDict.get("symbols")
    orderby = reqdataDict.get("orderby")

    #Yishan@09122019 select methods
    #判斷是不是這3種參數 query|query_like|query_or
    if purpose != "query" and purpose != "query_like" and purpose != "query_or":
        if purpose == "":
            err_msg = "'purpose' can't Null"
        else:
            err_msg = "Error 'purpose' : {}".format(purpose)
        dicRet["Response"] = err_msg
        return jsonify( **dicRet)

    recList = []
    try:
        dbName = 'iot'
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        try:
            DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
            if DbSession is None:
                #表示連接資料庫有問題
                dicRet["Response"] = engine
                return jsonify( **dicRet)
            
            sess = DbSession()

            #---------------------------------------------------------
            # tables
            #---------------------------------------------------------
            #{{{
            #check table existed or not
            if tables != "":
                if len(tables) < 2:
                    dicRet["Response"] = "至少要有兩個table"
                    return jsonify( **dicRet)

                for i in range(len(tables)):
                    table_existed,backmsg = _retrieve_senrawtable(sess,metadata,tables[i])
                    if not table_existed:
                        dicRet["Response"] = "Table {}".format(backmsg)
                        return jsonify( **dicRet)
            else:
                dicRet["Response"] = "'tables' parameter can't be Null"
                return jsonify( **dicRet)
            #}}}
            #---------------------------------------------------------
            # field
            #---------------------------------------------------------
            #{{{
            fieldcolumnList = []
            tempfieldcolumnList = []
            if fields != "":
                if len(fields) == 0:
                    dicRet["Response"] = "error 'fields' parameter input, can't Null"
                    return jsonify( **dicRet)

                for fieldskey,fieldsvalue in fields.items():
                    if not fieldskey in tables:
                        dicRet["Response"] = "error 'fields key {}' parameter input".format(fieldskey)
                        return jsonify( **dicRet)

                    _,sensorDict = _retrieve_senrawtable(sess,metadata,fieldskey)
                    dbName = sensorDict["db_name"]
                    senTableName = sensorDict["sensor_raw_table"]

                    desc_table_status,fieldList,_,_ = _desc_table(SYSTEM,metaRaw,senTableName)
                    if desc_table_status != 'ok':
                        dicRet["Response"] = desc_table_status
                        return jsonify( **dicRet)

                    fieldsvalueList = []
                    if isinstance(fieldsvalue,list):
                        fieldsvalueList = fieldsvalue
                    else:
                        fieldsvalueList.append(fieldsvalue)

                    if len(fieldsvalueList) != len(list(set(fieldList).intersection(set(fieldsvalueList)))):
                        fieldsnomatch = map(str,list(set(fieldsvalueList).difference(set(fieldList))))
                        #如果difference()出來是空的，表示fields是符合schema但重複輸入，返回error
                        if len(fieldsnomatch) != 0:
                            err_msg = "Unknown column \'{}\' in 'field list'".format(fieldsnomatch)
                        else:
                            err_msg = "fields {} is duplicate".format(fieldsvalueList)

                        dicRet["Response"] = err_msg
                        return jsonify( **dicRet)
                    else:
                        for i in range(len(fieldsvalueList)):
                            tempfieldcolumnList.append("{} AS {}".format(getattr(Table(fieldskey ,metaRaw, autoload=True).c,fieldsvalueList[i]),fieldskey+"$"+fieldsvalueList[i]))
                            fieldcolumnList.append("{}".format(getattr(Table(fieldskey ,metaRaw, autoload=True).c,fieldsvalueList[i])))
            else:
                for i in range(len(tables)):
                    desc_table_status,fieldList,_,_ = _desc_table(SYSTEM,metaRaw,tables[i])
                    if desc_table_status != 'ok':
                        dicRet["Response"] = desc_table_status
                        return jsonify( **dicRet)

                    for j in range(len(fieldList)):
                        tempfieldcolumnList.append("{} AS {}".format(getattr(Table(tables[i] ,metaRaw, autoload=True).c,fieldList[j]),tables[i]+"$"+fieldList[j]))
                        fieldcolumnList.append("{}".format(getattr(Table(tables[i] ,metaRaw, autoload=True).c,fieldList[j])))

            finalselect = text(",".join(tempfieldcolumnList))
            #}}}
            #---------------------------------------------------------
            # jointype
            #---------------------------------------------------------
            #{{{
            #Yishan@05082020 sql join types
            #判斷是不是這3種參數 inner|left
            if jointype != "inner" and jointype != "left":
                if jointype == "":
                    err_msg = "'jointype' can't Null"
                else:
                    err_msg = "Error 'jointype' : {}".format(jointype)
                dicRet["Response"] = err_msg
                return jsonify( **dicRet)
            
            if jointype == "inner":
                isouter = False
            else:                
                isouter = True
            #}}}
            #---------------------------------------------------------
            # join
            #---------------------------------------------------------
            #{{{
            joinkeyList = []
            joincolumnList = []
            if join == "":
                #join一定要有因為此api是為了給join table用的
                dicRet["Response"] = "'join' parameter can't be Null"
                return jsonify( **dicRet)

            join = ConvertData().convert(join)
            joinkeyList0 = join.keys()[0]
            if not isinstance(join[join.keys()[0]],list):
                #一定要用陣列包
                dicRet["Response"] = "Error type of '{}',it must be an Array".format(join[join.keys()[0]])
                return jsonify( **dicRet)

            for i in join[join.keys()[0]]:
                response, msg, key, value = adjust_dict_for_joinapi(metadata=metaRaw,tables=tables,masterKey=joinkeyList0,data=i,joinkeyList=joinkeyList,joincolumnList=joincolumnList,selectDB="postgres",system=SYSTEM)
                if not response:
                    dicRet["Response"] = msg
                    return jsonify( **dicRet)
            else:
                joinkeyList = key
                joincolumnList = value
            #}}}
            #---------------------------------------------------------
            # where
            #---------------------------------------------------------
            #{{{
            wheredictforquery = {}
            wherestrList = []

            if where != "":
                if len(where) == 0:
                    dicRet["Response"] = "error 'where' parameter input, can't Null"
                    return jsonify( **dicRet)
                    
                if purpose == "query":
                    if symbols == "":
                        dicRet["Response"] = "error 'symbols' parameter input, can't Null"
                        return jsonify( **dicRet)

                    if len(symbols) != len(where):
                        dicRet["Response"] = "The number of {} data does not match {}" .format(symbols,where)
                        return jsonify( **dicRet)

                #比較運算子轉換
                operator = {"equal":"=","notequal":"!=","greater":">","less":"<"}
                operatorList = ["equal","notequal","greater","less"]
                #unicode dict change to str dict
                wheretoStrDict = ConvertData().convert(where)
                symbolstoStrDict = ConvertData().convert(symbols)

                for wherekey,wherevalue in wheretoStrDict.items():
                    if not wherekey in tables:
                        dicRet["Response"] = "error 'where key {}' parameter input".format(wherekey)
                        return jsonify( **dicRet)

                    #desc table schema
                    _,sensorDict = _retrieve_senrawtable(sess,metadata,wherekey)
                    #dbName = Retrieve_dbName(sensorDict[0], sensorDict[1],selectDB="mysql")
                    dbName = sensorDict["db_name"]
                    senTableName = sensorDict["sensor_raw_table"]

                    desc_table_status,fieldList,schemaDict,_ = _desc_table(SYSTEM,metaRaw,senTableName)
                    if desc_table_status != 'ok':
                        dicRet["Response"] = desc_table_status
                        return jsonify( **dicRet)

                    for wherevalue_key,wherevalue_value in wherevalue.items():
                        if wherevalue_key != "combine":
                            if not wherevalue_key in fieldList:
                                dicRet["Response"] = "Unknown column \'{}\' in 'where value dist'".format(wherevalue_key)
                                return jsonify( **dicRet)
                            
                            if schemaDict[wherevalue_key] == "JSON": 
                                dicRet["Response"] = "where condition does not support table : '{}' -> json field '{}'".format(wherekey,wherevalue_key)
                                return jsonify( **dicRet)

                        #只有purpose為query_or時，value len才能>1，否則return
                        if purpose != "query_or" and isinstance(wherevalue_value,list):
                            dicRet["Response"] = "error type of input {}, the 'purpose' is not 'query_or',it must be a string".format(wherevalue_value)
                            return jsonify( **dicRet)

                        if purpose == "query_like":
                            wherestrList.append("{} ::text LIKE '%{}%'".format(getattr(Table(wherekey ,metaRaw, autoload=True).c,wherevalue_key),wherevalue_value))
                        elif purpose == "query_or":
                            if not isinstance(wherevalue_value,list):
                                dicRet["Response"] = "error type of input {}, it must be a list".format(wherevalue_value)
                                return jsonify( **dicRet)
                            
                            if len(wherevalue_value) == 0:
                                dicRet["Response"] = "error 'where' parameter input {},can't be a Null Array".format(wherevalue_value)
                                return jsonify( **dicRet)

                            #判斷是否有使用combine參數
                            if wherevalue_key != "combine":
                                wheredictforquery[wherevalue_key] = ["{} = '{}'".format(getattr(Table(wherekey ,metaRaw, autoload=True).c,wherevalue_key),wherevalue_value[o])for o in range(len(wherevalue_value))]
                            else:
                                for i in wherevalue_value:
                                    for combine_key,combine_value in i.items():
                                        wheredictforquery[combine_key] = ["{} = '{}'".format(getattr(Table(wherekey ,metadata, autoload=True).c,combine_key),combine_value[o])for o in range(len(combine_value))]
                        else:
                            if symbolstoStrDict.get(wherekey) is None:
                                dicRet["Response"] = "The symbol key \'{}\' does not match {}" .format(symbolstoStrDict.keys(),wheretoStrDict.keys())
                                return jsonify( **dicRet)

                            if not isinstance(symbolstoStrDict[wherekey],dict):
                                dicRet["Response"] = "error 'symbols value : {}' parameter input , must be an Object".format(symbolstoStrDict[wherekey])
                                return jsonify( **dicRet)

                            if symbolstoStrDict[wherekey].get(wherevalue_key) is None:
                                dicRet["Response"] = "The symbol value \'{}\' does not match {}" .format(symbolstoStrDict[wherekey],wherevalue)
                                return jsonify( **dicRet)

                            if not isinstance(symbolstoStrDict[wherekey][wherevalue_key],str):
                                dicRet["Response"] = "error 'symbols value {}' parameter must be a string".format(symbolstoStrDict[wherekey][wherevalue_key])
                                return jsonify( **dicRet)
                                
                            if symbolstoStrDict[wherekey][wherevalue_key] not in operatorList:
                                dicRet["Response"] = "error 'symbols' parameter input \'{}\', not in {}" .format(symbolstoStrDict[wherekey][wherevalue_key],operatorList) 
                                return jsonify( **dicRet)

                            wherestrList.append("{} {} '{}'".format(getattr(Table(wherekey ,metaRaw, autoload=True).c,wherevalue_key),operator[symbolstoStrDict[wherekey][wherevalue_key]],wherevalue_value))
            else:
                finalquerywhere = ""
            #}}}
            #---------------------------------------------------------
            # orderby
            #---------------------------------------------------------
            #{{{
            errpostorderbyparameter = []
            orderbytableList = []
            orderbycolumnList = []
            orderbyTCdist = {}
            orderbyDA = ""
            checkorderbycolumnduplicate = []
            if orderby != "":
                if len(orderby) == 0:
                    dicRet["Response"] = "error 'orderby' parameter input, can't Null"
                    return jsonify( **dicRet)

                if str(orderby[0]) != "asc" and str(orderby[0]) != "desc":
                    dicRet["Response"] = "error 'orderby' parameter input \'{}\',must be asc or desc".format(orderby[0])
                    return jsonify( **dicRet)

                #先判斷orderby list是否為奇數陣列
                if len(orderby) % 2 != 1:
                    dicRet["Response"] = "error 'orderby' parameter input {}, must be an odd array" .format(orderby)
                    return jsonify( **dicRet)

                orderbyDA = orderby[0]
                for i in range(1,len(orderby)):
                    if i % 2 == 1:
                        #利用dict來檢查post的column有無重複
                        if orderby[i] not in orderbyTCdist.keys():
                            orderbyTCdist[orderby[i]] = []
                        orderbyTCdist[orderby[i]].append(orderby[i+1])

                        #檢查post data是否與fields相符
                        orderbyTC = orderby[i]+"."+orderby[i+1]
                        if orderbyTC not in fieldcolumnList:
                            err_msg = "Unknown column \'{}\' in 'field list'".format(orderbyTC)
                            errpostorderbyparameter.append(err_msg)

                        #檢查table name是否存在
                        if orderby[i] in tables:
                            orderbytableList.append(orderby[i])
                        else:
                            err_msg = "table \'{}\' doesn't existed".format(orderby[i])
                            errpostorderbyparameter.append(err_msg)
                    else:
                        _,sensorDict = _retrieve_senrawtable(sess,metadata,orderby[i-1])
                        dbName = sensorDict["db_name"]
                        senTableName = sensorDict["sensor_raw_table"]

                        desc_table_status,fieldList,schemaDict,_ = _desc_table(SYSTEM,metaRaw,senTableName)
                        if desc_table_status != 'ok':
                            dicRet["Response"] = desc_table_status
                            return jsonify( **dicRet)

                        if orderby[i] in fieldList:
                            orderbycolumnList.append(orderby[i])
                        else:
                            err_msg = "Unknown column \'{}\' in 'field list'".format(orderby[i])
                            errpostorderbyparameter.append(err_msg)

                if len(errpostorderbyparameter) != 0:
                    dicRet["Response"] = errpostorderbyparameter
                    return jsonify( **dicRet)

                from collections import Counter   #Yishan 11062019 引入Counter來找出list
                for key,value in orderbyTCdist.items():
                    checkduplicatecolumndict = dict(Counter(value))
                    checkorderbycolumnduplicate = [key for key2,value2 in checkduplicatecolumndict.items()if value2 > 1]
                if len(checkorderbycolumnduplicate) != 0:
                    dicRet["Response"] = "orderby fields {} is duplicate".format(orderbycolumnList)
                    return jsonify( **dicRet)

                if orderbyDA == "desc":
                    finalorderby = (getattr(Table(orderbytableList[hh] ,metaRaw, autoload=True).c,orderbycolumnList[hh]).desc()for hh in range(len(orderbytableList)))
                else:
                    finalorderby = (getattr(Table(orderbytableList[hh] ,metaRaw, autoload=True).c,orderbycolumnList[hh]).asc()for hh in range(len(orderbytableList)))
            else:
                finalorderby = ""
            #}}}
            #---------------------------------------------------------
            # limit
            #---------------------------------------------------------
            #{{{
            if limit != "":
                #檢查post limit length是否為2
                if len(limit) == 2:
                    #判斷limit[0],limit[1]皆為正整數，且[0]<[1]
                    try:
                        if int(limit[0]) >= 0 and int(limit[1]) >= 0:
                            limitStart = int(limit[0])
                            limitEnd = int(limit[1])
                        else:
                            dicRet["Response"] = "limit number {} is must be a Positive Integer and limit[0] need smaller than limit[1]".format(limit)
                            return jsonify( **dicRet)

                    except ValueError:
                        dicRet["Response"] = "limit number {} is must be a Positive Integer".format(limit)
                        return jsonify( **dicRet)

                else:
                    dicRet["Response"] = "error length of limit number {}".format(limit)
                    return jsonify( **dicRet)

            else:
                limitStart = 0
                #若無限制預設查1000筆
                limitEnd = 1000
            #}}}

        except Exception as e:
            result = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

        finally:
            if 'DbSession' in locals().keys() and DbSession is not None:
                sess.close()
                DbSession.remove()
                engine.dispose()

        #---------------------------------------------------------
        # sess.execute(sqlStr)
        #---------------------------------------------------------
        wherejoinSql = Table(joinkeyList0 ,metaRaw, autoload=True)
        setjump = 0
        for i in range(len(joinkeyList)):
            if not isinstance(joinkeyList[i],list):
                if not isinstance(joincolumnList[setjump],list):
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i] ,metadata, autoload=True), \
                            getattr(Table(joinkeyList0 ,metadata, autoload=True).c,joincolumnList[setjump]) == \
                            getattr(Table(joinkeyList[i] ,metadata, autoload=True).c,joincolumnList[1+setjump]),isouter=isouter)
                    setjump += 2
                else:
                    joinandsql = and_(*(((getattr(Table(joinkeyList0 ,metadata, autoload=True).c,joincolumnList[setjump][u]) == \
                            getattr(Table(joinkeyList[i],metadata, autoload=True).c,joincolumnList[setjump][u+1])))for u in range(0,len(joincolumnList[setjump]),2)))
                    setjump += 1
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i] ,metadata, autoload=True),joinandsql,isouter=isouter)
            else:
                if not isinstance(joincolumnList[setjump],list):
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i][1] ,metadata, autoload=True), \
                            getattr(Table(joinkeyList[i][0],metadata, autoload=True).c,joincolumnList[setjump]) == \
                            getattr(Table(joinkeyList[i][1] ,metadata, autoload=True).c,joincolumnList[1+setjump]),isouter=isouter)
                    setjump += 2
                else:
                    joinandsql = and_(*(((getattr(Table(joinkeyList[i][0] ,metadata, autoload=True).c,joincolumnList[setjump][u]) == \
                            getattr(Table(joinkeyList[i][1],metadata, autoload=True).c,joincolumnList[setjump][u+1])))for u in range(0,len(joincolumnList[setjump]),2)))
                    setjump += 1
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i][1] ,metadata, autoload=True),joinandsql,isouter=isouter)

        #Yishan 11042019 檢查finalquerywhere是否定義，若沒使用where，finalquerywhere會先定義為""，此時需加上wherejoinSql
        if 'finalquerywhere' in locals().keys():
            finalquerywhere = wherejoinSql
            
        if purpose == "query_or":
            for key,value in wheredictforquery.items():
                if 'finalquerywhere' not in locals().keys():
                    finalquerywhere =  and_(or_(*(text(i) for i in value)))
                else:
                    finalquerywhere =  and_(finalquerywhere,or_(*(text(i) for i in value)))
            #https://stackoverflow.com/questions/17006641/single-line-nested-for-loops
        else:
            finalquerywhere = and_(\
                                *(text(i)for i in wherestrList)\
                            )

        sqlStr = select([finalselect]).\
                    select_from(wherejoinSql).\
                    where(finalquerywhere).\
                    order_by(*finalorderby).\
                    limit(limitEnd).offset(limitStart)

        for row in sessRaw.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recList.append(drow)

        dicRet['QueryTableData'] = recList
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# to set select sql syntax join
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ @COMMONUSE_IOT_API.route('/api/<SYSTEM>/2.0/myps/Sensor/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def commonuse_qry_joinmultitable_v2(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢postgresql join資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "parameters":{
                "fields":{"type":"Object","requirement":"required","directions":"查詢欄位名稱參數","example":"{'table':['table_column1','table_column2',....]}"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；物件中的key皆以and來查詢，物件裡的value皆以array型態post；若有特殊or需求請看注意事項5,6,7；可為null","example":"{'table':{'table_column':['value',....],...},.....}"},
                "jointype":{"type":"Object","requirement":"required","directions":"欲sql join方式，key為'主表'_'欲JOIN的表(表1)'，value有「inner｜left」，這2種參數","example":{"site_sensor":"left","sensor_place":"inner","site_user":"inner"}},
                "join":{"type":"Object","requirement":"required","directions":"join多表表達式；最多只能有一個主表；可為null(請查看注意事項8)","example":"{'主表':[{'欲JOIN的表(表1)':{'主表column1':'欲JOIN表的column1', '主表column2':'欲JOIN表的column2', 'JOIN':{'欲與表1JOIN的表(表2)':{'表1column':'表2cloumn'}}......}},.......]}"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；物件裡的value皆以array型態post，value只有「equal(=) | notequal(!=) | greater(>) | less(<) | leftlike | notleftlike | like | notlike | rightlike | notrightlike | in | notin 」這12種運算子(此為預設運算子若有其他需求請看注意事項3、4)，且key必須與where的key相同，若使用有in的運算子其where value必須為陣列(其值都以and相連查詢)","example":"{'table':{'table_column':['equal',...],...},.....}"},
                "tables":{"type":"Array","requirement":"required","directions":"需要join的所有資料表名稱","example":"['table1','table2',.....]"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','table','column','table2','column',.....]"},
                "subquery":{"type":"Object","requirement":"required","directions":"子查詢條件；key必需與where條件的子查詢value對應，value為物件，即為一個新的SqlSyntax api，無需使用此參數放''即可","example":"{'condition_1':{'table':'sensor','fields':['id','name','noumenon_type','noumenon_id'],'where':{'sensor_raw_table':['f12','test'],'noumenon_id':[1]},'limit':'','symbols':{'sensor_raw_table':['equal','equal'],'noumenon_id':['equal']},'orderby':'','intervaltime':''}}"}
            },
            "precautions": {
                "注意事項1":"為避免多表join後有些欄位名稱一樣被覆蓋掉，系統統一將資料查詢結果回傳值的key訂為'table$column'",
                "注意事項2":"where條件與join條件不支援json欄位",
                "注意事項3":"symbols 同一個key條件中的所有運算子預設皆為or前一個value，若需指定or或and，直接_or或_and即可，example:in_or、equal_and...等，故此陣列內的value順序會影響where條件順序，詳例查看example11",
                "注意事項4":"symbols中的有關like、leftlike、rightlike這三種運算子皆可加in、notin，故可衍生出9種樣式，也能運用注意事項3的_or、_and。example:likein、leftlikenotin...等，詳例查看example3",
                "注意事項5":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項6)",
                "注意事項6":{
                    "where":{
                        "tablename":{
                            "combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]
                        }
                    }
                },
                "注意事項7":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}",
                "注意事項8":"開放'join'參數可為null，若為null時系統會自動抓'tables'參數的第一個值當值主表查詢",
                "注意事項9":"where若有子查詢需求，value必須為subcondition_x,ex:({'where':{'key':['subcondition_1']},'symbol':{'key':['in']}})",
                "注意事項10":"where子查詢查詢回來的欄位必須只有一個",
                "注意事項11":"where子查詢的symbol可以為['in'='in_and','notin'='notin_and','in_or','notin_or']",
                "注意事項12":"This version of MariaDB doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery"
            },
            "example":[
                {
                    "condition_1": {
                        "fields": {
                            "user": [
                                "uID",
                                "uName",
                                "email"
                            ],
                            "todoList": [
                                "depID",
                                "taskInfo",
                                "taskDetail",
                                "startDate",
                                "creatorID"
                            ]
                        },
                        "where": {
                            "todoList": {
                                "depID": [
                                    1003
                                ],
                                "assignTo": [
                                    2493
                                ],
                                "creatorID": [
                                    "subcondition_1"
                                ]
                            }
                        },
                        "join": {
                            "todoList": [
                                {
                                    "user": {
                                        "assignTo": "uID"
                                    }
                                }
                            ]
                        },
                        "jointype": {
                            "todoList_user": "inner"
                        },
                        "limit": "",
                        "tables": [
                            "todoList",
                            "user"
                        ],
                        "symbols": {
                            "todoList": {
                                "depID": [
                                    "equal"
                                ],
                                "assignTo": [
                                    "equal"
                                ],
                                "creatorID": [
                                    "in"
                                ]
                            }
                        },
                        "orderby": "",
                        "subquery": {
                            "subcondition_1": {
                                "fields": {
                                    "user": [
                                        "uID"
                                    ]
                                },
                                "where": {
                                    "department": {
                                        "depID": [
                                            1003
                                        ]
                                    }
                                },
                                "join": {
                                    "department": [
                                        {
                                            "user": {
                                                "depID": "noumenonID"
                                            }
                                        }
                                    ]
                                },
                                "jointype": {
                                    "department_user": "inner"
                                },
                                "limit": "",
                                "tables": [
                                    "department",
                                    "user"
                                ],
                                "symbols": {
                                    "department": {
                                        "depID": [
                                            "equal"
                                        ]
                                    }
                                },
                                "orderby": "",
                                "subquery": ""
                            }
                        }
                    }
                },
                {
                    "condition_1":
                        {
                            "fields":{"sensor":["id","name","noumenon_type","noumenon_id","sensor_type"],"site":["name","db_name"]},
                            "where":{"sensor":{"combine":[{"id":[1,12,13],"sensor_type":[1]}],"noumenon_id":[1,2]}},
                            "join":{
                                "site":[
                                    {
                                        "sensor":{"site_id":"noumenon_id"}
                                    }
                                ]
                            },
                            "jointype":{
                                "site_sensor":"inner",
                                "sensor_place":"inner",
                                "site_user":"inner"
                            },
                            "limit":"",
                            "tables": ["site","sensor","user","place"],
                            "symbols":{"sensor":{"combine":[{"id":["equal","equal","equal"],"sensor_type":["equal"]}],"noumenon_id":["equal","equal"]}},
                            "orderby":""
                        }
                },
                {
                    "condition_1": {
                        "orderby": [
                            "desc",
                            "work_order",
                            "update_at"
                        ],
                        "symbols": {
                            "v_cd_sp": {
                                "mld_json": [
                                    "notequal"
                                ],
                                "mld_org_json": [
                                    "notequal"
                                ]
                            },
                            "work_order": {
                                "device_name": [
                                    "likenotin","equal_and"
                                ],
                                "status": [
                                    "notequal"
                                ],
                                "wire_code": [
                                    "equal"
                                ],
                                "attributes": [
                                    "equal"
                                ]
                            }
                        },
                        "join": {
                            "v_cd_sp": [
                                {
                                    "work_order": {
                                        "org_code": "commodity_code"
                                    }
                                }
                            ]
                        },
                        "tables": [
                            "v_cd_sp",
                            "work_order"
                        ],
                        "fields": {
                            "v_cd_sp": [
                                "mld_json",
                                "mld_org_json"
                            ],
                            "work_order": [
                                "code",
                                "device_name",
                                "update_at",
                                "status",
                                "wire_code",
                                "attributes"
                            ]
                        },
                        "jointype": {
                            "v_cd_sp_work_order": "inner"
                        },
                        "subquery": "",
                        "limit": "",
                        "where": {
                            "v_cd_sp": {
                                "mld_json": [
                                    null
                                ],
                                "mld_org_json": [
                                    null
                                ]
                            },
                            "work_order": {
                                "device_name": [
                                    ["F12","F12","F12","F12"],"F11"
                                ],
                                "status": [
                                    "1"
                                ],
                                "wire_code": [
                                    "B33M077805"
                                ],
                                "attributes": [
                                    "一般派工"
                                ]
                            }
                        }
                    }
                }
            ]
        },
        "API_message_parameters":{"QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": "POST /api/IOT/2.0/myps/Sensor/SqlSyntax/JoinMultiTable",
            "OperationTime": "0.298",
            "BytesTransferred": 353,
            "DB": "MYSQL+POSTGRESQL",
            "System": "IOT",
            "QueryTableData": [
                {
                    "wire_box$wire_diameter": "4.8",
                    "wire_warehousing_dtl$rack_wgt": 30.0,
                    "wire_warehousing_dtl$doc_no": "WE_I201910071_002",
                    "wire_box$wire_material": "SCM435",
                    "wire_warehousing_dtl$manufacturer": "邢台鋼鐵"
                }
            ],
            "Response": "ok"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","getSqlSyntax"]
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
    
    #至少要有condition_1
    if reqdataDict.get("condition_1") is None:
        dicRet["Response"] = "'request.data' missing key : 'condition_1'"
        return jsonify( **dicRet)
    
    #先查key:condition_1的條件
    action_status,action_result = ApiSqlsyntaxActions({"request_data":reqdataDict["condition_1"],"isjoin":True}).check_post_parameter()
    if not action_status:
        dicRet["Response"] = action_result
        return jsonify( **dicRet)

    recList = []
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()
    
        tables = action_result["tables"]
        #---------------------------------------------------------
        # tables
        #---------------------------------------------------------
        #{{{
        #check table existed or not
        checkdbnameList = []
        if tables != "":
            if len(tables) < 2:
                dicRet["Response"] = "至少要有兩個table"
                return jsonify( **dicRet)

            for i in range(len(tables)):
                table_existed,sensorDict = _retrieve_senrawtable(sess,metadata,tables[i])
                if not table_existed:
                    dicRet["Response"] = "Table {}".format(sensorDict)
                    return jsonify( **dicRet)
                
                if sensorDict["db_name"] not in checkdbnameList:
                    checkdbnameList.append(sensorDict["db_name"])
            else:
                if len(checkdbnameList) > 1:
                    dicRet["Response"] = "不同資料庫無法join"
                    return jsonify( **dicRet)
        else:
            dicRet["Response"] = "'tables' parameter can't be Null"
            return jsonify( **dicRet)
        #}}}

        try:
            dbName = checkdbnameList[0]
            DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
            if DbSessionRaw is None:
                #表示連接資料庫有問題
                dicRet["Response"] = engineRaw
                return jsonify( **dicRet)
            
            sessRaw = DbSessionRaw()

            sqlsyntax_actions_status,sqlsyntax_actions_result = join_sqlsyntax_params_actions(action_result,int("condition_1".split("_")[1]),reqdataDict,sessRaw,metaRaw,"postgres",True,SYSTEM)
            if not sqlsyntax_actions_status:
                dicRet["Response"] = sqlsyntax_actions_result
                return jsonify( **dicRet)

            if request.args.get("getSqlSyntax") == "yes":
                dicRet['SqlSyntax'] = str(sqlsyntax_actions_result[1].compile(compile_kwargs={"literal_binds": True}))

            dicRet['QueryTableData'] = sqlsyntax_actions_result[0]
            err_msg = "ok" #done successfully
        
        except Exception as e:
            err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

        finally:
            if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
                sessRaw.close()
                DbSessionRaw.remove()
                engineRaw.dispose()

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRESQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# to set select sql syntax join
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ @COMMONUSE_IOT_API.route('/api/<SYSTEM>/2.5/myps/Sensor/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@SENSOR_API.route('/api/<SYSTEM>/2.5/myps/Sensor/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def commonuse_qry_joinmultitable_v2_5(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢postgresql join資料表資料服務，不經過mysql直接抓取postgresql",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_parameters":{"uid":"使用者帳號","dbName":"隸屬資料庫名稱","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "parameters":{
                "fields":{"type":"Object","requirement":"required","directions":"查詢欄位名稱參數","example":"{'table':['table_column1','table_column2',....]}"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；物件裡的value皆以array型態post；若有特殊or需求請看注意事項3,4,5；可為null","example":"{'table':{'table_column':['value',....],...},.....}"},
                "jointype":{"type":"Object","requirement":"required","directions":"欲sql join方式，key為'主表'_'欲JOIN的表(表1)'，value有「inner｜left」，這2種參數","example":{"site_sensor":"left","sensor_place":"inner","site_user":"inner"}},
                "join":{"type":"Object","requirement":"required","directions":"join多表表達式；最多只能有一個主表；可為null(請查看注意事項6)","example":"{'主表':[{'欲JOIN的表(表1)':{'主表column1':'欲JOIN表的column1', '主表column2':'欲JOIN表的column2', 'JOIN':{'欲與表1JOIN的表(表2)':{'表1column':'表2cloumn'}}......}},.......]}"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；物件裡的value皆以array型態post，value只有「equal(=) | notequal(!=) | greater(>) | less(<) | leftlike(left-like) | like(like) | rightlike(right-like) | in(in) | notin(notin)」這七種運算子，且key必須與where的key相同","example":"{'table':{'table_column':['equal',...],...},.....}"},
                "tables":{"type":"Array","requirement":"required","directions":"需要join的所有資料表名稱","example":"['table1','table2',.....]"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','table','column','table2','column',.....]"}
            },
            "precautions": {
                "注意事項1":"為避免多表join後有些欄位名稱一樣被覆蓋掉，系統統一將資料查詢結果回傳值的key訂為'table$column'",
                "注意事項2":"where條件與join條件不支援json欄位",
                "注意事項3":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項3)",
                "注意事項4":{
                    "where":{
                        "tablename":{
                            "combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]
                        }
                    }
                },
                "注意事項5":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}",
                "注意事項6":"開放'join'參數可為null，若為null時系統會自動抓'tables'參數的第一個值當值主表查詢"
            },
            "example":[
                {
                    "condition_1":
                    {
                        "fields":"",
                        "where":{"workhour":{"work_code":["F1210950022"]} },
                        "join":{"workhour":[{"runcard":{"project_id":"project_id"} }]},
                        "jointype":{
                            "workhour_runcard":"inner"
                        },
                        "limit":"",
                        "tables": ["workhour","runcard"],
                        "symbols":{"workhour":{"work_code":["equal"]} },
                        "orderby":""
                    }
                }
            ]
        },
        "API_message_parameters":{"QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": "POST /api/IOT/2.0/myps/Sensor/SqlSyntax/JoinMultiTable",
            "OperationTime": "0.298",
            "BytesTransferred": 353,
            "DB": "MYSQL+POSTGRESQL",
            "System": "IOT",
            "QueryTableData": [
                {
                    "wire_box$wire_diameter": "4.8",
                    "wire_warehousing_dtl$rack_wgt": 30.0,
                    "wire_warehousing_dtl$doc_no": "WE_I201910071_002",
                    "wire_box$wire_material": "SCM435",
                    "wire_warehousing_dtl$manufacturer": "邢台鋼鐵"
                }
            ],
            "Response": "ok"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","dbName","getSqlSyntax"]
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
    
    #至少要有condition_1
    if reqdataDict.get("condition_1") is None:
        dicRet["Response"] = "'request.data' missing key : 'condition_1'"
        return jsonify( **dicRet)
    
    #先查key:condition_1的條件
    action_status,action_result = ApiSqlsyntaxActions({"request_data":reqdataDict["condition_1"],"isjoin":True}).check_post_parameter()
    if not action_status:
        dicRet["Response"] = action_result
        return jsonify( **dicRet)

    recList = []
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()
    
        tables = action_result["tables"]
        #---------------------------------------------------------
        # tables
        #---------------------------------------------------------
        #{{{
        #check table existed or not
        checkdbnameList = []
        if tables != "":
            if len(tables) < 2:
                dicRet["Response"] = "至少要有兩個table"
                return jsonify( **dicRet)

            # for i in range(len(tables)):
            #     table_existed,sensorDict = _retrieve_senrawtable(sess,metadata,tables[i])
            #     if not table_existed:
            #         dicRet["Response"] = "Table {}".format(sensorDict)
            #         return jsonify( **dicRet)
                
            #     if sensorDict["db_name"] not in checkdbnameList:
            #         checkdbnameList.append(sensorDict["db_name"])
            # else:
            #     if len(checkdbnameList) > 1:
            #         dicRet["Response"] = "不同資料庫無法join"
            #         return jsonify( **dicRet)
        else:
            dicRet["Response"] = "'tables' parameter can't be Null"
            return jsonify( **dicRet)
        #}}}

        try:
            dbName  = request.args.get("dbName").encode('utf-8')
            DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
            if DbSessionRaw is None:
                #表示連接資料庫有問題
                dicRet["Response"] = engineRaw
                return jsonify( **dicRet)
            
            sessRaw = DbSessionRaw()

            sqlsyntax_actions_status,sqlsyntax_actions_result = join_sqlsyntax_params_actions(action_result,int("condition_1".split("_")[1]),reqdataDict,sessRaw,metaRaw,"postgres",True,SYSTEM)
            if not sqlsyntax_actions_status:
                dicRet["Response"] = sqlsyntax_actions_result
                return jsonify( **dicRet)

            if request.args.get("getSqlSyntax") == "yes":
                dicRet['SqlSyntax'] = str(sqlsyntax_actions_result[1].compile(compile_kwargs={"literal_binds": True}))

            dicRet['QueryTableData'] = sqlsyntax_actions_result[0]
            err_msg = "ok" #done successfully
        
        except Exception as e:
            err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

        finally:
            if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
                sessRaw.close()
                DbSessionRaw.remove()
                engineRaw.dispose()

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRESQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/1.0/myps/Sensor/Rows', 
# Definition: delete rows and reset auto-seq number
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Rows', methods = ['DELETE']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Rows',  methods = ['DELETE'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def snesor_delete_rows(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除postgresql單一感測器資料表所有資料服務",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "sensor_raw_table":{"type":"String","requirement":"required","directions":"感測器資料表名稱","example":"test"}
            },
            "example":[
                {
                    "sensor_raw_table":"test"
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{
            "sensor_raw_table":"string",
            "DB":"string"
        },
        "API_example":{
            "APIS": "DELETE /api/IOT/1.0/myps/Sensor/Rows",
            "BytesTransferred": 134,
            "OperationTime": "0.105",
            "sensor_raw_table": "weight",
            "Response": "ok",
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
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

    post_parameter = ["sensor_raw_table"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    sensor_raw_table = reqdataDict.get("sensor_raw_table").encode('utf8').strip()

    #查詢該ID是否存在，若存在回傳sensor detail
    thisIDexisted,sensorDict= retrieve_table(SYSTEM,sensor_raw_table)
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensorDict["sensor_raw_table"]

    try: 
        DbSessionRaw,_,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        sqlStr = 'DELETE from "{}";'.format(senTableName)
        # sqlStr2 = 'ALTER SEQUENCE "{}_seq_seq" RESTART WITH 1;'.format(senTableName)

        sessRaw.execute(sqlStr)
        # sessRaw.execute(sqlStr2)
        sessRaw.commit()
        err_msg = "ok" 

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["sensor_raw_table"] = sensor_raw_table
    dicRet["DB"] = 'MYSQL+POSTGRES'
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/2.0/myps/Sensor/Rows', 
# Definition: delete rows and reset auto-seq number
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Rows', methods = ['DELETE']), 
@SENSOR_API.route('/api/<SYSTEM>/2.0/myps/Sensor/Rows',  methods = ['DELETE'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def snesor_delete_rows_v2(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除postgresql單一感測器資料表所有資料服務，不經過mysql直接抓取postgresql",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "sensor_raw_table":{"type":"String","requirement":"required","directions":"感測器資料表名稱","example":"test"}
            },
            "example":[
                {
                    "sensor_raw_table":"test"
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{
            "sensor_raw_table":"string",
            "DB":"string"
        },
        "API_example":{
            "APIS": "DELETE /api/IOT/2.0/myps/Sensor/Rows",
            "BytesTransferred": 134,
            "OperationTime": "0.105",
            "sensor_raw_table": "weight",
            "Response": "ok",
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
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

    post_parameter = ["sensor_raw_table"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    sensor_raw_table = reqdataDict.get("sensor_raw_table").encode('utf8').strip()

    senTableName = sensor_raw_table

    #先去檢查Redis是否有此key:senTableName
    status,result = get_redis_sensor_IDKEY_ornot_create(SYSTEM,senTableName)
    if not status:
        dicRet["Response"] = result
        return jsonify( **dicRet)
    dbName = result

    try: 
        DbSessionRaw,_,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()
        
        sqlStr = 'DELETE from "{}";'.format(senTableName)
        # sqlStr2 = 'ALTER SEQUENCE "{}_seq_seq" RESTART WITH 1;'.format(senTableName)

        sessRaw.execute(sqlStr)
        # sessRaw.execute(sqlStr2)
        sessRaw.commit()
        err_msg = "ok" 

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["sensor_raw_table"] = sensor_raw_table
    dicRet["DB"] = 'MYSQL+POSTGRES'
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/1.0/myps/Sensor', 
# Definition: delete sensor and drop table in postgresql 
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor', methods = ['DELETE']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor',  methods = ['DELETE'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_delete(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除mysql一感測器基本資料服務，並在postgresql刪除感測器資料表",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "sensor_raw_table":{"type":"String","requirement":"required","directions":"感測器資料表名稱","example":"test"}
            },
            "example":[
                {
                    "sensor_raw_table":"test"
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{
            "sensor_raw_table":"string",
            "DB":"string"
        },
        "API_example":{
            "APIS": "DELETE /api/IOT/1.0/myps/Sensor",
            "userID": "AceMoriKTGH",
            "BytesTransferred": 134,
            "OperationTime": "0.105",
            "sensor_raw_table": "weight",
            "Response": "ok",
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
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

    post_parameter = ["sensor_raw_table"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    sensor_raw_table = reqdataDict.get("sensor_raw_table").encode('utf8').strip()

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #查詢該ID是否存在，若存在回傳sensor detail
        thisIDexisted,sensorDict= _retrieve_senrawtable(sess,metadata,sensor_raw_table)
        if not thisIDexisted: #True為存在
            dicRet["Response"] = "{} ID isn't exist".format(sensor_raw_table)
            return jsonify( **dicRet)

        dbName = sensorDict["db_name"]
        senTableName = sensor_raw_table

        deleteResult = delete_tables([senTableName],dbName,SYSTEM)

        if deleteResult == "ok":
            sess.query(Sensor.sensor_raw_table).\
                filter(Sensor.sensor_raw_table == sensor_raw_table).\
                delete()
            sess.commit()
            err_msg = "ok"
        else:
            err_msg = deleteResult

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["sensor_raw_table"] = sensor_raw_table
    dicRet["DB"] = 'MYSQL+POSTGRES'
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: '/api/<SYSTEM>/1.0/myps/Sensor/Schema/<serialID>'
# Definition: 查詢感測器資料表schema
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Schema/<tableName>', methods = ['GET']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/Schema/<tableName>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_schema(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢postgresql單一感測器資料表資料屬性服務",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"感測器資料表名稱"},
        "API_parameters":{"uid":"使用者帳號"},
        "API_message_parameters":{
            "schemaList":"array",
            "DB":"string"
        },
        "API_example":{
            "APIS": " GET /api/IOT/1.0/myps/Sensor/Schema/weight",
            "BytesTransferred": 191,
            "OperationTime": "0.065",
            "Response": "ok",
            "schemaList":[{"comment": "\u5275\u5efa\u6642\u9593", "primary_key": true, "type": "TIMESTAMP WITHOUT TIME ZONE", "name": "upload_at", "nullable": false}, {"comment": "\u8b58\u5225\u7de8\u865f", "primary_key": false, "type": "VARCHAR(7)", "name": "identifyid", "nullable": true}, {"comment": "\u6a21\u5177\u7de8\u865f", "primary_key": false, "type": "VARCHAR(50)", "name": "moldid", "nullable": true}, {"comment": "\u6a21\u5177\u5e8f\u865f", "primary_key": false, "type": "VARCHAR(50)", "name": "moldseqid", "nullable": true}, {"comment": "\u6d3e\u5de5\u55ae\u865f", "primary_key": false, "type": "VARCHAR(16)", "name": "workid", "nullable": true}, {"comment": "\u72c0\u614b(S/E)(S=\u9818\u7528,E=\u6b78\u9084)", "primary_key": false, "type": "VARCHAR(1)", "name": "status", "nullable": true}, {"comment": "\u652f\u6578", "primary_key": false, "type": "INTEGER", "name": "count", "nullable": true}, {"comment": "\u4f7f\u7528\u8005", "primary_key": false, "type": "VARCHAR(24)", "name": "uid", "nullable": true}],
            "DB":"MYSQL+POSTGRES"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    #查詢該ID是否存在，若存在回傳sensor detail
    thisIDexisted,sensorDict= retrieve_table(SYSTEM,tableName)
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = tableName

    try: 
        schemaList = []
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)

        # sqlStr = 'SELECT column_name, data_type from information_schema.columns where table_name=\'{}\';'.format(senTableName)
        metaRaw.reflect(only=[senTableName])
        for table in metaRaw.tables.values():
            if table.name == senTableName:
                for column in table.c:
                    schemaDict = {}
                    schemaDict["tablename"] = senTableName
                    schemaDict["tablecomment"] = table.comment
                    schemaDict["name"] = column.name
                    schemaDict["type"] = str(column.type)
                    schemaDict["comment"] = column.comment

                    column_autoincrement = False
                    if isinstance(column.autoincrement,bool):
                        column_autoincrement = True if column.autoincrement else False
                    schemaDict["isidentity"] = column_autoincrement

                    if column.primary_key:
                        thisPRI = "PRI"
                    else:
                        thisPRI = ""
                    schemaDict["primary_key"] = thisPRI

                    if column.nullable:
                        thisnullable = "YES"
                    else:
                        thisnullable = "NO"
                    schemaDict["nullable"] = thisnullable

                    schemaList.append(schemaDict)

        #https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        schemaList = sorted(schemaList, key=lambda k: k['primary_key'],reverse=True) 

        dicRet['schemaList'] = schemaList
        err_msg = "ok"

        # print "~~~~create_default_device_models~~~~"
        # device_models = create_default_device_models("test")
        # print device_models
        # print device_models[0].__tablename__
        # print device_models[0].__dict__
        # print device_models[1].__tablename__
        # print device_models[1].__dict__

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"

    return jsonify( **dicRet)
# }}}

#=======================================================
# Definition: backup mysql table
# Date: 09032019@Yishan
# 1. To backup data table
#=======================================================
#{{{ @SENSOR_API.route('/api/<SYSTEM>/1.0/ps/Sensor/BackUp/<sensor_raw_table>',  methods = ['GET'])
@SENSOR_API.route('/api/<SYSTEM>/1.0/ps/Sensor/BackUp/<sensor_raw_table>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_backup_table(SYSTEM,sensor_raw_table):
    #{{{APIINFO
    '''
    {
        "API_application":"提供postgresql以uploadtime(年)為條件來備份及刪除單一資料表基本資料服務",
        "API_parameters":{"uid":"使用者帳號","year":"西元年份"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sensor_raw_table":"感測器資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","backupYear":"string"},
        "API_example":{
            "APIS": " GET /api/IOT/1.0/ps/Sensor/BackUp/molduse",
            "BytesTransferred": 523,
            "OperationTime":"0.014",
            "Response": "ok",
            "Table":"molduse",
            "DB":"MYSQL",
            "backupYear":"2019"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","year"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    year = request.args.get("year")

    if err_msg == "ok":
        err_msg = "Error" #reset error message
        if request.method == "GET":
            import urllib
            #wei @03092017 adding uid for filtering
            #reUID = request.args.get("uid")
        # else:
            # reqdataDict = json.loads(request.data)
            # currently support [0-9] but not [\d] because escape char '\' in json dumps/loads
            # TODO: support \d \s and so on syntax in regular expression
    #end of err_msg check

    BACKUP_DIR = '/var/www/html/{}/sqlbackup/postgres'.format(SYSTEM)
    #Yishan@09032019 check BACKUP_DIR is existed or mkdir
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    os.chdir(BACKUP_DIR)

    #check table existed or not
    table_existed,sensorDict = retrieve_table(SYSTEM,sensor_raw_table)
    if not table_existed:
        dicRet["Response"] = sensorDict
        return jsonify( **dicRet)

    dbName = sensorDict["db_name"]
    senTableName = sensor_raw_table

    temporarytable = senTableName +"_"+ year
    start_year = year+"-01-01 00:00:00"
    end_year = year+"-12-31 23:59:59" 
    try: 
        #create Raw table in postgresql DB
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        query_table = Table(senTableName , metaRaw, autoload=True)
        query_field = getattr(query_table.c, globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"])

        check_data_existed = False
        for row in sessRaw.query(query_table).filter(query_field.between(start_year,end_year)).all():
            check_data_existed = True
        
        if not check_data_existed:
            dicRet["Response"] = "There is no matching data for your query"
            return jsonify( **dicRet)

        #先建立指定條件的表
        create_temptable_sql = "create table {} as select * from {} where {} between \'{}\' and \'{}\'".format(temporarytable,senTableName,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"],start_year,end_year)
        sessRaw.execute(create_temptable_sql)
        sessRaw.commit()

        pgdump_cmd = '/usr/bin/pg_dump -U postgres --table={} site2 > {}'.format(temporarytable,temporarytable +'.sql')
        try:
            subprocess.check_output(pgdump_cmd,shell=True,stderr= subprocess.STDOUT)
            #最後再進行刪除動作
            err_msg = del_backup_tabledata(SYSTEM,sessRaw,senTableName,start_year,end_year,temporarytable)
        except subprocess.CalledProcessError as e:
            err_msg = '<sensor_backup_restore_table>Unexpected error: 備份失敗'
            appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)

    except Exception as e:
        err_msg = app.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["backupYear"] = year
    dicRet["Response"] = err_msg
    dicRet["sensor_raw_table"] = sensor_raw_table
    dicRet["DB"] = "POSTGRESQL"
    return jsonify( **dicRet)
#}}}

#=======================================================
# Definition: to create temporary table to show postgres history backup data
# Date: 09032019@Yishan
#=======================================================
#{{{ @SENSOR_API.route('/api/<SYSTEM>/1.0/ps/BackUpData/<sqlfilename>',  methods = ['GET'])
@SENSOR_API.route('/api/<SYSTEM>/1.0/ps/Sensor/BackUpData/<sqlfilename>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_get_backupdata(SYSTEM,sqlfilename):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢postgres備份歷史資料服務(以季為單位來做查詢)",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sqlfilename":"sql備份檔名稱"},
        "API_parameters":{"uid":"使用者帳號","quarter":"季(範圍:正整數0~4，0為整年資料)"},
        "API_message_parameters":{"DB":"string","backupfile":"string","backupData":"JSON","quarter":"string"},
        "API_example":{
            "APIS": " GET /api/IOT/1.0/ps/Sensor/BackUpData/molduse_2018",
            "BytesTransferred": 523,
            "OperationTime":"0.014",
            "Response": "ok",
            "backupfile":"molduse_2018.sql",
            "backupData":[{"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 1, "devID": "1", "workID": "1", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "1"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 2, "devID": "2", "workID": "2", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "2"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 3, "devID": "3", "workID": "3", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "3"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 4, "devID": "4", "workID": "4", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "4"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 5, "devID": "5", "workID": "5", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "5"}],
            "quarter":0
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","quarter"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    quarter = int(float(request.args.get("quarter"))) #防止使用者輸入小數，先轉成float()，再轉成int()整數

    if quarter > 4 or quarter < 0:
        dicRet["Response"] = "input error quarter number (0~4)"
        return jsonify( **dicRet)

    err_msg = dicRet["Response"]
    if err_msg == "ok":
        err_msg = "Error" #reset error message
        if request.method == "GET":
            import urllib
            #wei @03092017 adding uid for filtering
            #reUID = request.args.get("uid")
        # else:
            # reqdataDict = json.loads(request.data)
            # currently support [0-9] but not [\d] because escape char '\' in json dumps/loads
            # TODO: support \d \s and so on syntax in regular expression
    #end of err_msg check

    BACKUP_DIR = '/var/www/html/{}/sqlbackup/postgres'.format(SYSTEM)
    os.chdir(BACKUP_DIR)
    #Yishan@09032019 check BACKUP_DIR is existed or mkdir
    if not os.path.isfile(sqlfilename+'.sql'):
        dicRet["Response"] = "file: '{}.sql' is not existed".format(sqlfilename)
        return jsonify( **dicRet)

    try:
        #Yishan@09202019 匯入sql備份，並進行select查詢
        sql_cmd = '/usr/bin/psql -U postgres iot -f {}'.format(sqlfilename+".sql")
        subprocess.check_output(sql_cmd,shell=True,stderr= subprocess.STDOUT)
        dicRet["backupData"],err_msg = qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,quarter,True)
        #移除暫時表
        _,err_msg = qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,"",False)
        
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    dicRet["quarter"] = quarter
    dicRet["Response"] = err_msg
    dicRet["backupfile"] = sqlfilename+".sql"
    dicRet["DB"] = "POSTGRESQL"
    return jsonify( **dicRet)
#}}}

#=======================================================
# Definition: 抓取postgresql指定資料庫中的所有資料表的指定時間區段內的資料容量大小
# Date: 03182021@Yishan
#=======================================================
#{{{ @SENSOR_API.route('/api/<SYSTEM>/1.0/ps/TablesSize/TimeInterval/<db_name>',  methods = ['GET'])
@SENSOR_API.route('/api/<SYSTEM>/1.0/ps/Sensor/TablesSize/TimeInterval/<db_name>',  methods = ['GET'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def get_tables_size(SYSTEM,db_name):
    #{{{APIINFO
    '''
    {
        "API_application":"提供postgresql以upload_at為條件來查詢條件內資料容量大小服務",
        "API_parameters":{"uid":"使用者帳號","start":"年-月-日","end":"年-月-日"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","db_name":"資料庫名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","backupYear":"string"},
        "API_example":{
            "APIS": " GET /api/IOT/1.0/ps/TablesSize/TimeInterval/site2",
            "BytesTransferred": 523,
            "OperationTime":"0.014",
            "Response": "ok",
            "Table":"molduse",
            "DB":"MYSQL",
            "backupYear":"2019"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["start","end"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    if request.args.get("uid") != "ONLYFORPAAS":
        dicRet["Response"] = "no privillege to do this api"
        return jsonify( **dicRet)

    start = request.args.get("start").encode('utf-8')
    end = request.args.get("end").encode('utf-8')

    for timestr in (start,end):
        if not VerifyDataStrLawyer(timestr).verify_date(is_date=True):
            dicRet["Response"] = "error date str '{timestr}' is illegal".format(timestr=timestr)
            return jsonify( **dicRet)

    if datetime.strptime(start, "%Y-%m-%d") > datetime.strptime(end, "%Y-%m-%d"):
        dicRet["Response"] = "start date str '{}' need smaller than end date str '{}'".format(start, end)
        return jsonify( **dicRet)

    start_time = start+" 00:00:00"
    end_time = end+" 23:59:59" 
    try: 
        #create Raw table in postgresql DB
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=db_name,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)
        
        sessRaw = DbSessionRaw()

        metaRaw.reflect()
        tableList = ConvertData().convert(metaRaw.tables.keys())
        print tableList

        tableSizeList = []
        tempTableList = []
        print "start copy table",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        for table in tableList:
            print table
            tempTableList.append("temp_"+table)
        #     get_tables_size_sql = "SELECT pg_size_pretty(sum(pg_column_size(t.*))) as Size, count(*) as Records FROM {} as t where {} between '{}' and '{}'".format(table,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"],start_time,end_time)
        #     print get_tables_size_sql
        #     for row in sessRaw.execute(get_tables_size_sql):
        #         drow = AdjustDataFormat().format(dict(row.items()))
        #         print drow
        #         if drow["records"] != 0:
        #             drow["name"] = table
        #             tableSizeList.append(drow)

            create_temptable_sql = "create table {} as select * from {} where {} between \'{}\' and \'{}\'".format("temp_"+table,table,globalvar.UPLOADTIME[globalvar.SERVERIP]["postgres"],start_time,end_time)
            print create_temptable_sql
            sessRaw.execute(create_temptable_sql)
            sessRaw.commit()
        else:
            print "end copy table",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]

        print "start get table all size ",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        get_tables_size_sql = "SELECT relname as Table,pg_size_pretty(pg_total_relation_size(relid)) as Size\
                FROM pg_catalog.pg_statio_all_tables\
                where schemaname='public' AND relname LIKE '{}%'".format("temp_")
        print get_tables_size_sql

        for row in sessRaw.execute(get_tables_size_sql):
            drow = AdjustDataFormat().format(dict(row.items()))
            print drow
            tableSizeList.append(drow)
        else:
            print "end get table all size ",datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
        print

        if tableSizeList:
            err_msg = "ok"
            dicRet["tableSizeList"] = tableSizeList
        else:
            err_msg = "There is no matching data for your query"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            print tempTableList
            print 'DROP TABLE IF EXISTS {};'.format(",".join(tempTableList))
            sessRaw.execute('DROP TABLE IF EXISTS {};'.format(",".join(tempTableList)))
            sessRaw.commit()
            
            sessRaw.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    dicRet["Response"] = err_msg
    dicRet["StartTime"] = start
    dicRet["EndTime"] = end
    dicRet["DBName"] = db_name
    dicRet["DB"] = "POSTGRESQL"
    return jsonify( **dicRet)
#}}}

#=======================================================
# API: /api/<SYSTEM>/1.0/myps/Sensor/ExportCsv/<tableName>
# Definition: 提供使用者匯出postgresql指定資料表&欄位&時間條件的csv檔
# Date: 05062021@Yishan
# FOR MYSQL+POSTGRES
#=======================================================
#{{{ SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/ExportCsv/<tableName>', methods = ['POST']), 
@SENSOR_API.route('/api/<SYSTEM>/1.0/myps/Sensor/ExportCsv/<tableName>',  methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def sensor_export_csv(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供使用者匯出postgresql指定資料表&欄位&時間條件的csv檔",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"感測器資料表名稱"},
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":{},
            "parameters":{
                "fields":{"type":"Array","requirement":"required","directions":"欲匯出的資料表欄位列表","example":"['testa','testb',....]"},
                "intervaltime":{"type":"Object","requirement":"required","directions":"欲匯出的資料時間區段，key為時間欄位，value需為陣列:[start,end]","example":{"upload_at":["2021-05-05 22:00:01","2021-05-06 10:00:05"]}},
                "exportfilename":{"type":"String","requirement":"required","directions":"欲匯出的資料檔名，無須加副檔名(預設.csv)","example":"workhour"}
            },
            "precautions":{
                "注意事項1":"'intervaltime'的key需為時間屬性，value內的值必須為正確的時間字串(%Y-%m-%d %H:%M:%S)，且結束大於開始",
                "注意事項2":"匯出的csv檔案會在指定資料夾內，路徑請詢問系統維護者",
                "注意事項3":"匯出的csv檔案會於當天23:59時移除"
            },
            "example":[
                {
                    "fields":["work_code","project_id","upload_at","status"],
                    "intervaltime":{"upload_at":["2021-05-01 00:00:01","2021-05-06 00:55:56"]}
                }
            ]
        },
        "API_message_parameters":{
            "DB":"string"
        },
        "API_example":{
            "APIS": "POST /api/IOT/1.0/myps/Sensor/ExportCsv/workhour",
            "OperationTime": "0.127",
            "BytesTransferred": 113,
            "THISTIME": "2021-05-06 13:28:27.847981",
            "DB": "MYSQL+POSTGRES",
            "System": "IOT",
            "Response": "ok"
        }
    }
    '''
    #}}}
    err_msg = "error"
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

    post_parameter = {"fields":[list],"intervaltime":[dict],"exportfilename":[str,unicode]}
    if not check_post_parameter_exist_format(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters or error format : '{}'".format(post_parameter)
        return jsonify( **dicRet)
    
    fields = reqdataDict.get("fields")
    intervaltime = reqdataDict.get("intervaltime")
    exportfilename = reqdataDict.get("exportfilename").encode("utf8").strip()

    #查詢該ID是否存在，若存在回傳sensor detail
    thisIDexisted,sensorDict= retrieve_table(SYSTEM,tableName)
    if not thisIDexisted: #True為存在
        dicRet["Response"] = sensorDict
        return jsonify(**dicRet)

    dbName = sensorDict["db_name"]
    senTableName = tableName

    try: 
        schemaList = []
        DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(system=SYSTEM,dbName=dbName,forRawData="postgres")
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engineRaw
            return jsonify( **dicRet)

        desc_table_status,fieldList,schemaDict,_ = _desc_table(SYSTEM,metaRaw,senTableName)
        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)
        
        fields_not_existed = list(set(fields).difference(fieldList))
        if len(fields_not_existed) != 0:
            dicRet["Response"] = "Error fields parameters : '{}' not existed".format(fields_not_existed)
            return jsonify( **dicRet)
        
        timekey = intervaltime.keys()[0]
        
        if schemaDict[timekey] not in ["TIMESTAMP","DATETIME","TIMESTAMP WITHOUT TIME ZONE","DATE"]:
            dicRet["Response"] = "error 'intervaltime' parameter input '{}' schema is not TIMESTAMP or DATETIME or DATE".format(timekey)
            return jsonify( **dicRet)
        
        if not isinstance(intervaltime.values()[0],list):
            dicRet["Response"] = "error 'intervaltime' parameter input, '{}' it must be an Array".format(intervaltime.values()[0])
            return jsonify( **dicRet)
        
        #判斷intervaltime.values()[0][0],intervaltime.values()[0][1]皆為合法時間字串
        for timestr in intervaltime.values()[0]:
            if not VerifyDataStrLawyer(timestr).verify_date():
                dicRet["Response"] = "error 'intervaltime' parameter input, date str '{}' is illegal".format(timestr)
                return jsonify( **dicRet)
        
        #檢查post intervaltime childtime length是否為2
        if len(intervaltime.values()[0]) != 2:
            dicRet["Response"] = "error 'intervaltime' parameter input '{}', must have a start time and an end time".format(intervaltime.values()[0])
            return jsonify( **dicRet)
        
        timestart = intervaltime.values()[0][0]
        timeend = intervaltime.values()[0][1]

        if datetime.strptime(timeend, "%Y-%m-%d %H:%M:%S") < datetime.strptime(timestart, "%Y-%m-%d %H:%M:%S"):
            dicRet["Response"] = "error 'intervaltime' parameter input, start date str '{}' need smaller than end date str '{}'".format(timestart,timeend)
            return jsonify( **dicRet)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSessionRaw' in locals().keys() and DbSessionRaw is not None:
            DbSessionRaw.remove()
            engineRaw.dispose()
    
    try:
        # EXPORT_DIR = '/var/www/html/{}/csvfile'.format(SYSTEM)
        EXPORT_DIR = '/var/www/spdpaas/src/dashboard/csvfile/{}'.format(SYSTEM)
        #Yishan@09032019 check BACKUP_DIR is existed or mkdir
        if not os.path.isdir(EXPORT_DIR):
            os.makedirs(EXPORT_DIR)
        # os.chdir(EXPORT_DIR)

        sql_cmd = '/usr/bin/psql \
            "postgresql://{user}:{password}@{ip}:{port}/{db}" \
            -c "\copy (select {fields} from \\"{tablename}\\" where \\"{timekey}\\" between \'{timestart}\' and \'{timeend}\' order by \\"{timekey}\\" asc) \
            to \'{EXPORT_DIR}/{exportfilename}.csv\' csv header"'.format(user=dicConfig.get("DBPOSTGRESUser"),\
                password=dicConfig.get("DBPOSTGRESPassword"),ip=dicConfig.get("DBPOSTGRESIp"),\
                port=dicConfig.get("DBPOSTGRESPort"),db=dbName,fields='\\"'+'\\",\\"'.join(fields)+'\\"',tablename=senTableName,\
                timekey=timekey,timestart=timestart,timeend=timeend,EXPORT_DIR=EXPORT_DIR,exportfilename=exportfilename)
        print "~~~sql_cmd~~~"
        print sql_cmd
        subprocess.check_output(sql_cmd,shell=True,stderr= subprocess.STDOUT)  

        err_msg = "ok"

    except subprocess.CalledProcessError as e:
        err_msg = appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL+POSTGRES"

    return jsonify( **dicRet)
# }}}