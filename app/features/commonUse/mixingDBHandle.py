# -*- coding: utf-8 -*-
#CommonUse module description
"""
==============================================================================
created    : 03/26/2021
Last update: 03/31/2021
Developer: Yi-Shan Tsai 
Lite Version 2 @Yishan08212019
API Version 1.0

Filename: mixingDBHandle.py

Description: 多種資料庫整合在一起使用

Total = 1 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
# {{{
from sqlalchemy import *
# }}}

#=======================================================
# User-defined modules
#=======================================================
# {{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
from app.features.specificTable.sensorHandle import get_redis_sensor_IDKEY_ornot_create, _desc_table
from .inMemoryDBHandle import operate_CU_integration
from app.features.customizedHandle import trigger_specific_program
# }}}

#blueprint
MIXINGDB_API = Blueprint('MIXINGDB_API', __name__)

#=======================================================
# Definition: 提供一次在多種資料庫進行CUD動作之整合性api
# Date: 03262021@Yishan
#=======================================================
# {{{ MIXINGDB_API.route('/api/<SYSTEM>/1.0/mix/CommonUse/Operations', methods = ['POST'])
@MIXINGDB_API.route('/api/<SYSTEM>/1.0/mix/CommonUse/Operations', methods = ['POST'])
@decorator_check_legal_system()
def mixingDB_commonuse_register_update_delete(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供順序性一次在多種資料庫進行CUD動作之整合性api(mysql:department/site/place/device/sensor，mysql此五個表不適用)",
        "API_postData":{
            "bodytype":"Array",
            "bodyschema":"[{},...]",
            "parameters":{
                "database":{"type":"String","requirement":"required","directions":"欲使用的資料庫，value有「mysql|mssql|postgres|redis」","example":"{'database':'mysql'}"},
                "operations":{"type":"Array","requirement":"required","directions":"資料操作選項，value有「post(新增)|patch(部分更新)|put(全部更新，只有redis有此操作功能)|delete(刪除)」","example":"{'operations':['post','patch'...]}"},
                "tables":{"type":"Array","requirement":"required","directions":"欲使用的資料表(若使用的資料庫為redis，此參數可以不用)","example":"{'tables':['tablename1','tablename2'...]}"},
                "datas":{
                    "type":"Array",
                    "requirement":"required",
                    "directions":[
                        "進行操作的資料內容。參數database若為postgres時，參數datas陣列內的值須為陣列；若為其他種類資料庫時，參數datas陣列內的值則須為物件。詳細內容格式請看'Show Details'",
                        {
                            "資料表所有欄位":{"type":"Array","requirement":"optional","directions":"資料表所有欄位值"}
                        }
                    ],
                    "example":"{'datas':[{'id':[3687,3688],'email':['test','test'],'name':['test','test'],'access_list':[null,null],'creator':[0,0],'modifier':[0,0]},...]}"
                },
                "trigger_php":{"type":"Array","requirement":"optional","directions":"若使用的資料庫為postgres，需設定此次操作是否要觸發特定php程式，value為「yes|no」","example":"{'trigger_php':['yes','no']}"}
            },
            "precautions":{
                "注意事項1":"最外層的陣列內容順序代表欲資料操作的排序，每一筆值(需為物件)都是一次的資料操作",
                "注意事項2":"每一筆操作的內容參數operations、tables、datas需為陣列且長度必須相同，代表一次多筆資料處理",
                "注意事項3":"目前database:postgres只支援post操作，其他操作不接受",
                "注意事項4":"data內不可含有' : '，系統會自動替代成' - '",
                "注意事項5":"若要新增JSON欄位值，需以JSON字串方式傳入且key必須以雙引號包起來",
                "注意事項6":"固定時間欄位無需post",
                "注意事項7":"若該欄位可允許為null，value放null即可",
                "注意事項8":"若該欄位有預設default值則無需post此欄位"
            },
            "example":[
                [
                    {
                        "database":"postgres",
                        "operations":["post","post"],
                        "tables":["f11","f10"],
                        "datas":[
                            [
                                {
                                    "machine_detail":"test"
                                },
                                {
                                    "machine_detail":"test2"
                                }
                            ],
                            [
                                {
                                    "machine_detail":"test"
                                }
                            ]
                        ],
                        "trigger_php":["no","no"]
                    },
                    {
                        "database":"mysql",
                        "operations":["post"],
                        "tables":["bond_login"],
                        "datas":[
                            {
                                "user":["test"],
                                "dtc":["test"],
                                "device":["test"]
                            }
                        ]
                    }
                ],
                [
                    {
                        "database":"mysql",
                        "operations":["post","patch"],
                        "tables":["bond_login","bond_login"],
                        "datas":[
                            {
                                "user":["test2"],
                                "dtc":["test2"],
                                "device":["test2"]
                            },
                            {
                                "user":["test1"],
                                "old_dtc":["test"],
                                "device":["test1"]
                            }
                        ]
                    },
                    {
                        "database": "redis",
                        "operations": [
                            "put",
                            "post"
                        ],
                        "datas": [
                            {
                                "hash": {
                                    "data": {
                                        "test_hash1": {
                                            "data1": "ccc"
                                        }
                                    }
                                }
                            },
                            {
                                "string": {
                                    "data": {
                                        "test_string1": 5
                                    }
                                }
                            }
                        ]
                    }
                ]
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_message_parameters":{"operationstatus":"各筆資料操作結果"},
        "API_example":{
            "APIS": "POST /api/IOT/1.0/mix/CommonUse/Operations",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76
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

    database_config = {
        "mysql":{
            "post":commonuse_register_integration_myms,
            "patch":commonuse_update_integration_myms,
            "put":commonuse_update_integration_myms,
            "delete":commonuse_delete_integration_myms
        },
        "mssql":{
            "post":commonuse_register_integration_myms,
            "patch":commonuse_update_integration_myms,
            "put":commonuse_update_integration_myms,
            "delete":commonuse_delete_integration_myms
        },
        "postgres":{
            "post":None
        },
        "redis":{
            "post":"Insert",
            "patch":"Patch",
            "put":"Put",
            "delete":operate_CU_integration
        }
    }

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)
    
    Stauts = []

    try:
        for element in reqdataDict:
            # print "~~~element~~~"
            # print element
            element_status = []
            if not check_post_parameter_exist(element,["database","operations","datas"]):
                Stauts.append("Data : '{}' missing post parameters : '{}'".format(element, ["database","operations","datas"]))
                continue
            
            if element["database"] not in database_config.keys():
                Stauts.append("Data : '{}' parameter-database must be one of the following ['mysql','mssql','postgres','redis']".format(element))
                continue
            
            if element["database"] == "postgres":
                post_parameter = ["database","operations","tables","datas","trigger_php"]
                endnum = 5
                if element.get("trigger_php") is None:
                    Stauts.append("Data : '{}' missing post parameters : 'trigger_php'".format(element))
                    continue
            elif element["database"] == "redis":
                endnum = 3
                post_parameter = ["database","operations","datas"]
            else:
                endnum = 4
                post_parameter = ["database","operations","tables","datas"]

            listlength = None
            setbreak = False
            for i in range(1,endnum):
                #判斷["operations",("tables"),"datas",("trigger_php")]這幾個參數必須為陣列
                if not isinstance(element[post_parameter[i]],list):
                    Stauts.append("Data : '{}' parameter-{} must be an Array".format(element, post_parameter[i]))
                    setbreak = True
                    break
                
                #判斷["operations",("tables"),"datas",("trigger_php")]這幾個參數的長度必須相同
                if not listlength:
                    listlength = len(element[post_parameter[i]])
                elif len(element[post_parameter[i]]) != listlength:
                    Stauts.append("Data : '{}' parameter-{} 參數陣列大小必須相同".format(element, ",".join(post_parameter)))
                    setbreak = True
                    break

            if setbreak: continue

            setbreak = False
            dbName = [""]
            checktableoperationnotreapt = {}
            pg_dbname_list = []
            pg_table_dbname = {}
            for i in range(len(element["operations"])):
                if element["database"] != "redis":
                    if checktableoperationnotreapt.get(element["tables"][i]) is None:
                        checktableoperationnotreapt[element["tables"][i]] = [element["operations"][i]]
                    else:
                        if element["operations"][i] in checktableoperationnotreapt[element["tables"][i]]:
                            Stauts.append("Data : '{}' parameter-tables參數，其值不能重複".format(element))
                            setbreak = True
                            break

                if element["database"] == "postgres":
                    operationslist = ["post"]
                    if not isinstance(element["datas"][i],list):
                        Stauts.append("Data : '{}' ，Error -> when parameter-database is postgres , sparameter-datas value : '{}' must be an Array".format(element, element["datas"][i]))
                        setbreak = True
                        break

                    status,result = get_redis_sensor_IDKEY_ornot_create(SYSTEM,element["tables"][i])
                    if not status:
                        Stauts.append("Data : '{}' ，Error -> {}".format(result))
                        setbreak = True
                        break

                    pg_dbname_list.append(result)
                    if pg_table_dbname.get(result) is None:
                        pg_table_dbname[result] = [element["tables"][i]]
                    else:
                        pg_table_dbname[result].append(element["tables"][i])

                else:
                    operationslist = ["post","patch","put","delete"]
                    if not isinstance(element["datas"][i],dict):
                        Stauts.append("Data : '{}' ，Error -> when parameter-database is mysql、mssql、redis , sparameter-datas value : '{}' must be an Object".format(element, element["datas"][i]))
                        setbreak = True
                        break
                        
                    if element["database"] == "mysql":
                        if element["tables"][i] in ("department","site","place","device","sensor"):
                            Stauts.append("Data : '{}' ，Error -> parameter-tables 不能使用此api".format(element))
                            setbreak = True
                            break
                    
                    elif element["database"] == "redis":
                        dbName = [globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)]
                        if element["operations"][i] == "delete":
                            if not check_post_parameter_exist(element["datas"][i],["keys"]):
                                Stauts.append("Data : '{}' ，Error -> parameter-datas missing post parameters : '{}'".format(element,"keys"))
                                setbreak = True
                                break
                            
                            if not isinstance(element["datas"][i].get("keys"),list):
                                Stauts.append("Data : '{}' ，Error -> parameter-datas Error type of '{}',it must be an Array".format(element,element["datas"][i].get("keys")))
                                setbreak = True
                                break

                if element["operations"][i] not in operationslist:
                    Stauts.append("Data : '{}' ，Error -> parameter-operations 存在不支援的操作選項 : '{}'".format(element,element["operations"][i]))
                    setbreak = True
                    break
            else:
                if element["database"] == "postgres":
                    dbName = list(set(pg_dbname_list))
            
            if setbreak: continue

            # print "~~~dbName~~~"
            # print dbName
            
            for db in dbName:
                try:
                    DbSession,metadata,engine= appPaaS.getDbSessionType(dbName=db, forRawData=element["database"], system=SYSTEM)
                    if DbSession is None:
                        #表示連接資料庫有問題
                        element_status.append("Data : '{}' ，Error -> {}".format(element,engine))
                        continue
                    
                    if element["database"] != "redis":
                        sess = DbSession()

                    #只有database為postgres有可能有多個dbName的可能，所以需抓該db為哪一個table
                    if element["database"] == "postgres":
                        trigger_php = False
                        for table in pg_table_dbname[db]:
                            index = element["tables"].index(table)

                            if re.search(r'[Y|y][E|e][S|s]',element["trigger_php"][index]): trigger_php = True

                            SensorTable = Table(table, metadata,  autoload=True)

                            desc_table_status,_,schemaDict,prikeyisTime = _desc_table(SYSTEM,metadata,table)
                            if desc_table_status != 'ok':
                                element_status.append("Data : '{}' ，Error -> {}".format(element,desc_table_status))
                                continue

                            if not prikeyisTime:
                                sqlInsert = SensorTable.insert().values(element["datas"][index])
                                sess.execute(sqlInsert)
                                sess.commit()
                            else:
                                for i in element["datas"][index]:
                                    sqlInsert = SensorTable.insert().values(i)
                                    sess.execute(sqlInsert)
                                    sess.commit()

                            element_status.append("ok")
                        
                            if trigger_php:
                                programDir = SYSTEM
                                #確定PaaS是否為container
                                if globalvar.ISCONTAINER: programDir = globalvar.CONTAINER_API_HTML
                                trigger_settime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[::]
                                trigger_obj = {"table":table,"data":element["datas"][index],"upload_at":trigger_settime,"ip":request.host.split(":")[0]}
                                trigger_specific_program(SYSTEM, selfUse=True, useThread=True, languages="php", programName="/{}/mes_modules/mes_modules.php".format(programDir), programData=json.dumps(ConvertData().convert(trigger_obj)), postHttp=True)

                    else:
                        for i in range(len(element["operations"])):
                            if element["database"] == "redis":
                                if element["operations"][i] != "delete":
                                    _, status = operate_CU_integration(element["datas"][i], DbSession, database_config[element["database"]][element["operations"][i]])
                                    for key,value in status.items():
                                        if not value: del status[key]
                                    if not status:
                                        element_status.append("ok")
                                    else:
                                        element_status.append(status)
                                else:
                                    DbSession.delete(*element["datas"][i].get("keys"))
                                    element_status.append("ok")
                            else:
                                result = database_config[element["database"]][element["operations"][i]](element["datas"][i], sess, metadata, element["tables"][i], SYSTEM, element["database"])
                                if result.get("insertstatus") is not None:
                                    element_status.append(result["insertstatus"])
                                else:
                                    element_status.append(result["err_msg"])

                except Exception as e:
                    element_status.append(appPaaS.catch_exception(e,sys.exc_info(),SYSTEM))
                finally:
                    # print "@@@@@@@@@@@@@@@@@@@@@@@@"
                    # print element["database"],db
                    if 'DbSession' in locals().keys() and DbSession is not None and element["database"] != "redis":
                        sess.close()
                        DbSession.remove()
                        engine.dispose()
            
            if element_status:
                Stauts.append(element_status)

        else:
            err_msg = "ok"
            if Stauts:
                dicRet["Stauts"] = Stauts

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
    finally:
        if Stauts:
            dicRet["Stauts"] = Stauts

    dicRet["Response"] = err_msg

    return jsonify( **dicRet)
# }}}