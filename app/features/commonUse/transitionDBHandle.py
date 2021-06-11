# -*- coding: utf-8 -*-
#CommonUse module description
"""
==============================================================================
created    : 
Last update: 03/31/2021
Developer: Yi-Shan Tsai 
Lite Version 2 @Yishan08212019
API Version 1.0

Filename: transitionDBHandle.py

Description: about transition type DB(MariaDB)

Total = 16 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
# {{{
from sqlalchemy import *
import hmac, hashlib
import subprocess #Yishan 05212020 subprocess 取代 os.popen

# #Yishan 07222020 捕捉pymysql Exception
# #https://www.itread01.com/content/1544814466.html
# import pymysql
# from warnings import filterwarnings
# filterwarnings("error",category=pymysql.Warning)
# }}}

#=======================================================
# User-defined modules
#=======================================================
# {{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
# }}}

#blueprint
TRANSITIONDB_API = Blueprint('TRANSITIONDB_API', __name__)

#=======================================================
# Definition: 刪除備份好的mysql table data
# Date: 09032019@Yishan
#=======================================================
#{{{def del_backup_tabledata(SYSTEM,sess,query_table,start_year,end_year)
def del_backup_tabledata(SYSTEM,sess,query_table,start_year,end_year):
    try:
        delete_backup_table = query_table
        sess.execute(delete_backup_table.delete().where(between(getattr(delete_backup_table.c,globalvar.CREATETIME[globalvar.SERVERIP]["mysql"]),start_year,end_year)))
        sess.commit()
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    return err_msg
#}}}

#=======================================================
# Definition: mysql 先查詢後刪除temporary backup table data
# Date: 09032019@Yishan
#=======================================================
#{{{def qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,quarter,setquery)
def qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,quarter,setquery):
    recList = []
    sqlfile_year = sqlfilename.split("_")
    sqlfile_year = sqlfile_year[1]
    DAYSTART = "01 00:00:00"
    set_quarter = ["",1,4,7,10]
    set_days30or31 = ["","31 23:59:59","30 23:59:59","30 23:59:59","31 23:59:59"]

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            return
        
        sess = DbSession()

        if not retrieve_table_exist(metadata,'temporary_'+sqlfilename,SYSTEM):
            err_msg = "Table '{}' doesn't exist".format('temporary_'+sqlfilename)
            return

        temporary_backuptable = Table('temporary_'+sqlfilename , metadata, autoload=True)
        query_field = getattr(temporary_backuptable.c, globalvar.CREATETIME[globalvar.SERVERIP]["mysql"])

        if setquery:
            if quarter == 0:
                result = sess.query(temporary_backuptable).all()
            else:
                if quarter != "":
                    yearmonthStart = sqlfile_year+"-"+str(set_quarter[quarter])+"-"
                    yearmonthEnd = sqlfile_year+"-"+str((set_quarter[quarter]+2))+"-"
                    whereStart = yearmonthStart + DAYSTART
                    whereEnd = yearmonthEnd + set_days30or31[quarter]
                    result = sess.query(temporary_backuptable).filter(query_field.between(whereStart,whereEnd)).all()

            for row in result:
                drow = AdjustDataFormat().format(row._asdict())
                recList.append(drow)
                
            if len(recList) == 0:
                err_msg = "There is no matching data for your query"
            else:
                err_msg = "ok"
        else:
            temporary_backuptable.drop()
            err_msg = "ok"

    except Exception as e:
            err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

        return recList,err_msg
#}}}

#=======================================================
# CommonUse
# special API to query all tables 
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/TableData', methods = ['GET']), 
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/TableData',  methods = ['GET'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_tabledata(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","table":"欲查詢之資料表名稱"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " GET /api/VUESYSTEM/1.0/my/CommonUse/TableData",
            "BytesTransferred": 50810,
            "userID": "LTMtouspourun",
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "mfgprocess",
            "QueryTableData":[{
                "updated_at": "2018-11-07 16:49:40",
                "created_at": "2018-10-31 16:33:03",
                "plevel": "gg",
                "mfgpID": "PWW001",
                "devinfo": "gg"
            }],
            "DB":"MYSQL"
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
    uri_parameter = ["uid","table"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    tableName = request.args.get("table")

    if request.method == "GET":
        import urllib
        #wei @03092017 adding uid for filtering
        #reUID = request.args.get("uid")
    # else:
        # reqdataDict = json.loads(request.data)
        # currently support [0-9] but not [\d] because escape char '\' in json dumps/loads
        # TODO: support \d \s and so on syntax in regular expression
    #end of err_msg check

    recList = []
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)
        
        #Yishan 10172019 改變方式
        query_table = Table(tableName , metadata, autoload=True)
        for row in sess.query(query_table):
            drow = AdjustDataFormat().format(row._asdict())
            recList.append(drow)

        dicRet['QueryTableData'] = recList
        err_msg = "ok" #done successfully
        # http://stackoverflow.com/questions/4112337/regular-expressions-in-sqlalchemy-queries

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# API: /api/<SYSTEM>/1.0/my/CommonUse/CreateTable 
# Definition:
# FOR MYSQL
#=======================================================
#{{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/CreateTable', methods = ['POST']), 
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/CreateTable',  methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_create_table(SYSTEM):
    #{{{APIINFO
    """
    {
        "API_application":"提供建立mysql資料表服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "table_name":{"type":"String","requirement":"required","directions":"資料表名稱","example":"test"},
                "table_comment":{"type":"String","requirement":"required","directions":"資料表描述說明","example":"測試資料表"},
                "table_attr":{
                    "type":"Array",
                    "requirement":"required",
                    "directions":[
                        "建立資料表的屬性，詳細內容格式請看'Show Details'",
                        {
                            "name":{"說明":"欄位名稱(string)"},
                            "type":{
                                "說明":"欄位屬性(string)",
                                "備註":"可放以下sql屬性：MYSQL_INTEGER/BOOLEAN/VARCHAR/JSON/DECIMAL/TIMESTAMP",
                                "注意事項":"若欲使用MYSQL_INTEGER當主鍵且為auto-increment值，primarykey設為true_autoinc，即可"
                            },
                            "primarykey":{"說明":"欄位主鍵(string)","備註":"true/true_autoinc/false"},
                            "length":{"說明":"欄位長度(string)"},
                            "default":{"說明":"欄位預設值(string)","備註":"若無預設值則不用放此參數"},
                            "nullable":{"說明":"欄位nullable(string)","備註":"true/false"},
                            "comment":{"說明":"欄位備註說明(string)"}
                        }
                    ],
                    "example":[
                        {"name":"id","type":"INTEGER","length":"5","primarykey":"true_autoinc","nullable":"","comment":"ggggg"},
                        {"name":"name","type":"VARCHAR","length":"50","primarykey":"true","nullable":"","comment":""},
                        {"name":"face","type":"DECIMAL","length":"7.6","primarykey":"","nullable":"","comment":""}
                    ]
                }
            },
            "precautions": {
                "注意事項1":"'table_attr' 目前尚未提供foreign key，固定欄位會有created_at跟update_at",
                "注意事項2":"'table_name'不得重複"
            },
            "example":[
                {
                    "table_name":"test",
                    "table_comment":"測試",
                    "table_attr":[
                        {"name":"id","type":"INTEGER","length":"5","primarykey":"true_autoinc","nullable":"","comment":"ggggg"},
                        {"name":"name","type":"VARCHAR","length":"50","primarykey":"true","nullable":"","comment":""},
                        {"name":"face","type":"DECIMAL","length":"7.6","primarykey":"","nullable":"","comment":""}
                    ]
                }
            ]
        },
        "API_message_parameters":{
            "dbName":"string",
            "DB":"string"
        },
        "API_example":{
            "Response": "ok",
            "APIS": "POST /api/VUESYSTEM/1.0/my/CommonUse/CreateTable",
            "OperationTime": "0.212",
            "BytesTransferred": 111,
            "DB": "MYSQL",
            "System": "VUESYSTEM",
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

    post_parameter = ["table_name","table_comment","table_attr"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    table_name = reqdataDict.get("table_name").encode('utf-8').strip()
    table_comment = reqdataDict.get("table_comment").encode('utf8').strip()
    table_attr = reqdataDict.get("table_attr")

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)

        if retrieve_table_exist(metadata,table_name,SYSTEM):
            dicRet["Response"] = "this : 'table_name' : '{}' existed".format(table_name)
            return jsonify( **dicRet)

        table_attrnameList = []
        #判斷table_attr格式正確性
        post_parameter = ["name","type","length","primarykey","nullable","comment"]
        for i in table_attr:
            table_attrnameList.append(i["name"])
            if not check_post_parameter_exist(i,post_parameter):
                dicRet["Response"] = " table_attr '{}' Missing post parameters : '{}'".format(i,post_parameter)
                return jsonify( **dicRet)

        #若table_attr的長度跟抓到的name長度不同，表示有重複的name，回覆error
        if len(table_attr) != len(list(set(table_attrnameList))):
            dicRet["Response"] = "table_attr fields 'name' : '{}' is duplicate".format(table_attrnameList)
            return jsonify( **dicRet)

        result ,err_msg = create_table(table_name=table_name, attrList=table_attr, table_comment=table_comment, forRawData="mysql",system=SYSTEM)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL"
    return jsonify(**dicRet)
# }}}

#=======================================================
# CommonUse
# API: '/api/<SYSTEM>/1.0/my/CommonUse/queryRows/interval/<tableID>'
# Definition: query the first and last between value of param
# Date: 0214-2019
# Who: Wei
# Note: 1. could be same value
#       2. only single attribute value will be retrieved
# FOR MYSQL
#=======================================================
#{{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/Interval/<tableID>', methods = ['GET']), 
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/Interval/<tableID>',  methods = ['GET'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_multi_rows_interval(SYSTEM,tableID):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql資料表資料內容的一個範圍",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableID":"資料表名稱"},
        "API_parameters":{
            "uid":"使用者帳號",
            "attr":"資料屬性名稱",
            "valueStart":"欲查詢資料起始值",
            "valueEnd":"欲查詢資料終端值"
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " GET /api/VUESYSTEM/1.0/my/CommonUse/Interval/department",
            "BytesTransferred": 436,
            "Table": "department",
            "OperationTime": "0.019",
            "Response": "ok",
            "attr": "depID",
            "QueryTableData":[{
                "updated_at": "2019-08-26 11:54:10",
                "depinfo": "",
                "noumenonType": "",
                "g_accessNo": "",
                "created_at": "2019-08-26 11:54:10",
                "noumenonID": "",
                "creatorID": "",
                "depname": "sapidoVUESYSTEM",
                "depID": "sapidoVUESYSTEM",
                "dbName": "sapidoVUESYSTEM"
            }],
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
    uri_parameter = ["uid","attr","valueStart","valueEnd"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    tableName = tableID 
    attr   = request.args.get("attr")
    valueStart  = request.args.get("valueStart").encode('utf-8')
    valueEnd   = request.args.get("valueEnd").encode('utf-8')
    wp = request.args.get("whereParameter")
    wv = request.args.get("whereValue")
    
    if err_msg == "ok":
        err_msg = "Error" #reset error message
        if request.method == "GET":
            import urllib
            #wei @03092017 adding uid for filtering
            #reUID = request.args.get("uid")
        else:
            reqdataDict = json.loads(request.data)
            # currently support [0-9] but not [\d] because escape char '\' in json dumps/loads
            # TODO: support \d \s and so on syntax in regular expression

    recList = []
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        queryTable = Table(tableName , metadata, autoload=True)
        columnAttr = getattr(queryTable.c, attr)
        if wp:
            whereParameter = wp.encode("utf-8")
            whereValue = wv.encode("utf-8")
            sql = sess.query(queryTable).filter(columnAttr.between(valueStart,valueEnd),getattr(queryTable.c, whereParameter) == whereValue).all()
        else:
            sql = sess.query(queryTable).filter(columnAttr.between(valueStart,valueEnd)).all()

        for row in sql:
            drow = AdjustDataFormat().format(row._asdict())
            for key,value in drow.items():
                if tableName == "user":
                    if key == globalvar.MYSQL_USER_ID[globalvar.SERVERIP]:
                        catchuID = str(value)
                if key=="pwd": #for user to AES_DECRYPT pwd
                    AES_IV = catchuID
                    AES = Prpcrypt(dicConfig.get('aes_key'), AES_IV, SYSTEM)
                    status,de_result = AES.decrypt(value)
                    if not status:
                        dicRet["Response"] = de_result
                        return jsonify( **dicRet)
                        
                    drow[key] = de_result

            recList.append(drow)
        
        dicRet['QueryTableData'] = recList
        err_msg = "ok" #done successfully
        # http://stackoverflow.com/questions/4112337/regular-expressions-in-sqlalchemy-queries

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName 
    dicRet["DB"] = "MYSQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# CommonUse to set select sql syntax 
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/SqlSyntax/<tableName>', methods = ['POST']), 
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/SqlSyntax/<tableName>',  methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_sqlsyntax(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql資料表資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "precautions": {
                "注意事項1":"where條件不支援json欄位",
                "注意事項2":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項3)",
                "注意事項3":{"where":{"combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]}},
                "注意事項4":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}"
            },
            "parameters":{
                "purpose":{"type":"String","requirement":"required","directions":"欲查詢select方式；只接受3種參數(query|query_or|query_like)","example":"query"},
                "fields":{"type":"Array","requirement":"required","directions":"查詢欄位名稱參數","example":"['id','name','z',......]"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；若是使用query_or，物件裡的value以array型態post，若有特殊or需求請看注意事項2,3,4","example":"{'field':'value',.....}"},
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
                    "fields":["name","id"],
                    "where":{"created_at":"2020-06"},
                    "limit":[0,5],
                    "symbols":{"created_at":"equal"},
                    "orderby":["desc","id"],
                    "intervaltime":{"created_at":["2020-04-01 16:00:00"]}
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
            "APIS": " POST /api/VUESYSTEM/1.0/my/CommonUse/SqlSyntax/user",
            "BytesTransferred": 50810,
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "user",
            "QueryTableData":[{
                "updated_at": "2018-11-07 16:49:40",
                "created_at": "2018-10-31 16:33:03",
                "uid":"e"
            }],
            "DB":"MYSQL"
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
    uri_parameter = ["uid"]
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
            err_msg = "'purpose' can't Null"
        else:
            err_msg = "Error 'purpose' : {}".format(purpose)
        dicRet["Response"] = err_msg
        return jsonify( **dicRet)

    recList = []
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        query_table = Table(tableName , metadata, autoload=True)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,SYSTEM)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        schemaDict = desc_table_return[3]

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
                dicRet["Response"] = "error 'fields' parameter input, can't Null"
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

            fieldcolumnList = ["{}".format(getattr(query_table.c,fields[i]))for i in range(len(fields))]
            finalselect = text(",".join(fieldcolumnList))
        else:
            finalselect = query_table
        #}}}
        #---------------------------------------------------------
        # where
        #---------------------------------------------------------
        #{{{
        wheredictforquertLike = {}
        wheredictforquery = {}
        whereorList = []
        wherecombineList = []
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

            for key,value in wheretoStrDict.items():
                if key !="combine":
                    #判斷where進來的key是否與資料表欄位相符
                    if key not in fieldList: 
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
                    wheredictforquertLike[key] = "%{}%".format(value)
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
                if (schemaDict[timekey] != "TIMESTAMP") and (schemaDict[timekey] != "DATETIME"):
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
                        dicRet["Response"] = "error 'intervaltime' parameter input, start date str '{}' need smaller than end date str '{}'".format(timevalue[0],timevalue[1])
                        return jsonify( **dicRet)

                    startdate = timevalue[0]
                    enddate = timevalue[1]
                else:
                    #欲查詢指定日期到今天
                    enddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    startdate = timevalue[0]

                wherentervaltime[timekey] = [startdate,enddate] 
        #}}}
        #---------------------------------------------------------
        # sess.execute(sqlStr)
        #---------------------------------------------------------
        if purpose == "query_like":
            finalquerywhere = and_(and_(*((between(getattr(query_table.c,key),value[0],value[1]))for key,value in wherentervaltime.items())),
                                *((getattr(query_table.c,key).like(value))for key,value in wheredictforquertLike.items())\
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

        sqlStr = select([finalselect]).distinct().\
                        select_from(query_table).\
                            where(finalquerywhere).\
                            order_by(*finalorderby).\
                            limit(limitEnd).offset(limitStart)
                            
        for row in sess.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recList.append(drow)

        dicRet['QueryTableData'] = recList
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# CommonUse to set select sql syntax 
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/<SYSTEM>/2.0/my/CommonUse/SqlSyntax', methods = ['POST']), 
@TRANSITIONDB_API.route('/api/<SYSTEM>/2.0/my/CommonUse/SqlSyntax',  methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_sqlsyntax_v2(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
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
            "APIS": " POST /api/VUESYSTEM/2.0/my/CommonUse/SqlSyntax",
            "BytesTransferred": 50810,
            "OperationTime": "0.223",
            "Response": "ok",
            "Table": "user",
            "QueryTableData":[{
                "updated_at": "2018-11-07 16:49:40",
                "created_at": "2018-10-31 16:33:03",
                "uid":"e"
            }],
            "DB":"MYSQL"
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
    
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        sqlsyntax_actions_status,sqlsyntax_actions_result = sqlsyntax_params_actions(action_result,"condition_1",reqdataDict,sess,metadata,"mysql",False,SYSTEM)
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
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# CommonUse to set select sql syntax join
# FOR MSSQL
#=======================================================
#{{{ @TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_sqlsyntax_joinmultitable(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql join資料表資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
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
                "注意事項5":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}"
            },
            "example":[
                {
                    "purpose":"query",
                    "fields":{"site":["name","id"],"sensor":["id"]},
                    "where":{"sensor":{"noumenon_id":1} },
                    "join":{"site":[{"sensor":{"id":"noumenon_id"} }]},
                    "jointype":"inner",
                    "limit":[0,10],
                    "tables": ["site","sensor"],
                    "symbols":{"sensor":{"noumenon_id":"equal"} },
                    "orderby":["desc","sensor","id"]
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
        "API_message_parameters":{"QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": "POST /api/VUESYSTEM/1.0/my/CommonUse/SqlSyntax/JoinMultiTable",
            "OperationTime": "0.298",
            "BytesTransferred": 353,
            "DB": "MSSQL",
            "System": "VUESYSTEM",
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
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
    #---------------------------------------------------------
    #Wei@03092017 adding the if-else for user check
    #For runnable version, the uid check for administor 
    # of service, should be added to the database and set it up 
    # when deployed to client
    #---------------------------------------------------------
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
                if not retrieve_table_exist(metadata,tables[i],SYSTEM):
                    dicRet["Response"] = "Table '{}' doesn't exist".format(tables)
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

                desc_table_return = desc_table(metadata,fieldskey,SYSTEM)
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]
                keyList = desc_table_return[2]

                if desc_table_status != 'ok':
                    dicRet["Response"] = desc_table_status
                    return jsonify( **dicRet)

                fieldsvalueList = []
                if isinstance(fieldsvalue,list):
                    fieldsvalueList = fieldsvalue
                else:
                    fieldsvalueList = fieldList

                if len(fieldsvalueList) != len(list(set(fieldList).intersection(set(fieldsvalueList)))):
                    fieldsnomatch = map(str,list(set(fieldsvalueList).difference(set(fieldList))))
                    #如果difference()出來是空的，表示fields是符合schema但重複輸入，返回error
                    if len(fieldsnomatch) != 0:
                        err_msg = "Unknown column \'{}\' in 'field list'".format(fieldsnomatch)
                    else:
                        err_msg = "fields {} is duplicate".format(fieldsvalueList)
                    dicRet["Response"] = err_msg
                    return jsonify( **dicRet)

                for i in range(len(fieldsvalueList)):
                    tempfieldcolumnList.append("{} AS {}".format(getattr(Table(fieldskey ,metadata, autoload=True).c,fieldsvalueList[i]),fieldskey+"$"+fieldsvalueList[i]))
                    fieldcolumnList.append("{}".format(getattr(Table(fieldskey ,metadata, autoload=True).c,fieldsvalueList[i])))
        else:
            for i in range(len(tables)):
                desc_table_return = desc_table(metadata,tables[i],SYSTEM)
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]
                keyList = desc_table_return[2]

                if desc_table_status != 'ok':
                    dicRet["Response"] = desc_table_status
                    return jsonify( **dicRet)

                for j in range(len(fieldList)):
                    tempfieldcolumnList.append("{} AS {}".format(getattr(Table(tables[i] ,metadata, autoload=True).c,fieldList[j]),tables[i]+"$"+fieldList[j]))
                    fieldcolumnList.append("{}".format(getattr(Table(tables[i] ,metadata, autoload=True).c,fieldList[j])))

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
            response, msg, key, value = adjust_dict_for_joinapi(metadata=metadata,tables=tables,masterKey=joinkeyList0,data=i,joinkeyList=joinkeyList,joincolumnList=joincolumnList,system=SYSTEM)
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
                if not isinstance(wherevalue,dict):
                    dicRet["Response"] = "error 'where value : {}' parameter input , must be an Object".format(wherevalue)
                    return jsonify( **dicRet)

                if not wherekey in tables:
                    dicRet["Response"] = "error 'where key {}' parameter input".format(wherekey)
                    return jsonify( **dicRet)

                #desc table schema
                desc_table_return = desc_table(metadata,wherekey,SYSTEM)
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]
                keyList = desc_table_return[2]
                schemaDict = desc_table_return[3]

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
                        wherestrList.append("{} LIKE '%{}%'".format(getattr(Table(wherekey ,metadata, autoload=True).c,wherevalue_key),wherevalue_value))
                    elif purpose == "query_or":
                        if not isinstance(wherevalue_value,list):
                            dicRet["Response"] = "error 'where' parameter input {},must be an Array".format(wherevalue_value)
                            return jsonify( **dicRet)

                        if len(wherevalue_value) == 0:
                            dicRet["Response"] = "error 'where' parameter input {},can't be a Null Array".format(wherevalue_value)
                            return jsonify( **dicRet)

                        #判斷是否有使用combine參數
                        if wherevalue_key != "combine":
                            wheredictforquery[wherevalue_key] = ["{} = '{}'".format(getattr(Table(wherekey ,metadata, autoload=True).c,wherevalue_key),wherevalue_value[o])for o in range(len(wherevalue_value))]
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

                        wherestrList.append("{} {} '{}'".format(getattr(Table(wherekey ,metadata, autoload=True).c,wherevalue_key),operator[symbolstoStrDict[wherekey][wherevalue_key]],wherevalue_value))
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

            #先判斷orderby list長度不為1
            if len(orderby) == 1:
                dicRet["Response"] = "error 'orderby' parameter input {}, miss table & column ex:['asc','table','column']" .format(orderby)
                return jsonify( **dicRet)

            #先判斷orderby list是否為奇數陣列，但長度不為１
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
                    desc_table_return = desc_table(metadata,orderby[i-1],SYSTEM)
                    desc_table_status = desc_table_return[0]
                    fieldList = desc_table_return[1]
                    keyList = desc_table_return[2]

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
                finalorderby = (getattr(Table(orderbytableList[hh] ,metadata, autoload=True).c,orderbycolumnList[hh]).desc()for hh in range(len(orderbytableList)))
            else:
                finalorderby = (getattr(Table(orderbytableList[hh] ,metadata, autoload=True).c,orderbycolumnList[hh]).asc()for hh in range(len(orderbytableList)))
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
            limitEnd = 100
        #}}}
        #---------------------------------------------------------
        # sess.execute(sqlStr)
        #---------------------------------------------------------
        wherejoinSql = Table(joinkeyList0 ,metadata, autoload=True)
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

        for row in sess.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recList.append(drow)

        dicRet['QueryTableData'] = recList
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MSSQL" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# CommonUse to set select sql syntax join
# FOR MYSQL
#=======================================================
#{{{ @TRANSITIONDB_API.route('/api/<SYSTEM>/2.0/my/CommonUse/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/2.0/my/CommonUse/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_sqlsyntax_joinmultitable_v2(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql join資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "parameters":{
                "fields":{"type":"Object","requirement":"required","directions":"查詢欄位名稱參數，若要全選則丟入空字串","example":"{'table':['table_column1','table_column2',....]}"},
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
            "APIS": "POST /api/VUESYSTEM/2.0/my/CommonUse/SqlSyntax/JoinMultiTable",
            "OperationTime": "0.298",
            "BytesTransferred": 353,
            "DB": "MSSQL",
            "System": "VUESYSTEM",
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

        sqlsyntax_actions_status,sqlsyntax_actions_result = join_sqlsyntax_params_actions(action_result,"condition_1",reqdataDict,sess,metadata,"mysql",True,SYSTEM)
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
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["DB"] = "MYSQL" 
    return jsonify( **dicRet)
# }}}

# #=======================================================
# # API: /api/<SYSTEM>/1.0/my/CommonUse/CallProcedure 
# # Definition: 呼叫指定Procedure
# # FOR MYSQL
# #=======================================================
# #{{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/CallProcedure', methods = ['POST']), 
# @TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/CallProcedure',  methods = ['POST'])
# def transitionDB_commonuse_create_table(SYSTEM):
#     #{{{APIINFO
#     """
#     {
#         "API_application":"提供建立mysql資料表服務",
#         "API_parameters":{"uid":"使用者帳號"},
#         "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
#         "API_postData":{
#             "bodytype":"Object",
#             "bodyschema":"{}",
#             "parameters":{
#                 "table_name":{"type":"String","requirement":"required","directions":"資料表名稱","example":"test"},
#                 "table_comment":{"type":"String","requirement":"required","directions":"資料表描述說明","example":"測試資料表"},
#                 "table_attr":{
#                     "type":"Array",
#                     "requirement":"required",
#                     "directions":[
#                         "建立資料表的屬性，詳細內容格式請看'Show Details'",
#                         {
#                             "name":{"說明":"欄位名稱(string)"},
#                             "type":{
#                                 "說明":"欄位屬性(string)",
#                                 "備註":"可放以下sql屬性：MYSQL_INTEGER/BOOLEAN/VARCHAR/JSON/DECIMAL/TIMESTAMP",
#                                 "注意事項":"若欲使用MYSQL_INTEGER當主鍵且為auto-increment值，primarykey設為true_autoinc，即可"
#                             },
#                             "primarykey":{"說明":"欄位主鍵(string)","備註":"true/true_autoinc/false"},
#                             "length":{"說明":"欄位長度(string)"},
#                             "default":{"說明":"欄位預設值(string)","備註":"若無預設值則不用放此參數"},
#                             "nullable":{"說明":"欄位nullable(string)","備註":"true/false"},
#                             "comment":{"說明":"欄位備註說明(string)"}
#                         }
#                     ],
#                     "example":[
#                         {"name":"id","type":"INTEGER","length":"5","primarykey":"true_autoinc","nullable":"","comment":"ggggg"},
#                         {"name":"name","type":"VARCHAR","length":"50","primarykey":"true","nullable":"","comment":""},
#                         {"name":"face","type":"DECIMAL","length":"7.6","primarykey":"","nullable":"","comment":""}
#                     ]
#                 }
#             },
#             "precautions": {
#                 "注意事項1":"'table_attr' 目前尚未提供foreign key，固定欄位會有created_at跟update_at",
#                 "注意事項2":"'table_name'不得重複"
#             },
#             "example":[
#                 {
#                     "table_name":"test",
#                     "table_comment":"測試",
#                     "table_attr":[
#                         {"name":"id","type":"INTEGER","length":"5","primarykey":"true_autoinc","nullable":"","comment":"ggggg"},
#                         {"name":"name","type":"VARCHAR","length":"50","primarykey":"true","nullable":"","comment":""},
#                         {"name":"face","type":"DECIMAL","length":"7.6","primarykey":"","nullable":"","comment":""}
#                     ]
#                 }
#             ]
#         },
#         "API_message_parameters":{
#             "dbName":"string",
#             "DB":"string"
#         },
#         "API_example":{
#             "Response": "ok",
#             "APIS": "POST /api/VUESYSTEM/1.0/my/CommonUse/CreateTable",
#             "OperationTime": "0.212",
#             "BytesTransferred": 111,
#             "DB": "MYSQL",
#             "System": "VUESYSTEM",
#             "dbName": "site2"
#         }
#     }
#     """
#     #}}}
#     err_msg = "error"
#     dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)
#     if SYSTEM not in globalvar.SYSTEMLIST[globalvar.SERVERIP]:
#         dicRet["Response"] = "system:{} has no privillege to use this API".format(SYSTEM)
#         return jsonify( **dicRet)

#     uri_parameter = ["uid"]
#     result, result_msg = check_uri_parameter_exist(request,uri_parameter)
#     if not result:
#         dicRet["Response"] = result_msg
#         return jsonify( **dicRet)
    
#     if not VerifyDataStrLawyer(request.data).verify_json():
#         dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
#         return jsonify( **dicRet)

#     reqdataDict = json.loads(request.data)
#     if isinstance(reqdataDict,type(u"")):
#         reqdataDict = json.loads(reqdataDict)

#     post_parameter = ["table_name","table_comment","table_attr"]
#     if not check_post_parameter_exist(reqdataDict,post_parameter):
#         dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
#         return jsonify( **dicRet)

#     table_name = reqdataDict.get("table_name").encode('utf-8').strip()
#     table_comment = reqdataDict.get("table_comment").encode('utf8').strip()
#     table_attr = reqdataDict.get("table_attr")

#     try:
#         sess,DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
#         if DbSession is None:
#             #表示連接資料庫有問題
#             dicRet["Response"] = engine
#             return jsonify( **dicRet)

#         sess = DbSession()

#         if retrieve_table_exist(metadata,table_name,SYSTEM):
#             dicRet["Response"] = "this : 'table_name' : '{}' existed".format(table_name)
#             return jsonify( **dicRet)

#         table_attrnameList = []
#         #判斷table_attr格式正確性
#         post_parameter = ["name","type","length","primarykey","nullable","comment"]
#         for i in table_attr:
#             table_attrnameList.append(i["name"])
#             if not check_post_parameter_exist(i,post_parameter):
#                 dicRet["Response"] = " table_attr '{}' Missing post parameters : '{}'".format(i,post_parameter)
#                 return jsonify( **dicRet)

#         #若table_attr的長度跟抓到的name長度不同，表示有重複的name，回覆error
#         if len(table_attr) != len(list(set(table_attrnameList))):
#             dicRet["Response"] = "table_attr fields 'name' : '{}' is duplicate".format(table_attrnameList)
#             return jsonify( **dicRet)

#         result ,err_msg = create_table(table_name=table_name, attrList=table_attr, table_comment=table_comment, forRawData="mysql",system=SYSTEM)

#     except Exception as e:
#         err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

#     finally:
#         if 'DbSession' in locals().keys() and DbSession is not None:
#             sess.close()
#             DbSession.remove()
#             engine.dispose()

#     dicRet["Response"] = err_msg
#     dicRet["DB"] = "MYSQL"
#     return jsonify(**dicRet)
# # }}}

#=======================================================
# API to CommonUse register
# Date: 08292019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/<tableName>', methods = ['POST'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/<tableName>', methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_register(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供註冊mysql通用Table的單筆或多筆資料服務(department/site/place/device/sensor，此五個表不適用)",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "資料表所有欄位":{"type":"Array","requirement":"optional","directions":"資料表所有欄位值","example":"['value1','value2',...]"},
            "precautions":{
                "注意事項1":"postData內不可含有' : '，系統會自動替代成' - '",
                "注意事項2":"若要新增JSON欄位值，需以JSON字串方式傳入且key必須以雙引號包起來",
                "注意事項3":"mysql固定時間欄位無需post",
                "注意事項4":"若該欄位可允許為null，value放null即可",
                "注意事項5":"若該欄位有預設default值則無需post此欄位"
            },
            "example":[
                {
                    "device_name":["test"],
                    "pre_work_code":[""],
                    "work_code":[""],
                    "mould_code":[""],
                    "mould_series_no":["a"],
                    "material_code":[""],
                    "material_batch_no":[""],
                    "scroll_no":[""],
                    "first_inspection":[0],
                    "status":["E"],
                    "self_inspection":["2020-06-18 09:53:17"],
                    "runcard_code":[""],
                    "screw_weight":[0]
                },
                {
                    "id":[3687,3688],
                    "email":["test","test"],
                    "name":["test","test"],
                    "access_list":[null,null],
                    "creator":[0,0],
                    "modifier":[0,0]
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","insertstatus":"string+各筆資料新增狀態，若全部新增成功則無此Response"},
        "API_example":{
            "APIS": "POST /api/VUESYSTEM/1.0/my/CommonUse/VUESYSTEMgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device" or tableName == "sensor":
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)

    #多筆資料新增的狀態
    insertstatus = [] 
    insertstatusmsg = ""
    #此資料表的主鍵為id(流水號，自動產生)
    thisPRIisid = False

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,SYSTEM,havetime=False)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        keyList = desc_table_return[2]
        schemaDict = desc_table_return[3]
        defaultDict = desc_table_return[4]
        nullableDict = desc_table_return[6]

        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        if not VerifyDataStrLawyer(request.data).verify_json():
            dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
            return jsonify( **dicRet)

        #collect data items from a request
        reqdataDict = json.loads(request.data)
        if isinstance(reqdataDict,type(u"")):
            reqdataDict = json.loads(reqdataDict)
        
        registertargetTable = Table(tableName , metadata, autoload=True)

        if not keyList:
            dicRet["Response"] = "Error 此資料表找不到主鍵"
            return jsonify( **dicRet)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        for i in range(len(keyList)): 
            #有任何主鍵沒post到，return error
            if reqdataDict.get(keyList[i]) is None:
                dicRet["Response"] = "primary key is necessary"
                return jsonify( **dicRet)
            
            if not isinstance(reqdataDict.get(keyList[i]),list):
                dicRet["Response"] = "Error type of '{}',it must be an Array".format(keyList[i])
                return jsonify( **dicRet)

            #把unicode list 轉成 str list，才能抓到list內的各內容
            postDataKEYtostrList = map(str,reqdataDict.get(keyList[i]))
            postDataCount = len(postDataKEYtostrList)

            #判斷主鍵為空陣列回覆error
            if not postDataKEYtostrList:
                dicRet["Response"] = "primary key {} can't be None".format(keyList[i])
                return jsonify( **dicRet)

            thisseq = -1
            for j in range(len(postDataKEYtostrList)):
                if tableName != "user" and keyList[i] == "id":
                    thisPRIisid = True
                    if postDataKEYtostrList[j] != "":
                        dicRet["Response"] = "primary key '{}'為自動地增值，放空值即可".format(keyList[i])
                        return jsonify( **dicRet)

                if keyList[i] != "seq":
                    query_field = getattr(registertargetTable.c, keyList[i])
                    if isinstance(postDataKEYtostrList[j],str):
                        postKeyList.append('({} = "{}")'.format(query_field,postDataKEYtostrList[j]))
                    else:
                        postKeyList.append('({} = {})'.format(query_field,postDataKEYtostrList[j]))
                else:
                    dataexist = sess.query(registertargetTable).all()
                    columnAttr = getattr(registertargetTable.c, "seq")
                    if len(dataexist) != 0:
                        for row in sess.query(getattr(registertargetTable.c,"seq")).order_by(desc(getattr(registertargetTable.c,"seq"))).limit(1):
                            thisseq = row[0]

                    nextseq = int(thisseq)+(j+1)
                    postKeyList.append('({} = {})'.format(columnAttr,nextseq))
                # #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                # postKeyList.append('({} = "{}")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))
            
        #每一筆新增資料的where條件陣列
        whereDict = [postKeyList[i::postDataCount] for i in range(postDataCount)]

        #每一筆新增資料的where條件str
        for i in range(len(whereDict)):
            check_data_existed = False
            if not thisPRIisid:
                #以&來join陣列
                whereStr = " & ".join(whereDict[i])
                for row in sess.execute(registertargetTable.select(text(whereStr))):
                    check_data_existed = True

            #獲取目前的i
            thisNum = i
            #各筆資料的所有Data dict
            postDataList = {}
        
            if not check_data_existed:
                for x in range(len(fieldList)):
                    #有任何欄位沒post到，return error
                    if reqdataDict.get(fieldList[x]) is None:
                        #排除有dafault值的欄位
                        if not defaultDict[fieldList[x]]:
                            dicRet["Response"] = "{} missing post fields : '{}'".format(tableName, fieldList[x])
                            return jsonify( **dicRet)
                    else:
                        if not isinstance(reqdataDict.get(fieldList[x]),list):
                            dicRet["Response"] = "Error type of '{}',it must be an Array".format(fieldList[x])
                            return jsonify( **dicRet)

                        postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                        #postDatatostrList = map(str,reqdataDict.get(fieldList[x]))
                        if len(postDatatostrList) == postDataCount:
                            #Yishan@12252020 排除有default值或可允許null的欄位，不檢查是否有值
                            if (not (defaultDict[fieldList[x]] or nullableDict[fieldList[x]])) and (postDatatostrList[thisNum] is None):
                                dicRet["Response"] = "{} data can't be None".format(fieldList[x])
                                return jsonify( **dicRet)

                            if fieldList[x] == "seq":
                                postDataList['seq'] = int(thisseq)+(i+1)
                            else:
                                if tableName == "user" or fieldList[x] != "id":
                                    needRE = False
                                    if postDatatostrList[thisNum] is not None:
                                        if (not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int))) and \
                                            ((not VerifyDataStrLawyer(postDatatostrList[thisNum]).verify_json()) and (schemaDict[fieldList[x]] not in ("TIMESTAMP","DATETIME","DATE"))):
                                            #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                                            #Yishan@12252020 判斷此欄位是否為時間型態，若是取消re替代
                                            needRE = True
                                    if needRE:
                                        postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                                    else:
                                        postDataList[fieldList[x]] = postDatatostrList[thisNum]
                        else:
                            dicRet["Response"] = "The number of input data does not match"
                            return jsonify( **dicRet)
                        #add time
                        postDataList[globalvar.CREATETIME[globalvar.SERVERIP]["mysql"]] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        postDataList[globalvar.UPLOADTIME[globalvar.SERVERIP]["mysql"]] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                sess.execute(registertargetTable.insert().values(postDataList))
                sess.commit()
                err_msg = "ok"
            else:
                insertstatus.append(whereStr)
                err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if len(insertstatus) != 0:
        insertstatusmsg = "Error: {} ID ({}) existed".format(tableName," , ".join(insertstatus))
        dicRet["insertstatus"] = insertstatusmsg

    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse register
# Date: 08292019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.5/my/CommonUse/<tableName>', methods = ['POST'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.5/my/CommonUse/<tableName>', methods = ['POST'])
@decorator_check_legal_system()
def transitionDB_commonuse_register_v1_5(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供註冊mysql通用Table的單筆或多筆資料服務(department/site/place/device/sensor，此五個表不適用)",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "資料表所有欄位":{"type":"Array","requirement":"optional","directions":"資料表所有欄位值","example":"['value1','value2',...]"},
            "precautions":{
                "注意事項1":"postData內不可含有' : '，系統會自動替代成' - '",
                "注意事項2":"若要新增JSON欄位值，需以JSON字串方式傳入且key必須以雙引號包起來",
                "注意事項3":"mysql固定時間欄位無需post",
                "注意事項4":"若該欄位可允許為null，value放null即可",
                "注意事項5":"若該欄位有預設default值則無需post此欄位"
            },
            "example":[
                {
                    "device_name":["test"],
                    "pre_work_code":[""],
                    "work_code":[""],
                    "mould_code":[""],
                    "mould_series_no":["a"],
                    "material_code":[""],
                    "material_batch_no":[""],
                    "scroll_no":[""],
                    "first_inspection":[0],
                    "status":["E"],
                    "self_inspection":["2020-06-18 09:53:17"],
                    "runcard_code":[""],
                    "screw_weight":[0]
                },
                {
                    "id":[3687,3688],
                    "email":["test","test"],
                    "name":["test","test"],
                    "access_list":[null,null],
                    "creator":[0,0],
                    "modifier":[0,0]
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","insertstatus":"string+各筆資料新增狀態，若全部新增成功則無此Response"},
        "API_example":{
            "APIS": "POST /api/VUESYSTEM/1.5/my/CommonUse/VUESYSTEMgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    err_msg = "error"
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device" or tableName == "sensor":
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        result = commonuse_register_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, "mysql")
        err_msg = result["err_msg"]
        
        if result.get("insertstatus") is not None:
            dicRet["insertstatus"] = result["insertstatus"]
        
        if result.get("nextPRIid") is not None:
            dicRet["nextPRIid"] = result["nextPRIid"]

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse update
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/<tableName>', methods = ['PATCH'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/<tableName>', methods = ['PATCH'])
@decorator_check_legal_system()
def transitionDB_commonuse_update(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供更新mysql通用Table的資料服務(department/site/place/device/sensor，此五個表不適用)",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "old_資料表主鍵欄位": {"type":"Array","requirement":"required","directions":"欲更新的資料主鍵欄位值","example":"['value1','value2',...]"},
            "資料表欄位": {"type":"Array","requirement":"optional","directions":"欲更新的資料欄位內容","example":"['value1','value2',...]"},
            "precautions": {
                "注意事項1":"postData內不可含有' : '，系統會自動替代成' - '",
                "注意事項2":"若要修改JSON欄位值，需以JSON字串方式傳入且key必須以雙引號包起來",
                "注意事項3":"尚未提供修改主鍵",
                "注意事項3":"若該欄位有預設default值或可允許為null，value放null即可"
            },
            "example":[
                {
                    "old_device_name":["test"],
                    "scroll_no":["1"]
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","updatestatus":"string+各筆資料更新狀態，若全部更新成功則無此Response"},
        "API_example":{
            "APIS": "PATCH /api/VUESYSTEM/1.0/my/CommonUse/VUESYSTEMgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL",
            "Table":"VUESYSTEMgroup"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device" or tableName == "sensor":
        dicRet["Response"] = "Try another api for update {}".format(tableName)
        return jsonify( **dicRet)

    #多筆資料更新的狀態
    updatestatus = [] 
    updatestatusmsg = ""

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,SYSTEM,havetime=True)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        keyList = desc_table_return[2]
        schemaDict = desc_table_return[3]
        defaultDict = desc_table_return[4]
        nullableDict = desc_table_return[6]

        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        if not VerifyDataStrLawyer(request.data).verify_json():
            dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
            return jsonify( **dicRet)

        #collect data items from a request
        reqdataDict = json.loads(request.data)
        if isinstance(reqdataDict,type(u"")):
            reqdataDict = json.loads(reqdataDict)

        updatetargetTable = Table(tableName , metadata, autoload=True)

        if not keyList:
            dicRet["Response"] = "Error 此資料表找不到主鍵"
            return jsonify( **dicRet)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        for i in range(len(keyList)):
            if reqdataDict.get("old_"+ keyList[i]) is None:
                dicRet["Response"] = "primary key is necessary and format of the primary key must be 'old_xxx'"
                return jsonify( **dicRet)

            if not isinstance(reqdataDict.get("old_"+ keyList[i]),list):
                dicRet["Response"] = "Error type of '{}',it must be an Array".format("old_"+ keyList[i])
                return jsonify( **dicRet)

            #把unicode list 轉成 str list，才能抓到list內的各內容
            postDataKEYtostrList = map(str,reqdataDict.get("old_"+ keyList[i]))

            #判斷主鍵為空陣列回覆error
            if not postDataKEYtostrList:
                dicRet["Response"] = "primary key {} can't be None".format(keyList[i])
                return jsonify( **dicRet)

            postDataCount = len(postDataKEYtostrList)
            if i == 0:
                checkpostDataCount = postDataCount
            else:
                if postDataCount != checkpostDataCount:
                    dicRet["Response"] = "error 'Composite Primary Key' parameter input '{}', Length does not match".format(reqdataDict.get("old_"+ keyList[i]))
                    return jsonify( **dicRet)

            for j in range(len(postDataKEYtostrList)):
                query_field = getattr(updatetargetTable.c,keyList[i])
                if isinstance(postDataKEYtostrList[j],str):
                    postKeyList.append('({} = "{}")'.format(query_field,postDataKEYtostrList[j]))
                else:
                    postKeyList.append('({} = {})'.format(query_field,postDataKEYtostrList[j]))
                # #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                # postKeyList.append('({} = \"{}\")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))
                    
        #每一筆更新資料的where條件陣列
        whereDict = [postKeyList[i::postDataCount] for i in range(postDataCount)]
        # for i in range(postDataCount):
        #     #以間隔方式一一抓取
        #     whereDict.append(postKeyList[i::postDataCount])

        #每一筆更新資料的where條件str
        for i in range(len(whereDict)):
            check_data_existed = False
            #以&來join陣列
            whereStr = " & ".join(whereDict[i])
            for row in sess.execute(updatetargetTable.select(text(whereStr))):
                check_data_existed = True
            
            #獲取目前的i
            thisNum = i
            #各筆資料的所有Data dict
            postDataList = {}

            if check_data_existed:
                for x in range(len(fieldList)):
                    #開放給使用者選擇性update參數
                    if reqdataDict.get(fieldList[x]) is not None:
                        if fieldList[x] in keyList:
                            dicRet["Response"] = "Error：主鍵尚未提供修改"
                            return jsonify( **dicRet)

                        if not isinstance(reqdataDict.get(fieldList[x]),list):
                            dicRet["Response"] = "Error type of '{}',it must be an Array".format(fieldList[x])
                            return jsonify( **dicRet)

                        postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                        if len(postDatatostrList) == postDataCount:
                            #Yishan@12252020 排除有default值或可允許null的欄位，不檢查是否有值
                            if (not (defaultDict[fieldList[x]] or nullableDict[fieldList[x]])) and (postDatatostrList[thisNum] is None):
                                dicRet["Response"] = "{} data can't be None".format(fieldList[x])
                                return jsonify( **dicRet)

                            needRE = False
                            if postDatatostrList[thisNum] is not None:
                                if (not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int))) and \
                                        ((not VerifyDataStrLawyer(postDatatostrList[thisNum]).verify_json()) and (schemaDict[fieldList[x]] not in ("TIMESTAMP","DATETIME","DATE"))):
                                        #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                                        #Yishan@12252020 判斷此欄位是否為時間型態，若是取消re替代
                                    needRE = True
                            if needRE:
                                postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                            else:
                                postDataList[fieldList[x]] = postDatatostrList[thisNum]
                            
                        else:
                            dicRet["Response"] = "The number of input data does not match"
                            return jsonify( **dicRet)
                
                if not postDataList:
                    updatestatus.append("Error '{}' 更新失敗：沒有給予任何資料欄位".format(whereStr))
                else:
                    sess.execute(updatetargetTable.update().where(text(whereStr)).values(postDataList))
                    sess.commit()
            else:
                updatestatus.append("Error '{}' doesn't existed".format(whereStr))
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if updatestatus:
        dicRet["updatestatus"] = updatestatus

    dicRet["Response"] = err_msg 
    dicRet["Table"] = tableName 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse update
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.5/my/CommonUse/<tableName>', methods = ['PATCH'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.5/my/CommonUse/<tableName>', methods = ['PATCH'])
@decorator_check_legal_system()
def transitionDB_commonuse_update_v1_5(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供更新mysql通用Table的資料服務(department/site/place/device/sensor，此五個表不適用)",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "old_資料表主鍵欄位": {"type":"Array","requirement":"required","directions":"欲更新的資料主鍵欄位值","example":"['value1','value2',...]"},
            "資料表欄位": {"type":"Array","requirement":"optional","directions":"欲更新的資料欄位內容","example":"['value1','value2',...]"},
            "precautions": {
                "注意事項1":"postData內不可含有' : '，系統會自動替代成' - '",
                "注意事項2":"若要修改JSON欄位值，需以JSON字串方式傳入且key必須以雙引號包起來",
                "注意事項3":"尚未提供修改主鍵",
                "注意事項3":"若該欄位有預設default值或可允許為null，value放null即可"
            },
            "example":[
                {
                    "old_device_name":["test"],
                    "scroll_no":["1"]
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","updatestatus":"string+各筆資料更新狀態，若全部更新成功則無此Response"},
        "API_example":{
            "APIS": "PATCH /api/VUESYSTEM/1.5/my/CommonUse/VUESYSTEMgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL",
            "Table":"VUESYSTEMgroup"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device" or tableName == "sensor":
        dicRet["Response"] = "Try another api for update {}".format(tableName)
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        result = commonuse_update_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, "mysql")
        err_msg = result[0]

        if len(result) == 2:
            dicRet["updatestatus"] = result[1]

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse delete
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/<tableName>', methods = ['DELETE'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/<tableName>', methods = ['DELETE'])
@decorator_check_legal_system()
def transitionDB_commonuse_delete(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除mysql通用Table的指定多筆或單筆資料服務(department/site/place/device/sensor，此五個表不適用)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "資料表主鍵欄位":{"type":"Array","requirement":"optional","directions":"欲刪除的資料表主鍵值","example":"['value1','value2',...]"},
            "timeflag":{ "type":"Object","requirement":"optional","directions":"時間條件標記；key必為時間屬性欄位，若value只有一個值，系統自動抓取value[0]到現在時間之區間","example":"{'時間欄位':['起始時間','結束時間']}"},
            "precautions":{
                "注意事項1":
                    "若要以時間條件進行刪除再使用'timeflag'參數，資料表主鍵欄位就無需再post，若同時存在則以'timeflag'為優先",
                "注意事項2":
                    "若使用'timeflag'參數，系統一次只接受一個時間條件",
                "注意事項3":
                    "資料表要刪除的主鍵欄位為條件式輸入，不一定要所有主鍵都post，可一次刪除多筆資料"
            },
            "example":[{"id":[1,2,3]},{"timeflag":["2020-07-09 14:23:10","2020-07-09 17:23:10"]}]
        },
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","deletestatus":"string+各筆資料刪除狀態，若全部刪除成功則無此Response"},
        "API_example":{
            "APIS": "DELETE /api/VUESYSTEM/1.0/my/CommonUse/VUESYSTEMgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if  tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device" or tableName == "sensor":
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)
    
    #是否有使用time參數
    timeflag = False
    #多筆資料刪除的狀態
    deletestatus = [] 
    deletestatusmsg = ""

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,SYSTEM)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        keyList = desc_table_return[2]

        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        if not VerifyDataStrLawyer(request.data).verify_json():
            dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
            return jsonify( **dicRet)

        #collect data items from a request
        reqdataDict = json.loads(request.data)
        if isinstance(reqdataDict,type(u"")):
            reqdataDict = json.loads(reqdataDict)

        deletetargetTable = Table(tableName , metadata, autoload=True)

        #判斷是否有使用time參數
        if reqdataDict.get("timeflag") is not None:
            timeflag = True
            if not isinstance(reqdataDict.get("timeflag"),dict):
                dicRet["Response"] = "Error type of '{}',it must be an Object".format(reqdataDict.get("timeflag"))
                return jsonify( **dicRet)
            
            if len(reqdataDict.get("timeflag").keys()) > 1:
                dicRet["Response"] = "系統只接受一個時間欄位"
                return jsonify( **dicRet)
            
            if reqdataDict.get("timeflag").keys()[0] not in fieldList:
                dicRet["Response"] = "時間欄位 '{}' 不存在".format(reqdataDict.get("timeflag").keys()[0])
                return jsonify( **dicRet)

            where_time_attr = getattr(deletetargetTable.c,reqdataDict.get("timeflag").keys()[0])

            timevalue = reqdataDict.get("timeflag").values()[0]
            if not isinstance(timevalue,list):
                dicRet["Response"] = "Error type of '{}',it must be an Array".format(timevalue)
                return jsonify( **dicRet)
            
            if not timevalue:
                dicRet["Response"] = "error 'timeflag' parameter input, '{}' can't Null".format(timevalue)
                return jsonify( **dicRet)

            #判斷timevalue[0],timevalue[1]皆為合法時間字串
            for timestr in timevalue:
                if not VerifyDataStrLawyer(timestr).verify_date():
                    dicRet["Response"] = "error 'timeflag' parameter input, date str '{}' is illegal".format(timestr)
                    return jsonify( **dicRet)

            where_time_start = timevalue[0]

            if len(timevalue) == 1:
                where_time_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                if datetime.strptime(timevalue[1], "%Y-%m-%d %H:%M:%S") < datetime.strptime(timevalue[0], "%Y-%m-%d %H:%M:%S"):
                    dicRet["Response"] = "error 'timeflag' parameter input, start date str '{}' need smaller than end date str '{}'".format(timevalue[0],timevalue[1])
                    return jsonify( **dicRet)

                where_time_end = timevalue[1]
        
        if timeflag:
            sess.execute(deletetargetTable.delete().where(between(where_time_attr,where_time_start,where_time_end)))
            sess.commit()
            err_msg = "ok"
        else:
            #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
            postKeyList = []
            #檢查是否主鍵Data數量相同
            setPKdatanum = ""

            if not keyList:
                dicRet["Response"] = "Error 此資料表找不到主鍵"
                return jsonify( **dicRet)

            for i in range(len(keyList)):
                if reqdataDict.get(keyList[i]) is not None:
                    if not isinstance(reqdataDict.get(keyList[i]),list):
                        dicRet["Response"] = "Error type of '{}',it must be an Array".format(keyList[i])
                        return jsonify( **dicRet)

                    #把unicode list 轉成 str list，才能抓到list內的各內容
                    postDataKEYtostrList = map(str,reqdataDict.get(keyList[i]))
                    
                    #判斷主鍵為空陣列回覆error
                    if not postDataKEYtostrList:
                        dicRet["Response"] = "primary key {} can't be None".format(keyList[i])
                        return jsonify( **dicRet)

                    postDataCount = len(postDataKEYtostrList)
                    #第一次for loop PRI，確定輸入的主鍵資料數量是相同的
                    if isinstance(setPKdatanum,str):
                        setPKdatanum = postDataCount
                    else:
                        if setPKdatanum != postDataCount:
                            dicRet["Response"] = "The number of input data does not match"
                            return jsonify( **dicRet)
                        
                    for j in range(len(postDataKEYtostrList)):
                        query_field = getattr(deletetargetTable.c,keyList[i])
                        postKeyList.append('({} = \"{}\")'.format(query_field,postDataKEYtostrList[j]))
                        # #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                        # postKeyList.append('({} = \"{}\")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))

            #檢查是否都沒input PRI
            if len(postKeyList) == 0:
                dicRet["Response"] = "At least one primary key is necessary"
                return jsonify( **dicRet)

            #每一筆刪除資料的where條件陣列
            whereDict = [] 
            for i in range(postDataCount):
                #以間隔方式一一抓取
                whereDict.append(postKeyList[i::postDataCount])

            #每一筆刪除資料的where條件str
            for i in range(len(whereDict)):
                check_data_existed = False
                #以&來join陣列
                whereStr = " & ".join(whereDict[i])
                for row in sess.execute(deletetargetTable.select(text(whereStr))):
                    check_data_existed = True

                if check_data_existed:
                    sess.execute(deletetargetTable.delete().where(text(whereStr)))
                    sess.commit()
                else:
                    deletestatus.append(whereStr)
            err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if len(deletestatus) != 0:
        #以,來join陣列
        deletestatusmsg = "Error: {} ID ({}) isn't existed".format(tableName," , ".join(deletestatus))
        dicRet["deletestatus"] = deletestatusmsg

    dicRet["timeflag"] = timeflag
    dicRet["Response"] = err_msg 
    dicRet["Table"] = tableName 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse delete
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.5/my/CommonUse/<tableName>', methods = ['DELETE'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.5/my/CommonUse/<tableName>', methods = ['DELETE'])
@decorator_check_legal_system()
def transitionDB_commonuse_delete_v1_5(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除mysql通用Table的指定多筆或單筆資料服務(department/site/place/device/sensor，此五個表不適用)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "資料表主鍵欄位":{"type":"Array","requirement":"optional","directions":"欲刪除的資料表主鍵值","example":"['value1','value2',...]"},
            "timeflag":{ "type":"Object","requirement":"optional","directions":"時間條件標記；key必為時間屬性欄位，若value只有一個值，系統自動抓取value[0]到現在時間之區間","example":"{'時間欄位':['起始時間','結束時間']}"},
            "precautions":{
                "注意事項1":
                    "若要以時間條件進行刪除再使用'timeflag'參數，資料表主鍵欄位就無需再post，若同時存在則以'timeflag'為優先",
                "注意事項2":
                    "若使用'timeflag'參數，系統一次只接受一個時間條件",
                "注意事項3":
                    "資料表要刪除的主鍵欄位為條件式輸入，不一定要所有主鍵都post，可一次刪除多筆資料"
            },
            "example":[{"id":[1,2,3]},{"timeflag":["2020-07-09 14:23:10","2020-07-09 17:23:10"]}]
        },
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","deletestatus":"string+各筆資料刪除狀態，若全部刪除成功則無此Response"},
        "API_example":{
            "APIS": "DELETE /api/VUESYSTEM/1.5/my/CommonUse/VUESYSTEMgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if  tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device" or tableName == "sensor":
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)
    
    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        result = commonuse_delete_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, "mysql")
        err_msg = result[0]

        if len(result) == 2:
            dicRet["deletestatus"] = result[1]

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg 
    dicRet["Table"] = tableName 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse query schema
# Date: 09022019@Yishan
# FOR MYSQL
#=======================================================
# {{{ TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/Schema/<tableName>', methods = ['GET'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/Schema/<tableName>', methods = ['GET'])
@decorator_check_legal_system()
#@DecoratorCheckUriParameterExist(request,["uid"]) #利用裝飾器檢查
def transitionDB_commonuse_get_tableschema(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql通用Table的欄位屬性",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"DB":"string","Table":"string","schemaList":"array"},
        "API_example":{
            "APIS": "POST /api/VUESYSTEM/1.0/my/CommonUse/Schema/user",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL",
            "Table":"user",
            "schemaList": [{"comment": "\u5834\u57df\u7de8\u865f", "primary_key": true, "type": "VARCHAR(15)", "name": "placeID", "nullable": false}, {"comment": "\u5834\u57df\u540d\u7a31", "primary_key": false, "type": "VARCHAR(128)", "name": "placeName", "nullable": true}, {"comment": "\u5275\u5efa\u8005ID", "primary_key": false, "type": "VARCHAR(24)", "name": "creatorID", "nullable": true}, {"comment": "\u5275\u5efa\u6642\u9593", "primary_key": false, "type": "TIMESTAMP", "name": "created_at", "nullable": false}, {"comment": "\u6700\u5f8c\u4fee\u6539\u6642\u9593", "primary_key": false, "type": "TIMESTAMP", "name": "updated_at", "nullable": false}]
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    try:
        schema_notime_List = []
        schema_time_List = []
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        metadata.reflect(only=[tableName])
        for table in metadata.tables.values():
            if table.name == tableName:
                for column in table.c:
                    schemaDict = {}
                    thistype = str(column.type).split(" COLLATE ")[0]
                    #判斷欄位是否為json，MYSQL裡的json型態為LONGTEXT.....
                    if re.search(r'LONGTEXT.',thistype):
                        thistype = "JSON"

                    schemaDict["tablename"] = tableName
                    schemaDict["tablecomment"] = table.comment
                    schemaDict["name"] = column.name
                    schemaDict["type"] = thistype
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

                    if column.name == globalvar.CREATETIME[globalvar.SERVERIP]["mysql"] or column.name == globalvar.UPLOADTIME[globalvar.SERVERIP]["mysql"]:
                        schema_time_List.append(schemaDict)
                    else:
                        schema_notime_List.append(schemaDict)

        #https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        schema_notime_List = sorted(schema_notime_List, key=lambda k: k['primary_key'],reverse=True) 
        schema_notime_List.extend(schema_time_List)

        dicRet['schemaList'] = schema_notime_List
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()

    dicRet["Table"] = tableName 
    dicRet["Response"] = err_msg 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# Definition: backup mysql table
# Date: 09032019@Yishan
# 1. To backup data table
#=======================================================
#{{{ @TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/BackUp/<tableName>',  methods = ['GET'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/BackUp/<tableName>',  methods = ['GET'])
@decorator_check_legal_system()
def transitionDB_commonuse_backup_mysql_table(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供mysql以created_at(年)為條件來備份及刪除單一資料表基本資料服務",
        "API_parameters":{"uid":"使用者帳號","year":"西元年份"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","backupYear":"string"},
        "API_example":{
            "APIS": " GET /api/VUESYSTEM/1.0/my/CommonUse/BackUp/user",
            "BytesTransferred": 523,
            "OperationTime":"0.014",
            "Response": "ok",
            "Table":"user",
            "DB":"MYSQL",
            "backupYear":"2019"
        }
    }
    '''
    #}}}
    err_msg = "ok"
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
        else:
            reqdataDict = json.loads(request.data)
            # currently support [0-9] but not [\d] because escape char '\' in json dumps/loads
            # TODO: support \d \s and so on syntax in regular expression
    #end of err_msg check

    BACKUP_DIR = '/var/www/html/{}/sqlbackup/mysql'.format(SYSTEM)
    #Yishan@09032019 check BACKUP_DIR is existed or mkdir
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    os.chdir(BACKUP_DIR)    

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,SYSTEM):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)
        
        start_year = year+"-01-01 00:00:00"
        end_year = year+"-12-31 23:59:59" 
                    
        query_table = Table(tableName , metadata, autoload=True)
        query_field = getattr(query_table.c, globalvar.CREATETIME[globalvar.SERVERIP]["mysql"])

        check_data_existed = False
        for row in sess.query(query_table).filter(query_field.between(start_year,end_year)).all():
            check_data_existed = True

        if not check_data_existed:
            dicRet["Response"] = "There is no matching data for your query"
            return jsonify( **dicRet)

        #Yishan@09032019 mysqldump默認會設置時區SET TIME_ZONE='+00:00'，所以會使where條件查不到，使用--skip-tz-utc ->禁止mysqldump設置時區
        sqldump_cmd = '/usr/bin/mysqldump -uroot -psapido {} {} --single-transaction --skip-tz-utc --where="{} between \'{}\' and \'{}\'"> {}'.format(dicConfig.get("DBMYSQLDbname_"+SYSTEM),tableName,globalvar.CREATETIME[globalvar.SERVERIP]["mysql"],start_year,end_year,tableName+'_'+year+'.sql')
        try:
            subprocess.check_output(sqldump_cmd,shell=True,stderr= subprocess.STDOUT)  
            err_msg = del_backup_tabledata(SYSTEM,sess,query_table,start_year,end_year)
            if err_msg == "ok": 
                #Yishan@09032019 改變sql備份的表名，固定為temporary_xxx
                #sed精準匹配 https://zhidao.baidu.com/question/510527829.html https://blog.csdn.net/yychenxie21/article/details/52919009 
                change_tablename_cmd = "/bin/sed -i 's/\<{}\>/{}/g' {}".format(tableName,'temporary_'+tableName+'_'+year,tableName+'_'+year+'.sql')
                try:
                    subprocess.check_output(change_tablename_cmd,shell=True,stderr= subprocess.STDOUT)
                except subprocess.CalledProcessError as d:
                    err_msg = '<commonuse_backup_mysql_changename>Unexpected error: 備份檔改名失敗'
                    appPaaS.catch_exception(d.output,sys.exc_info(),SYSTEM)
        except subprocess.CalledProcessError as e:
            err_msg = '<commonuse_backup_mysql_data>Unexpected error: 備份失敗'
            appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["backupYear"] = year
    dicRet["Response"] = err_msg
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL"
    return jsonify( **dicRet)
#}}}

#=======================================================
# Definition: to create temporary table to show mysql history backup data
# Date: 09032019@Yishan
#=======================================================
#{{{ @TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/BackUpData/<sqlfilename>',  methods = ['GET'])
@TRANSITIONDB_API.route('/api/<SYSTEM>/1.0/my/CommonUse/BackUpData/<sqlfilename>',  methods = ['GET'])
@decorator_check_legal_system()
def transitionDB_commonuse_get_mysql_backupdata(SYSTEM,sqlfilename):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql備份歷史資料服務(以季為單位來做查詢)",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","sqlfilename":"sql備份檔名稱"},
        "API_parameters":{"uid":"使用者帳號","quarter":"季(範圍:正整數0~4，0為整年資料)"},
        "API_message_parameters":{"DB":"string","backupfile":"string","backupData":"JSON","quarter":"string"},
        "API_example":{
            "APIS": " GET /api/VUESYSTEM/1.0/my/CommonUse/BackUpData/workorder_2019",
            "BytesTransferred": 523,
            "OperationTime":"0.014",
            "Response": "ok",
            "backupfile":"workorder_2019.sql",
            "backupData":[{"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 1, "devID": "1", "workID": "1", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "1"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 2, "devID": "2", "workID": "2", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "2"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 3, "devID": "3", "workID": "3", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "3"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 4, "devID": "4", "workID": "4", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "4"}, {"updated_at": "2019-09-04 10:37:59", "uwire": "JSON", "wqty": 5, "devID": "5", "workID": "5", "created_at": "2019-09-04 10:37:59", "umold": "JSON", "prodID": "5"}],
            "quarter":0,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    err_msg = "ok"
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
        else:
            reqdataDict = json.loads(request.data)
            # currently support [0-9] but not [\d] because escape char '\' in json dumps/loads
            # TODO: support \d \s and so on syntax in regular expression
    #end of err_msg check


    BACKUP_DIR = '/var/www/html/{}/sqlbackup/mysql'.format(SYSTEM)
    os.chdir(BACKUP_DIR)
    #Yishan@09032019 check BACKUP_DIR is existed or mkdir
    if not os.path.isfile(sqlfilename+'.sql'):
        dicRet["Response"] = "file: '{}.sql' is not existed".format(sqlfilename)
        return jsonify( **dicRet)
    
    try:
        #Yishan@09042019 匯入sql備份，並進行select查詢
        sql_cmd = '/usr/bin/mysql -uroot -psapido {} < {}'.format(dicConfig.get("DBMYSQLDbname_"+SYSTEM),sqlfilename+".sql")
        subprocess.check_output(sql_cmd,shell=True,stderr= subprocess.STDOUT)
        dicRet["backupData"],err_msg = qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,quarter,True)
        #移除暫時表
        _,err_msg = qrydel_backup_temporary_tabledata(SYSTEM,sqlfilename,"",False)

    except subprocess.CalledProcessError as e:
        err_msg = '<commonuse_get_mysql_backupdata>Unexpected error: 還原失敗'
        appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)

    dicRet["quarter"] = quarter
    dicRet["Response"] = err_msg
    dicRet["backupfile"] = sqlfilename+".sql"
    dicRet["DB"] = "MYSQL"
    return jsonify( **dicRet)
#}}}