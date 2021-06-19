# -*- coding: utf-8 -*-
#CommonUse module description
"""
==============================================================================
created    : 
Last update: 03/31/2021
Developer: Yi-Shan Tsai 
Lite Version 2 @Yishan08212019
API Version 1.0

Filename: commonuseHandle.py

Description: 

Total = 11 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
# {{{
from sqlalchemy import *
import hmac, hashlib
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
COMMONUSE_APIDOC_API = Blueprint('COMMONUSE_APIDOC_API', __name__)

#=======================================================
# CommonUse
# special API to query time, 
#=======================================================
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/CommonUse/Time', methods = ['GET']), 
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/CommonUse/Time',  methods = ['GET'])
def commonuse_get_time():
    #{{{APIINFO
    '''
    {
        "API_name":"GET /api/APIDOC/1.0/CommonUse/Time",
        "API_application":"查詢現在時間",
        "API_message_parameters":{"time":"string"},
        "API_example":{
            "OperationTime": "0.000",
            "BytesTransferred": 72,
            "time": "2019-08-08 10:21:40",
            "Response": "ok",
            "APIS": "GET /api/APIDOC/1.0/CommonUse/Time"
        }
    }
    '''
    #}}}
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="YS")
    #if(reUser_id in "AceMoriKTGH"):
    err_msg = dicRet["Response"]
    try:
        dicRet['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        err_msg = "ok" 
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

    dicRet["Response"] = err_msg
    return jsonify( **dicRet)
# }}}

#=======================================================
# CommonUse
# special API to query all tables 
# FOR MYSQL
#=======================================================
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/TableData', methods = ['GET']), 
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/TableData',  methods = ['GET'])
def commonuse_get_tabledata():
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","table":"欲查詢之資料表名稱"},
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " GET /api/APIDOC/1.0/my/CommonUse/TableData",
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
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="YS")
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
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)

        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
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
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
# CommonUse
# API: '/api/APIDOC/1.0/my/CommonUse/queryRows/interval/<tableID>'
# Definition: query the first and last between value of param
# Date: 0214-2019
# Who: Wei
# Note: 1. could be same value
#       2. only single attribute value will be retrieved
# FOR MYSQL
#=======================================================
#{{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/Interval/<tableID>', methods = ['GET']), 
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/Interval/<tableID>',  methods = ['GET'])
def commonuse_get_multi_rows_interval(tableID):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql資料表資料內容的一個範圍",
        "API_path_parameters":{"tableID":"資料表名稱"},
        "API_parameters":{
            "uid":"使用者帳號",
            "attr":"資料屬性名稱",
            "valueStart":"欲查詢資料起始值",
            "valueEnd":"欲查詢資料終端值"
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " GET /api/APIDOC/1.0/my/CommonUse/Interval/department",
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
                "depname": "sapidoAPIDOC",
                "depID": "sapidoAPIDOC",
                "dbName": "sapidoAPIDOC"
            }],
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    err_msg = "ok"
    dicRet = appPaaS.preProcessRequest(request,system="YS")
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
    vs  = request.args.get("valueStart")
    valuestart   = vs.encode('utf-8')
    ve   = request.args.get("valueEnd")
    valueend   = ve.encode('utf-8')

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
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        query_table = Table(tableName , metadata, autoload=True)
        query_field = getattr(query_table.c, attr)

        for row in sess.query(query_table).filter(query_field.between(valuestart,valueend)).all():
            drow = AdjustDataFormat().format(row._asdict())
            for key,value in drow.items():
                if key=="pwd": #for user to AES_DECRYPT pwd
                    AES_IV = valuestart
                    AES = Prpcrypt(dicConfig.get('aes_key'), AES_IV, "APIDOC")
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
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax/<tableName>', methods = ['POST']), 
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax/<tableName>',  methods = ['POST'])
def commonuse_get_sqlsyntax(tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql資料表資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"tableName":"資料表名稱"},
        "API_postData":{
            "注意事項":"where條件不支援json欄位",
            "parameters":{
                "purpose":"類型：string，欲查詢select方式(query|query_or|query_like，只接受這3種參數)",
                "fields":"類型：array，查詢欄位名稱參數(ex: ['x','y','z',......])",
                "where":"類型：object，查詢條件參數(ex: {'key':'value',.....})；若是使用query_or，物件裡的value以array型態post",
                "orderby":"類型：array，查詢排序參數(ex: ['desc(asc)','x','y','z',.....])",
                "limit":"類型：array，查詢筆數限制參數(ex: [1,10])，只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，如需查詢所有資料使用['ALL'],若無設定則預設查100筆",
                "symbols":"類型：object，sql比較運算子，value只有「equal(=) | notequal(!=) | greater(>) | less(<)」這四種運算子，且key必須與where的key相同(ex:{key:'equal',...})，使用purpose->query時，才需使用此參數，其他皆放''即可"
            }
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " POST /api/APIDOC/1.0/my/CommonUse/SqlSyntax/user",
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
    dicRet = appPaaS.preProcessRequest(request,system="YS")
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
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        query_table = Table(tableName , metadata, autoload=True)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,"APIDOC")
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
                err_msg = "error 'fields' parameter input, can't Null"
                dicRet["Response"] = err_msg
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
        wheredictforqueryAnd = {}
        wheredictforquery = {}
        whereorList = []
        if where != "":
            if len(where) == 0:
                err_msg = "error 'where' parameter input, can't Null"
                dicRet["Response"] = err_msg
                return jsonify( **dicRet)

            if purpose == "query":
                if symbols == "":
                    err_msg = "error 'symbols' parameter input, can't Null"
                    dicRet["Response"] = err_msg
                    return jsonify( **dicRet)

                if len(symbols) != len(where):
                    err_msg = "The number of {} data does not match {}" .format(symbols,where)
                    dicRet["Response"] = err_msg
                    return jsonify( **dicRet)

            #比較運算子轉換
            operator = {"equal":"=","notequal":"!=","greater":">","less":"<"}
            operatorList = ["equal","notequal","greater","less"]
            #unicode dict change to str dict
            wheretoStrDict = ConvertData().convert(where)
            symbolstoStrDict = ConvertData().convert(symbols)

            for key,value in wheretoStrDict.items():
                #判斷where進來的key是否與資料表欄位相符
                if not key in fieldList: 
                    err_msg = "Unknown column \'{}\' in 'field list'".format(key)
                    dicRet["Response"] = err_msg
                    return jsonify( **dicRet)
                
                if schemaDict[key] == "JSON": 
                    err_msg = "where condition does not support json field '{}'".format(key)
                    dicRet["Response"] = err_msg
                    return jsonify( **dicRet)

                #只有purpose為query_or時，value才能為list，否則return
                if purpose != "query_or" and isinstance(value,list):
                    err_msg = "error type of input {}, it must be a string".format(value)
                    dicRet["Response"] = err_msg
                    return jsonify( **dicRet)

                if purpose == "query_like":
                    wheredictforquertLike[key] = "%{}%".format(value)
                elif purpose == "query_or":
                    if not isinstance(value,list):
                        err_msg = "error type of input {}, it must be a list".format(value)
                        dicRet["Response"] = err_msg
                        return jsonify( **dicRet)

                    if len(value) == 0:
                        err_msg = "error 'where' parameter input {},can't be a Null Array".format(value)
                        dicRet["Response"] = err_msg
                        return jsonify( **dicRet)

                    if len(value) > 1:
                        whereor = or_(*(getattr(query_table.c,key) == value[o]for o in range(len(value))))
                        whereorList.append(whereor)
                    else:
                        wheredictforqueryAnd[key] = value[0]
                else:
                    if symbolstoStrDict.get(key) is None:
                        err_msg = "The symbol key \'{}\' does not match {}" .format(symbolstoStrDict.keys(),key)
                        dicRet["Response"] = err_msg
                        return jsonify( **dicRet)

                    if not isinstance(symbolstoStrDict[key],str):
                        err_msg = "error 'symbols value {}' parameter must be a string".format(symbolstoStrDict[key])
                        dicRet["Response"] = err_msg
                        return jsonify( **dicRet)
                    
                    if symbolstoStrDict[key] not in operatorList:
                        err_msg = "error 'symbols' parameter input \'{}\', not in {}" .format(symbolstoStrDict[key],operatorList)
                        dicRet["Response"] = err_msg 
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
                err_msg = "error 'orderby' parameter input, can't Null"
                dicRet["Response"] = err_msg
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
            finalquerywhere = and_(and_(*((between(getattr(query_table.c,key),value[0],value[1]))for key,value in wherentervaltime.items())),
                                *((getattr(query_table.c,key).like(value))for key,value in wheredictforquertLike.items())\
                                )

        elif purpose == "query_or":
            finalquerywhere =  and_(and_(*(i for i in whereorList)),
                                    and_(*((between(getattr(query_table.c,key),value[0],value[1]))for key,value in wherentervaltime.items())),
                                    *((getattr(query_table.c,key) == value)for key,value in wheredictforqueryAnd.items())\
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
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
# {{{ COMMONUSE_APIDOC_API.route('/APIDOC/1.0/my/CommonUse/SqlSyntax_', methods = ['POST']), 
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax_',  methods = ['POST'])
def commonuse_get_sqlsyntax_():
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "precautions": {
                "注意事項1":"parameters內的固定格式key為：condition_x，其中的x為數字(1~x)，至少必須有condition_1；若有子查詢，parameters內的key繼續往下新增",
                "注意事項2":"where value條件不支援json欄位但提供子查詢",
                "注意事項3":"當有以下情況時:要同時查詢A欄位值為a1、a2與B欄位值為b1且A欄位值a3與B欄位值b2時，在where條件內使用'combine'參數(Array)，以上述情況為例的where使用方法為(接續注意事項3)",
                "注意事項4":{"where":{"combine":[{"A欄位":["a1","a2"],"B欄位":["b1"]},{"A欄位":["a3"],"B欄位":["b2"]}]}},
                "注意事項5":"'combine'參數格式為：同時幾筆條件以物件方式包在陣列內，物件格式為{'field':['value',....]}",
                "注意事項6":"where若有子查詢需求，value格式為字串且必須為condition_x({'where':{'key':'condition_2'},'symbol':{'key':'in'}})，其中x必不能小於原本父親key的x，例如：在condition_1內有子查詢，接續condition_x的x不得小於1，詳例查看example3,4,5",
                "注意事項7":"where子查詢查詢回來的欄位必須只有一個"
            },
            "parameters":{
                "table":{"type":"String","requirement":"required","directions":"欲查詢的資料表名稱","example":"sensor"},
                "fields":{"type":"Array","requirement":"required","directions":"查詢欄位名稱參數","example":"['id','name','z',......]"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；物件裡的value皆以array型態post(預設以query_or查詢)，若有特殊or需求請看注意事項3,4,5；若需使用子查詢請看注意事項6,7","example":"{'field':['value',....],.....}"},
                "orderby":{"type":"Array","requirement":"required","directions":"查詢排序參數","example":"['desc(asc)','id','name','z',.....]"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，如需查詢所有資料使用['ALL'],若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；物件裡的value皆以array型態post，value只有「equal(=) | notequal(!=) | greater(>) | less(<) | like(like) | in(in) | notin(notin)」這七種運算子，且key必須與where的key相同","example":"{key:['equal',....],...}"},
                "intervaltime":{"type":"Object","requirement":"required","directions":"查詢指定間段時間；key必為時間屬性欄位，value為陣列，陣列內有幾個時間條件陣列(格式為['起始時間','結束時間'])以or方式連接查詢，不同時間條件以and方式連接查詢；無需使用此參數放''即可","example":"{'created_at':[['2020-07-09 15:55:55','2020-07-09 18:00:00'],[],....],'updated_at':[['2020-07-28 10:00:00','2020-07-28 12:00:00'],[],...],....}"}
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
                            "intervaltime":""
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
                            "intervaltime":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":"condition_2","sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":"in","sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}]
                            },
                            "orderby":"",
                            "intervaltime":""
                        },
                    "condition_2":
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
                            "intervaltime":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":"condition_2","sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":"condition_3"
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":"in","sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}],
                                "noumenon_id":"in"
                            },
                            "orderby":"",
                            "intervaltime":""
                        },
                    "condition_2":
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
                            "intervaltime":""
                        },
                    "condition_3":
                        {
                            "table":"department",
                            "fields":["department_id"],
                            "where":"",
                            "limit":"",
                            "symbols":"",
                            "orderby":"",
                            "intervaltime":""
                        }
                },
                {
                    "condition_1":
                        {
                            "table":"sensor",
                            "fields":["id","name","noumenon_type","noumenon_id"],
                            "where":{
                                "combine":[{"noumenon_id":"condition_2","sensor_raw_table":["work_code_use","f12"]},{"sensor_type":[1],"sensor_raw_table":["work_code_abn","test"]}],
                                "noumenon_id":[1]
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"noumenon_id":"in","sensor_raw_table":["equal","equal"]},{"sensor_type":["equal"],"sensor_raw_table":["equal","equal"]}],
                                "noumenon_id":["equal"]
                            },
                            "orderby":"",
                            "intervaltime":""
                        },
                    "condition_2":
                        {
                            "table":"site",
                            "fields":["site_id"],
                            "where":{
                                "combine":[{"creator":[1],"db_name":["site2","test"]},{"modifier":[1],"name":["久陽二廠","test"]}],
                                "site_id":"condition_3"
                            },
                            "limit":"",
                            "symbols":{
                                "combine":[{"creator":["equal"],"db_name":["equal","equal"]},{"modifier":["equal"],"name":["equal","equal"]}],
                                "site_id":"in"
                            },
                            "orderby":"",
                            "intervaltime":""
                        },
                    "condition_3":
                        {
                            "table":"department",
                            "fields":["department_id"],
                            "where":"",
                            "limit":"",
                            "symbols":"",
                            "orderby":"",
                            "intervaltime":""
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
                }
            ]
        },
        "API_message_parameters":{"Table":"string","QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": " POST /api/APIDOC/1.0/my/CommonUse/SqlSyntax/user",
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
    dicRet = appPaaS.preProcessRequest(request,system="YS")
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
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)

        sess = DbSession()

        sqlsyntax_actions_status,sqlsyntax_actions_result = sqlsyntax_params_actions(action_result,"condition_1",reqdataDict,sess,metadata,"mysql",False,"APIDOC")
        if not sqlsyntax_actions_status:
            dicRet["Response"] = sqlsyntax_actions_result
            return jsonify( **dicRet)
        
        if request.args.get("getSqlSyntax") == "yes":
            dicRet['SqlSyntax'] = str(sqlsyntax_actions_result[1].compile(compile_kwargs={"literal_binds": True}))

        dicRet['QueryTableData'] = sqlsyntax_actions_result[0]
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
#{{{ @COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax/JoinMultiTable',  methods = ['POST'])
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax/JoinMultiTable',  methods = ['POST'])
def commonuse_get_sqlsyntax_joinmultitable():
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql join資料表資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "注意事項1":"為避免多表join後有些欄位名稱一樣被覆蓋掉，系統統一將資料查詢結果回傳值的key訂為'table$column'",
            "注意事項2":"where條件與join條件不支援json欄位",
            "parameters":{
                "purpose":"類型：string，欲查詢select方式(query|query_or|query_like，只接受這3種參數)",
                "fields":"類型：object，查詢欄位名稱參數(ex: {'table':['table_column1','table_column2',....]})",
                "where":"類型：object，查詢條件參數(ex: {'table':{'table_column':'value'},.....})；若是使用query_or，物件裡的value以array型態post",
                "jointype":"類型：string，欲sql join方式(inner|left，只接受這2種參數)",
                "join":"類型：object，join多表(ex: {'主表':[{'欲JOIN的表(表1)':{'主表column1':'欲JOIN表的column1', '主表column2':'欲JOIN表的column2', 'JOIN':{'欲與表1JOIN的表(表2)':{'表1column':'表2cloumn'}}......}},.......]}),最多只能有一個主表且若是使用left join，放入的順序會影響查詢結果",
                "limit":"類型：array，查詢筆數限制參數(ex: [1,10])，只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，若無設定則預設查100筆",
                "symbols":"類型：object，sql比較運算子，value只有「equal(=) | notequal(!=) | greater(>) | less(<)」這四種運算子，且key必須與where的key相同和value的table_column必須與where的table_column相同(ex:{'table':{'table_column':'equal'},.....})，使用purpose->query時，才需使用此參數，其他皆放''即可",
                "tables":"類型：array，需要join的tablename(ex: ['table1','table2',.....])",
                "orderby":"類型：array，查詢排序參數(ex: ['desc(asc)','table','column','table2','column',.....])"
            }
        },
        "API_message_parameters":{"QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": "POST /api/APIDOC/1.0/my/CommonUse/SqlSyntax/JoinMultiTable",
            "OperationTime": "0.298",
            "BytesTransferred": 353,
            "DB": "MSSQL",
            "System": "APIDOC",
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
    dicRet = appPaaS.preProcessRequest(request,system="YS")
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
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
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
                err_msg = "至少要有兩個table"
                dicRet["Response"] = err_msg
                return jsonify( **dicRet)

            for i in range(len(tables)):
                if not retrieve_table_exist(metadata,tables[i],"APIDOC"):
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

                desc_table_return = desc_table(metadata,fieldskey,"APIDOC")
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
                desc_table_return = desc_table(metadata,tables[i],"APIDOC")
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
            response, msg, key, value = adjust_dict_for_joinapi(metadata=metadata,tables=tables,masterKey=joinkeyList0,data=i,joinkeyList=joinkeyList,joincolumnList=joincolumnList,system="YS")
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
                desc_table_return = desc_table(metadata,wherekey,"APIDOC")
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]
                keyList = desc_table_return[2]
                schemaDict = desc_table_return[3]

                if desc_table_status != 'ok':
                    dicRet["Response"] = desc_table_status
                    return jsonify( **dicRet)

                for wherevalue_key,wherevalue_value in wherevalue.items():
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

                        wheredictforquery[wherevalue_key] = ["{} = '{}'".format(getattr(Table(wherekey ,metadata, autoload=True).c,wherevalue_key),wherevalue_value[o])for o in range(len(wherevalue_value))]
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
                    desc_table_return = desc_table(metadata,orderby[i-1],"APIDOC")
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
                if not isinstance(joincolumnList[i],list):
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i] ,metadata, autoload=True), \
                            getattr(Table(joinkeyList0 ,metadata, autoload=True).c,joincolumnList[i+setjump]) == \
                            getattr(Table(joinkeyList[i] ,metadata, autoload=True).c,joincolumnList[i+1+setjump]),isouter=isouter)
                    setjump += 1
                else:
                    joinandsql = and_(*(((getattr(Table(joinkeyList0 ,metadata, autoload=True).c,joincolumnList[i+setjump][u]) == \
                            getattr(Table(joinkeyList[i],metadata, autoload=True).c,joincolumnList[i+setjump][u+1])))for u in range(0,len(joincolumnList[i+setjump]),2)))
                    if setjump != 0:
                        setjump -= 1
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i] ,metadata, autoload=True),joinandsql,isouter=isouter)
            else:
                if not isinstance(joincolumnList[i],list):
                    wherejoinSql = wherejoinSql.join(Table(joinkeyList[i][1] ,metadata, autoload=True), \
                            getattr(Table(joinkeyList[i][0],metadata, autoload=True).c,joincolumnList[i+setjump]) == \
                            getattr(Table(joinkeyList[i][1] ,metadata, autoload=True).c,joincolumnList[i+1+setjump]),isouter=isouter)
                    setjump += 1
                else:
                    joinandsql = and_(*(((getattr(Table(joinkeyList[i][0] ,metadata, autoload=True).c,joincolumnList[i+setjump][u]) == \
                            getattr(Table(joinkeyList[i][1],metadata, autoload=True).c,joincolumnList[i+setjump][u+1])))for u in range(0,len(joincolumnList[i+setjump]),2)))
                    if setjump != 0:
                        setjump -= 1
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
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
#{{{ @COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax/JoinMultiTable_',  methods = ['POST'])
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/SqlSyntax/JoinMultiTable_',  methods = ['POST'])
def commonuse_get_sqlsyntax_joinmultitable_():
    #{{{APIINFO
    '''
    {
        "API_application":"提供sql語法查詢mysql join資料表資料服務",
        "API_parameters":{"uid":"使用者帳號","getSqlSyntax":"是否抓取此次查詢的sql語法(yes/no)"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{'condition_1':{}}",
            "parameters":{
                "fields":{"type":"Object","requirement":"required","directions":"查詢欄位名稱參數","example":"{'table':['table_column1','table_column2',....]}"},
                "where":{"type":"Object","requirement":"required","directions":"查詢條件參數；物件裡的value皆以array型態post；若有特殊or需求請看注意事項3,4,5；可為null","example":"{'table':{'table_column':['value',....],...},.....}"},
                "jointype":{"type":"Object","requirement":"required","directions":"欲sql join方式，key為'主表'_'欲JOIN的表(表1)'，value有「inner｜left」，這2種參數","example":{"site_sensor":"left","sensor_place":"inner","site_user":"inner"}},
                "join":{"type":"Object","requirement":"required","directions":"join多表表達式；最多只能有一個主表；可為null(請查看注意事項6)","example":"{'主表':[{'欲JOIN的表(表1)':{'主表column1':'欲JOIN表的column1', '主表column2':'欲JOIN表的column2', 'JOIN':{'欲與表1JOIN的表(表2)':{'表1column':'表2cloumn'}}......}},.......]}"},
                "limit":{"type":"Array","requirement":"required","directions":"查詢筆數限制參數；只接受2個數字(第一個數字為從第幾筆開始查，第二個數字為總共要查幾筆)，若無設定則預設查100筆","example":"[1,10]"},
                "symbols":{"type":"Object","requirement":"required","directions":"sql比較運算子；物件裡的value皆以array型態post，value只有「equal(=) | notequal(!=) | greater(>) | less(<) | like(like) | in(in) | notin(notin)」這七種運算子，且key必須與where的key相同","example":"{'table':{'table_column':['equal',...],...},.....}"},
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
                            "fields":{"sensor":["id","name","noumenon_type","noumenon_id","sensor_type"],"site":["name","db_name"]},
                            "where":{"sensor":{"combine":[{"id":[1,12,13],"sensor_type":[1]}],"noumenon_id":"condition_2"}},
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
                            "symbols":{"sensor":{"combine":[{"id":["equal","equal","equal"],"sensor_type":["equal"]}],"noumenon_id":"notin"}},
                            "orderby":""
                        },
                    "condition_2":
                        {
                            "fields":{"department":["department_id"]},
                            "where":"",
                            "join":"",
                            "jointype":"",
                            "limit":"",
                            "tables": ["department"],
                            "symbols":"",
                            "orderby":""
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
                }
            ]
        },
        "API_message_parameters":{"QueryTableData":"JSON","DB":"string"},
        "API_example":{
            "APIS": "POST /api/APIDOC/1.0/my/CommonUse/SqlSyntax/JoinMultiTable_",
            "OperationTime": "0.298",
            "BytesTransferred": 353,
            "DB": "MSSQL",
            "System": "APIDOC",
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
    dicRet = appPaaS.preProcessRequest(request,system="YS")
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
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        sqlsyntax_actions_status,sqlsyntax_actions_result = join_sqlsyntax_params_actions(action_result,"condition_1",reqdataDict,sess,metadata,"mysql",True,"APIDOC")
        if not sqlsyntax_actions_status:
            dicRet["Response"] = sqlsyntax_actions_result
            return jsonify( **dicRet)

        if request.args.get("getSqlSyntax") == "yes":
            dicRet['SqlSyntax'] = str(sqlsyntax_actions_result[1].compile(compile_kwargs={"literal_binds": True}))

        dicRet['QueryTableData'] = sqlsyntax_actions_result[0]
        err_msg = "ok" #done successfully

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
# API to CommonUse register
# Date: 08292019@Yishan
# FOR MYSQL
#=======================================================
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/<tableName>', methods = ['POST'])
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/<tableName>', methods = ['POST'])
def commonuse_register(tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供註冊mysql通用Table的單筆或多筆資料服務(user/department/sensor，此三個表不適用)",
        "API_postData":{"postData":"各表應輸入的所有資料欄位","Data格式範例":"key:['value',.....]","注意事項":"postData內不可含有' : '，系統會自動替代成' - '"},
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","insertstatus":"string+各筆資料新增狀態，若全部新增成功則無此Response"},
        "API_example":{
            "APIS": "POST /api/APIDOC/1.0/my/CommonUse/APIDOCgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system="YS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "user" or tableName == "department" or tableName == "sensor":
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)

    #多筆資料新增的狀態
    insertstatus = [] 
    insertstatusmsg = ""

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,"APIDOC",havetime=False)
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

        registertargetTable = Table(tableName , metadata, autoload=True)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        for i in range(len(keyList)): 
            #有任何主鍵沒post到，return error
            if reqdataDict.get(keyList[i]) is None:
                dicRet["Response"] = "primary key is necessary"
                return jsonify( **dicRet)

            #把unicode list 轉成 str list，才能抓到list內的各內容
            postDataKEYtostrList = map(str,reqdataDict.get(keyList[i]))
            postDataCount = len(postDataKEYtostrList)
            for j in range(len(postDataKEYtostrList)):
                #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                query_field = getattr(registertargetTable.c, keyList[i])
                postKeyList.append('({} = "{}")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))
        #每一筆新增資料的where條件陣列
        whereDict = [] 
        for i in range(postDataCount):
            #以間隔方式一一抓取
            whereDict.append(postKeyList[i::postDataCount])

        #每一筆新增資料的where條件str
        for i in range(len(whereDict)):
            check_data_existed = False
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
                        dicRet["Response"] = "{} missing post some fields".format(tableName)
                        return jsonify( **dicRet)

                    if reqdataDict.get(fieldList[x]) == "":
                        dicRet["Response"] = "data '{}' can't Null".format(fieldList[x])
                        return jsonify( **dicRet)

                    if tableName == "DTCOnline" and (fieldList[x] == "selfInsp" or fieldList[x] == "dtctime" or fieldList[x] == "wireID"):
                        #此欄位為時間字串不做過濾
                        postDatatostrList = reqdataDict.get(fieldList[x])
                    else:
                        postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                    #postDatatostrList = map(str,reqdataDict.get(fieldList[x]))
                    if len(postDatatostrList) == postDataCount:
                        if postDatatostrList[thisNum] is None:
                            dicRet["Response"] = "{} data can't be None".format(fieldList[x])
                            return jsonify( **dicRet)

                        if not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int)):
                            #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
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

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

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
# API to CommonUse update
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/<tableName>', methods = ['PATCH'])
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/<tableName>', methods = ['PATCH'])
def commonuse_update(tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供更新mysql通用Table的資料服務(user/department/sensor，此三個表不適用)",
        "API_postData":{"postData":"需更新的個欄位內容","Data格式範例":"key:['value',.....](需為陣列)","舊的主鍵格式(necessary)":"old_'主鍵ID'","新的主鍵格式":"主鍵ID","注意事項":"postData內不可含有' : '，系統會自動替代成' - '"},
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","updatestatus":"string+各筆資料更新狀態，若全部更新成功則無此Response"},
        "API_example":{
            "APIS": "PATCH /api/APIDOC/1.0/my/CommonUse/APIDOCgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL",
            "Table":"APIDOCgroup"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system="YS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "user" or tableName == "department" or tableName == "sensor":
        dicRet["Response"] = "Try another api for update {}".format(tableName)
        return jsonify( **dicRet)

    #多筆資料更新的狀態
    updatestatus = [] 
    updatestatusmsg = ""

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,"APIDOC",havetime=False)
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

        updatetargetTable = Table(tableName , metadata, autoload=True)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        for i in range(len(keyList)):
            if reqdataDict.get("old_"+ keyList[i]) is None:
                dicRet["Response"] = "primary key is necessary and format of the primary key must be 'old_xxx'"
                return jsonify( **dicRet)

            if not isinstance(reqdataDict.get("old_"+ keyList[i]),list):
                dicRet["Response"] = "Error type of '{}',it must be a Array".format(reqdataDict.get("old_"+ keyList[i]))
                return jsonify( **dicRet)

            #把unicode list 轉成 str list，才能抓到list內的各內容
            postDataKEYtostrList = map(str,reqdataDict.get("old_"+ keyList[i]))
            postDataCount = len(postDataKEYtostrList)
            for j in range(len(postDataKEYtostrList)):
                #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                query_field = getattr(updatetargetTable.c,keyList[i])
                postKeyList.append('({} = \"{}\")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))
                    
        #每一筆更新資料的where條件陣列
        whereDict = [] 
        for i in range(postDataCount):
            #以間隔方式一一抓取
            whereDict.append(postKeyList[i::postDataCount])

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
                        if not isinstance(reqdataDict.get(fieldList[x]),list):
                            dicRet["Response"] = "Error type of '{}',it must be a Array".format(reqdataDict.get(fieldList[x]))
                            return jsonify( **dicRet)

                        #postDatatostrList = map(str,reqdataDict.get(fieldList[x]))
                        if tableName == "DTCOnline" and (fieldList[x] == "selfInsp" or fieldList[x] == "dtctime" or fieldList[x] == "wireID"):
                            #此欄位為時間字串不做過濾
                            postDatatostrList = reqdataDict.get(fieldList[x])
                        else:
                            postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                        if len(postDatatostrList) == postDataCount:
                            for y in range(len(postDatatostrList)):
                                if not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int)):
                                    #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                                    postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                                else:
                                    postDataList[fieldList[x]] = postDatatostrList[thisNum]
                        else:
                            dicRet["Response"] = "The number of input data does not match"
                            return jsonify( **dicRet)

                sess.execute(updatetargetTable.update().where(text(whereStr)).values(postDataList))
                sess.commit()
            else:
                updatestatus.append(whereStr)
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if len(updatestatus) != 0:
        updatestatusmsg = "Error: {} ID ({}) isn't existed".format(tableName," , ".join(updatestatus))
        dicRet["updatestatus"] = updatestatusmsg

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
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/<tableName>', methods = ['DELETE'])
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/<tableName>', methods = ['DELETE'])
def commonuse_delete(tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除mysql通用Table的指定資料服務(department/sensor，此兩個表不適用)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{"postData":"各表要刪除的主鍵欄位(條件式-主鍵輸入)"},
        "API_path_parameters":{"tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","deletestatus":"string+各筆資料刪除狀態，若全部刪除成功則無此Response"},
        "API_example":{
            "APIS": "DELETE /api/APIDOC/1.0/my/CommonUse/APIDOCgroup",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system="YS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    if tableName == "department" or tableName == "sensor":
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)
    
    #多筆資料刪除的狀態
    deletestatus = [] 
    deletestatusmsg = ""

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        #desc table schema
        desc_table_return = desc_table(metadata,tableName,"APIDOC",havetime=False)
        desc_table_status = desc_table_return[0]
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

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        #檢查是否主鍵Data數量相同
        setPKdatanum = ""
        for i in range(len(keyList)):
            if reqdataDict.get(keyList[i]) is not None:
                #把unicode list 轉成 str list，才能抓到list內的各內容
                postDataKEYtostrList = map(str,reqdataDict.get(keyList[i]))
                postDataCount = len(postDataKEYtostrList)
                #第一次for loop PRI，確定輸入的主鍵資料數量是相同的
                if isinstance(setPKdatanum,str):
                    setPKdatanum = postDataCount
                else:
                    if setPKdatanum != postDataCount:
                        dicRet["Response"] = "The number of input data does not match"
                        return jsonify( **dicRet)
                    
                for j in range(len(postDataKEYtostrList)):
                    #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                    query_field = getattr(deletetargetTable.c,keyList[i])
                    postKeyList.append('({} = \"{}\")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))

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
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if len(deletestatus) != 0:
        #以,來join陣列
        deletestatusmsg = "Error: {} ID ({}) isn't existed".format(tableName," , ".join(deletestatus))
        dicRet["deletestatus"] = deletestatusmsg

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
# {{{ COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/Schema/<tableName>', methods = ['GET'])
@COMMONUSE_APIDOC_API.route('/api/APIDOC/1.0/my/CommonUse/Schema/<tableName>', methods = ['GET'])
def commonuse_get_tableschema(tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢mysql通用Table的欄位屬性",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"tableName":"資料表名稱"},
        "API_message_parameters":{"DB":"string","Table":"string","schemaDict":"JSON"},
        "API_example":{
            "APIS": "POST /api/APIDOC/1.0/my/CommonUse/Schema/user",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "DB":"MYSQL",
            "Table":"user",
            "schemaDict": {
                "sensorName": "VARCHAR(128)",
                "updated_at": "TIMESTAMP",
                "senAttr": "JSON",
                "noumenonType": "VARCHAR(128)",
                "senInfo": "VARCHAR(256)",
                "dbName": "VARCHAR(60)",
                "noumenonID": "VARCHAR(128)",
                "creatorID": "VARCHAR(24)",
                "senID": "VARCHAR(128)",
                "senRawTable": "VARCHAR(128)",
                "created_at": "TIMESTAMP"
            }
        }
    }
    '''
    #}}}
    dicRet = {}
    dicRet = appPaaS.preProcessRequest(request,system="YS")

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)

    try:
        DbSession,metadata,engine= appPaaS.getDbSessionType(system="YS")
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)

        #check table existed or not
        if not retrieve_table_exist(metadata,tableName,"APIDOC"):
            dicRet["Response"] = "Table '{}' doesn't exist".format(tableName)
            return jsonify( **dicRet)

        desc_table_return = desc_table(metadata,tableName,"APIDOC")
        desc_table_status = desc_table_return[0]
        schemaDict = desc_table_return[3]

        if desc_table_status != 'ok':
            dicRet["Response"] = desc_table_status
            return jsonify( **dicRet)

        dicRet['schemaDict'] = schemaDict
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),"APIDOC")
        
    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()

    dicRet["Table"] = tableName 
    dicRet["Response"] = err_msg 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}