# -*- coding: utf-8 -*-
#RelatedPG module description
"""
==============================================================================
created    : 
Last update: 03/31/2021
Developer: Yi-Shan Tsai 
Lite Version 2 @Yishan05282020
API Version 1.0

Filename: relatedpgHandle.py

Description: 有關聯postgresql -> 這四個表：department/site/place/device的通用api

Total = 3 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
# {{{
from sqlalchemy import *
import subprocess #Yishan 05212020 subprocess 取代 os.popen
from copy import deepcopy
# }}}

#=======================================================
# User-defined modules
#=======================================================
# {{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
from .sensorHandle import retrieve_table
# }}}

ACCESS_SYSTEM_LIST = ["IOT"]

#blueprint
RELATEDPG_API = Blueprint('RELATEDPG_API', __name__)

#=======================================================
# Definition1: 檢查this noumenon_type & noumenon_id 存在
# Definition2: 確定此筆新增的資料是否建立資料庫，建立資料庫
# Date: 05292020@Yishan
#=======================================================
#{{{def _check_idtype_createDB_ornot(reqdataDict,thisNum,tableName,metadata,sess)
def _check_idtype_createDB_ornot(reqdataDict, thisNum, tableName, metadata, sess, iscreatefunc=True):
    noumenontypeList = map(str,reqdataDict.get("noumenon_type"))
    noumenonidList = map(str,reqdataDict.get("noumenon_id"))
    if noumenonidList[thisNum] == "null":
        if tableName == "place" or tableName == "device":
            return False,"'noumenon_id' data : '{}' can't be null".format(noumenonidList[thisNum])

        thisdbname = None
    else:
        thisid_existed,thisdbname = retrieve_noumenon_dbname(metadata, sess, noumenontypeList[thisNum], noumenonidList[thisNum])
        if not thisid_existed:
            return  False,"this : 'noumenon_type' : '{}' & 'noumenon_id' : '{}' doesn't existed".format(noumenontypeList[thisNum],noumenonidList[thisNum])

    if iscreatefunc:
        createDBList = map(str,reqdataDict.get("createDB"))
        dbnameList = map(str,reqdataDict.get("db_name"))
        if createDBList[thisNum] == "yes":
            if dbnameList[thisNum] == "" or dbnameList[thisNum] == "null":
                return False,"error 'db_name' input data : '{}' can't Null".format(dbnameList[thisNum])

            if retrieve_database_exist(system, dbName=dbnameList[thisNum], forRawData="postgres")[0]:
                return False,"this 'db_name' : '{}' existed".format(dbnameList[thisNum])

            result,msg = create_database(system,dbnameList[thisNum])
            if not result:
                return False,msg

            thisdbname = dbnameList[thisNum]
        elif createDBList[thisNum] == "no":
            thisdbname = None
        else:
            return False,"error 'createDB' input data : '{}' must be yes or no".format(createDBList[thisNum])

    return True,thisdbname
#}}}

#=======================================================
# Definition: 轉移資料表程序(先備份後刪除再轉移至新的資料庫)
# Date: 06032020@Yishan
#=======================================================
#{{{def _transfer_table(SYSTEM,dbname,noumenon_sensorList,new_dbname)
def _transfer_table(SYSTEM,dbname,noumenon_sensorList,new_dbname):
    success = True #成功狀態
    for i in noumenon_sensorList:
        #check table existed or not
        table_existed,msg = retrieve_table(i)
        if not table_existed:
            success = False

    if success:
        try:
            #1.備份資料表
            pg_dump_tablestr = " ".join(['--table='+i for i in noumenon_sensorList])
            pgdump_cmd = '/usr/bin/pg_dump -U postgres {} {} > {}'.format(pg_dump_tablestr,dbname,'/var/www/spdpaas/doc/'+dbname+'.sql')
            subprocess.check_output(pgdump_cmd,shell=True,stderr= subprocess.STDOUT)
            #2.備份成功，刪除此資料表
            msg = delete_tables(noumenon_sensorList,dbname,SYSTEM)
            if msg == "ok":
                try:
                    #3.刪除成功，匯入sql備份至新的隸屬資料庫
                    sql_cmd = '/usr/bin/psql -U postgres {} -f {}'.format(new_dbname,'/var/www/spdpaas/doc/'+ dbname+'.sql')
                    subprocess.check_output(sql_cmd,shell=True,stderr= subprocess.STDOUT)
                    try:
                        #4.匯入成功，刪除sql備份檔
                        sql_cmd = '/bin/rm {}'.format('/var/www/spdpaas/doc/'+ dbname+'.sql')
                        subprocess.check_output(sql_cmd,shell=True,stderr= subprocess.STDOUT)
                    except subprocess.CalledProcessError as e:
                        success = False
                        msg = "<transfer_table_del_sqlfile>Unexpected error: file -> '{}' 刪除備份檔失敗".format(dbname+'.sql')
                        appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)
                except subprocess.CalledProcessError as e:
                    success = False
                    msg = "<transfer_table_backup_restore>Unexpected error: database : '{}' table-> '{}' 還原失敗".format(new_dbname,noumenon_sensorList)
                    appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)
            else:
                success = False
        except subprocess.CalledProcessError as e:
            success = False
            msg = "<transfer_table_backup>Unexpected error: database : '{}' table-> '{}' 備份失敗".format(dbname,noumenon_sensorList)
            appPaaS.catch_exception(e.output,sys.exc_info(),SYSTEM)

    return success,msg
#}}}

#=======================================================
# Definition: 抓取隸屬於該編號的所有id(dep/site/pla/dev)
# Date: 06032020@Yishan
#=======================================================
# {{{ def _retrieve_noumenon_list(metadata,sess)
def _retrieve_noumenon_list(metadata,sess,tablename,thisid,noumenonList,deepnoumenonList,noumenonDict,deep=False,flag=False):
    retrieve_table_list = ["sensor","department","site","place","device"]
    tableDict = {
        "department":"dep",
        "site":"site",
        "place":"pla",
        "device":"dev"
    }
    for i in retrieve_table_list:
        thistable = Table(i , metadata, autoload=True)
        if i == "sensor":
            for row in sess.query(thistable).filter(getattr(thistable.c, "noumenonType") == tableDict[tablename],\
                                                getattr(thistable.c, "noumenonID") == thisid).all():
                drow = AdjustDataFormat().format(row._asdict())
                #flag為false時表示下階尚未有獨立資料庫，所以此sensor id隸屬於父親
                if not flag:
                    noumenonList.append(drow["senID"])
                if deep:
                    deepnoumenonList.append(drow["senID"])
        else:
            for row in sess.query(thistable).filter(getattr(thistable.c, "noumenon_type") == tableDict[tablename],\
                                                getattr(thistable.c, "noumenon_id") == thisid).all():
                drow = AdjustDataFormat().format(row._asdict())
                noumenonDict[tableDict[i]].append(drow["id"])
                #當flag為false時表示下階尚未有獨立資料庫，才需判斷此次的db_name是否為None
                if not flag:
                    #drow["db_name"] is None => 下階尚未有獨立資料庫 flag = False
                    flag = False if drow["db_name"] is None else True

                #當抓到的db_name為None才有必要繼續往下找
                if deep or drow["db_name"] is None:
                    _retrieve_noumenon_list(metadata,sess,i,drow["id"],noumenonList,deepnoumenonList,noumenonDict,deep,flag)

    return noumenonList,deepnoumenonList,noumenonDict
# }}}

#=======================================================
# Definition:
# 1. To check if dbName is existed
# 2. delete a data table within dbName
#=======================================================
# {{{ def _delete_mysql_data
def _delete_mysql_data(SYSTEM, idfield, sess, metadata, sensorList, noumenonDict):
    err_msg = "error"
    
    final_noumenonDict = {
        "department":noumenonDict["dep"],
        "site":noumenonDict["site"],
        "place":noumenonDict["pla"],
        "device":noumenonDict["dev"],
        "sensor":sensorList
    }
    try:
        for key,value in final_noumenonDict.items():
            deletetargetTable = Table(key , metadata, autoload=True)
            if key != "sensor":
                query_field = getattr(deletetargetTable.c, idfield)
            else:
                query_field = getattr(deletetargetTable.c, "senID")

            if value:
                sess.execute(deletetargetTable.delete().where(query_field.in_(value)))
                sess.commit()
            err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        return err_msg
# }}}

#=======================================================
# API to RelatedPG register
# Date: 08292019@Yishan
# FOR MYSQL
#=======================================================
# {{{ RELATEDPG_API.route('/api/<SYSTEM>/1.0/my/RelatedPG/<tableName>', methods = ['POST'])
@RELATEDPG_API.route('/api/<SYSTEM>/1.0/my/RelatedPG/<tableName>', methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def relatedpg_register(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供註冊mysql特定Table的單筆或多筆資料服務(此四個表：department/site/place/device)",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "id":{"type":"Array","requirement":"required","directions":"編號","example":[1]},
                "name":{"type":"Array","requirement":"required","directions":"名稱","example":["test"]},
                "db_name":{"type":"Array","requirement":"required","directions":"資料庫名稱","example":["test"]},
                "noumenon_type":{"type":"Array","requirement":"required","directions":"隸屬類別(dep/site/pla/dev)","example":["site"]},
                "noumenon_id":{"type":"Array","requirement":"required","directions":"隸屬編號","example":[1]},
                "note":{"type":"Array","requirement":"required","directions":"備註說明","example":["test"]},
                "creator":{"type":"Array","requirement":"required","directions":"建立者","example":[2]},
                "modifier":{"type":"Array","requirement":"required","directions":"修改者","example":[2]},
                "createDB":{"type":"Array","requirement":"required","directions":"是否在postgresql建立資料庫(yes/no)","example":["yes"]}
            },
            "precautions": {
                "注意事項":"若要新增空值放入'null'即可"
            },
            "example":[
                {
                    "id":[1,2,3,4],
                    "name":["","","",""],
                    "db_name":["aa","dd","ff","dd"],
                    "noumenon_type":["pla","dep","dep","null"],
                    "noumenon_id":[2,2,4,"null"],
                    "note":["","","",""],
                    "creator":[1,1,2,2],
                    "modifier":[1,1,2,2],
                    "createDB":["no","no","no","yes"]
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","insertsuccess":"array+新增成功的id列表，若全部新增失敗則無此Response","insertstatus":"array+各筆資料新增狀態，若全部新增成功則無此Response"},
        "API_example":{
            "APIS": "POST /api/IOT/1.0/my/RelatedPG/site",
            "OperationTime": "0.138",
            "BytesTransferred": 164,
            "DB": "MYSQL",
            "System": "IOT",
            "insertsuccess": [
                "id: '1' register successful"
            ],
            "Table": "site",
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

    if not (tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device"):
        dicRet["Response"] = "Try another api for register {}".format(tableName)
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    post_parameter = ["id","name","db_name","noumenon_type","noumenon_id","note","creator","modifier","createDB"]
    post_parametertype = [int,str,str,str,int,str,int,int,str]
    datatype = {str:"varchar",int:"Integer"}
    noumenon_relation = {"place":"site","device":"pla"}
    
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    #多筆資料新增的狀態
    insertstatus = [] 
    # insertstatusmsg = ""
    #新增成功的資料
    insertsuccess = []
    #是否有建立資料庫
    createdbTrue = False
    #各表主鍵id field
    thistableidfield = "{}_id".format(tableName)

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

        fieldList = post_parameter

        registertargetTable = Table(tableName , metadata, autoload=True)

        if not isinstance(reqdataDict.get("id"),list):
            dicRet["Response"] = "Error type of 'id',it must be an Array"
            return jsonify( **dicRet)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        #把unicode list 轉成 str list，才能抓到list內的各內容
        postDataKEYList = reqdataDict.get("id")
        postDataCount = len(postDataKEYList)
        for j in range(len(postDataKEYList)):
            if not isinstance(postDataKEYList[j],int):
                dicRet["Response"] = "Error type of 'id' data : '{}' ,it must be an Integer".format(postDataKEYList[j])
                return jsonify( **dicRet)

            #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
            query_field = getattr(registertargetTable.c, thistableidfield)
            postKeyList.append('({} = {})'.format(query_field,postDataKEYList[j]))
        
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
                thisinsert_fail = False
                for x in range(len(fieldList)):
                    if not isinstance(reqdataDict.get(fieldList[x]),list):
                        dicRet["Response"] = "Error type of '{}',it must be an Array".format(fieldList[x])
                        return jsonify( **dicRet)

                    postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                    if len(postDatatostrList) != postDataCount:
                        dicRet["Response"] = "The number of input data does not match"
                        return jsonify( **dicRet)

                    if postDatatostrList[thisNum] is None:
                        dicRet["Response"] = "{} data can't be None".format(fieldList[x])
                        return jsonify( **dicRet)

                    if not isinstance(postDatatostrList[thisNum],post_parametertype[x]):
                        if postDatatostrList[thisNum] != "null":
                            dicRet["Response"] = "Error type of \'{}\',it must be a {}".format(fieldList[x],datatype[post_parametertype[x]])
                            return jsonify( **dicRet)

                    if fieldList[x] != "createDB" and fieldList[x] != "db_name":
                        if not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int)):
                            if postDatatostrList[thisNum] != "null":
                                #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                                postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                            else:
                                postDataList[fieldList[x]] = None
                                # https://stackoverflow.com/questions/32959336/how-to-insert-null-value-in-sqlalchemy
                        else:
                            if fieldList[x] == "id":
                                postDataList[thistableidfield] = postDatatostrList[thisNum]
                            else:
                                postDataList[fieldList[x]] = postDatatostrList[thisNum]

                # #當tableName為place&device時需判斷noumenon_type是否正確(place->site,device->pla)
                # if (noumenon_relation.get(tableName) is not None) and (noumenon_relation[tableName] != postDataList["noumenon_type"]):
                #     insertstatus.append("Error: {}".format("relationship : Place的noumenon_type必須是site，Device的noumenon_type必須是pla -> this noumenon_type : '{}'".format(postDataList["noumenon_type"])))
                #     thisinsert_fail = True

                if not thisinsert_fail:
                    result,thisdbname = _check_idtype_createDB_ornot(reqdataDict,thisNum,tableName,metadata,sess)
                    createdbTrue = result
                    if result:
                        postDataList["db_name"] = thisdbname
                        #noumenon_type與noumenon_id不可能有其一為空
                        if postDataList["noumenon_type"] is None or postDataList["noumenon_type"] == "" or postDataList["noumenon_id"] is None:
                            postDataList["noumenon_type"] = None
                            postDataList["noumenon_id"] = None

                        #add time
                        postDataList['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        postDataList['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        sess.execute(registertargetTable.insert().values(postDataList))
                        sess.commit()
                        err_msg = "ok"
                        #新增成功資料資訊
                        insertsuccess.append("id: '{}' register successful".format(postDataList['id']))
                    else:
                        insertstatus.append("Error: {}".format(thisdbname))
            else:
                insertstatus.append("Error:  '{}' existed".format(whereStr))
    except Exception as e:
        #以防已在postgresql建立資料庫後，mysql新增資料失敗，導致兩邊不一致，所以進行刪除資料庫動作
        if createdbTrue and retrieve_database_exist(SYSTEM, dbName=thisdbname, forRawData="postgres")[0]:
            delete_database([thisdbname],SYSTEM)

        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if len(insertsuccess) != 0:
        dicRet["insertsuccess"] = insertsuccess

    if len(insertstatus) != 0:
        dicRet["insertstatus"] = insertstatus

    dicRet["Response"] = err_msg 
    dicRet["Table"] = tableName
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to RelatedPG update
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ RELATEDPG_API.route('/api/<SYSTEM>/1.0/my/RelatedPG/<tableName>', methods = ['PATCH'])
@RELATEDPG_API.route('/api/<SYSTEM>/1.0/my/RelatedPG/<tableName>', methods = ['PATCH'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def relatedpg_update(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供更新mysql特定Table的單筆或多筆資料服務(此四個表：department/site/place/device)",
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "old_id": {"type":"Array","requirement":"required","directions":"欲更新的資料主鍵欄位值","example":"[1,3,...]"},
            "資料表欄位": {"type":"Array","requirement":"optional","directions":"欲更新的資料欄位內容","example":"['value1','value2',...]"},
            "precautions": {
                "注意事項1":"提供修改以下欄位：name(名稱),note(備註說明),modifier(修改者),noumenon_type(隸屬類別),noumenon_id(隸屬編號,'dep/site/pla/dev')",
                "注意事項2":"若要修改成空值放入'null'即可",
                "注意事項3":"noumenon_type與noumenon_id必須同時更新且若其中有空值，系統會將兩欄位都放defaul NULL值"
            },
            "example":[
                {
                    "old_id":[3],
                    "noumenon_id":[4],
                    "noumenon_type":["dep"]
                }
            ]
        },
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","updatesuccess":"array+更新成功的id列表，若全部更新失敗則無此Response","updatestatus":"array+各筆資料更新狀態，若全部更新成功則無此Response"},
        "API_example":{
            "APIS": "PATCH /api/IOT/1.0/my/RelatedPG/place",
            "BytesTransferred": 174,
            "DB": "MYSQL",
            "System": "IOT",
            "OperationTime": "0.115",
            "updatesuccess": [
                "'(place.id = 2)' update successful"
            ],
            "Table": "place",
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

    if not (tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device"):
        dicRet["Response"] = "Try another api for update {}".format(tableName)
        return jsonify( **dicRet)

    post_parameter = ["name","noumenon_type","noumenon_id","note","modifier"]
    post_parametertype = [str,str,int,str,int]
    datatype = {str:"varchar",int:"Integer"}

    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    #多筆資料更新的狀態
    updatestatus = [] 
    #更新成功的資料
    updatesuccess = []
    #各表主鍵id field
    thistableidfield = "{}_id".format(tableName)

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

        fieldList = post_parameter

        updatetargetTable = Table(tableName , metadata, autoload=True)

        if reqdataDict.get("old_id") is None:
            dicRet["Response"] = "primary key is necessary and format of the primary key must be 'old_id'"
            return jsonify( **dicRet)

        if not isinstance(reqdataDict.get("old_id"),list):
            dicRet["Response"] = "Error type of 'old_id',it must be an Array"
            return jsonify( **dicRet)

        #先判斷noumenon_type與noumenon_id若有就要兩者都有
        if reqdataDict.get("noumenon_type") is not None or reqdataDict.get("noumenon_id") is not None:
            if not check_post_parameter_exist(reqdataDict,["noumenon_type","noumenon_id"]):
                dicRet["Response"] = "Missing post parameters : '{}'".format(["noumenon_type","noumenon_id"])
                return jsonify( **dicRet)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        #把unicode list 轉成 str list，才能抓到list內的各內容
        postDataKEYList = reqdataDict.get("old_id")
        postDataCount = len(postDataKEYList)
        if not postDataKEYList:
            dicRet["Response"] = "old_id : '{}' can't be Null".format(postDataKEYList)
            return jsonify( **dicRet)

        for j in range(len(postDataKEYList)):
            if not isinstance(postDataKEYList[j],int):
                dicRet["Response"] = "Error type of 'old_id' data : '{}' ,it must be a Integer".format(postDataKEYList[j])
                return jsonify( **dicRet)

            #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
            query_field = getattr(updatetargetTable.c,thistableidfield)
            postKeyList.append('({} = {})'.format(query_field,postDataKEYList[j]))
                    
        #每一筆更新資料的where條件陣列
        whereDict = [] 
        for i in range(postDataCount):
            #以間隔方式一一抓取
            whereDict.append(postKeyList[i::postDataCount])

        #每一筆更新資料的where條件str
        for i in range(len(whereDict)):
            thisid = postDataKEYList[i]
            check_data_existed = False
            #以&來join陣列
            whereStr = " & ".join(whereDict[i])
            for row in sess.execute(updatetargetTable.select(text(whereStr))):
                drow = AdjustDataFormat().format(dict(row.items()))
                this_noumenon_type = drow["noumenon_type"]
                this_noumenon_id = drow["noumenon_id"]
                this_dbname = drow["db_name"]
                check_data_existed = True
            
            #獲取目前的i
            thisNum = i
            #各筆資料的所有Data dict
            postDataList = {}
            if check_data_existed:
                thisupdate_fail = False
                for x in range(len(fieldList)):
                    #開放給使用者選擇性update參數
                    if reqdataDict.get(fieldList[x]) is not None:
                        if not isinstance(reqdataDict.get(fieldList[x]),list):
                            dicRet["Response"] = "Error type of '{}',it must be an Array".format(fieldList[x])
                            return jsonify( **dicRet)

                        postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                        if len(postDatatostrList) != postDataCount:
                            dicRet["Response"] = "The number of input data does not match"
                            return jsonify( **dicRet)
                        
                        if postDatatostrList[thisNum] is None:
                            dicRet["Response"] = "{} data can't be None".format(fieldList[x])
                            return jsonify( **dicRet)

                        if not isinstance(postDatatostrList[thisNum],post_parametertype[x]):
                            if postDatatostrList[thisNum] != "null":
                                dicRet["Response"] = "Error type of '{}',it must be a {}".format(fieldList[x],datatype[post_parametertype[x]])
                                return jsonify( **dicRet)

                        if not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int)):
                            if postDatatostrList[thisNum] != "null":
                                #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                                postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                            else:
                                postDataList[fieldList[x]] = None
                                # https://stackoverflow.com/questions/32959336/how-to-insert-null-value-in-sqlalchemy
                        else:
                            postDataList[fieldList[x]] = postDatatostrList[thisNum]

                if not postDataList:
                    dicRet["Response"] = "更新失敗：沒有給予任何資料欄位"
                    return jsonify( **dicRet)
                
                #============若有修改隸屬關係，去查詢是否有此隸屬單位============
                #noumenon_type與noumenon_id不可能有其一為空，若有此參數表示有要轉移資料表
                #若原本就有抓到db_name就不用去找隸屬的db_name了，也不用搬移資料表
                if reqdataDict.get("noumenon_type") is not None:
                    if postDataList["noumenon_type"] is None or postDataList["noumenon_type"] == "" or postDataList["noumenon_id"] is None:
                        if this_dbname is None:
                            updatestatus.append("Error: (id : '{}' 原本有隸屬關係，不能改成null)".format(thisid))
                            thisupdate_fail = True
                        else:
                            postDataList["noumenon_type"] = None
                            postDataList["noumenon_id"] = None
                    else:
                        if postDataList["noumenon_type"] not in ["dep","site","pla","dev"]:
                            updatestatus.append("Error : 'noumenon_type' data : '{}' not in ['dep','site','pla','dev']".format(postDataList["noumenon_type"]))
                            thisupdate_fail = True
                        else:
                            if this_dbname is None:
                                #抓取新的的隸屬資料庫名稱
                                result,new_dbname = _check_idtype_createDB_ornot(reqdataDict,thisNum,tableName,metadata,sess,False)
                                if not result:
                                    updatestatus.append("Error: {}".format(new_dbname))
                                    thisupdate_fail = True
                                else:
                                    if new_dbname is None:
                                        updatestatus.append("Error: (this : 'noumenon_type' : '{}' & 'noumenon_id' : '{}' 找不到隸屬資料庫，更新失敗)".format(postDataList["noumenon_type"],postDataList["noumenon_id"]))
                                        thisupdate_fail = True
                                    else:
                                        #抓取隸屬於此次欲更新id的所有下階關係列表，要避免隸屬到自己的小孩
                                        noumenon_sensorList,_,noumenonDict = _retrieve_noumenon_list(metadata,sess,tableName,thisid,[],[],{"dep":[],"site":[],"pla":[],"dev":[]})
                                        if postDataList["noumenon_id"] in noumenonDict[postDataList["noumenon_type"]]:
                                            updatestatus.append("Error: (this : 'noumenon_type' : '{}' & 'noumenon_id' : '{}' 為此id : '{}' 的下屬階層關係，不可隸屬)".format(postDataList["noumenon_type"],postDataList["noumenon_id"],thisid))
                                            thisupdate_fail = True
                                        else:
                                            postDataList["db_name"] = None
                                            #============轉移已存在的原本資料庫的sensor資料表============
                                            #1.抓取舊的隸屬資料庫名稱
                                            thisid_existed,old_dbname = retrieve_noumenon_dbname(metadata,sess,this_noumenon_type,this_noumenon_id)
                                            #2.先備份原本隸屬於此id的所有資料表，再刪除，然後還原至新的資料庫裡
                                            #3.判斷舊的資料庫名與新的隸屬資料庫名不同且old_dbname是否存在，判斷是否有要轉移的下階關係列表
                                            if noumenon_sensorList and (old_dbname != new_dbname) and retrieve_database_exist(SYSTEM, dbName=old_dbname, forRawData="postgres")[0]:
                                                #4.將此次欲更新id的所有下階關係列表進行轉移至新資料庫
                                                success,resultmsg = _transfer_table(SYSTEM,old_dbname,noumenon_sensorList,new_dbname)
                                                if not success:
                                                    updatestatus.append("Error: {}".format(resultmsg))
                                                    thisupdate_fail = True
                    
                if not thisupdate_fail:
                    #add update time
                    postDataList['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sess.execute(updatetargetTable.update().where(text(whereStr)).values(postDataList))
                    sess.commit()
                    err_msg = "ok"
                    #新增成功資料資訊
                    updatesuccess.append("'{}' update successful".format(whereStr))
            else:
                updatestatus.append("Error '{}' doesn't existed".format(whereStr))

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if updatesuccess:
        dicRet["updatesuccess"] = updatesuccess

    if updatestatus:
        dicRet["updatestatus"] = updatestatus

    dicRet["Response"] = err_msg 
    dicRet["Table"] = tableName 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to RelatedPG delete
# Date: 08302019@Yishan
# FOR MYSQL
#=======================================================
# {{{ RELATEDPG_API.route('/api/<SYSTEM>/1.0/my/RelatedPG/<tableName>', methods = ['DELETE'])
@RELATEDPG_API.route('/api/<SYSTEM>/1.0/my/RelatedPG/<tableName>', methods = ['DELETE'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def relatedpg_delete(SYSTEM,tableName):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除mysql特定Table的單筆或多筆資料服務(此四個表：department/site/place/device)",
        "API_parameters":{"uid":"使用者帳號"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "id":{"type":"Array","requirement":"optional","directions":"欲刪除的資料表主鍵值","example":"[3,8,...]"},
            "precautions":{
                "注意事項":"此刪除功能會一併刪除與其有關聯的所有階層關係資料，請小心使用"
            },
            "example":[
                {
                    "id":[1,2,3,4]
                }
            ]
        },
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","tableName":"資料表名稱"},
        "API_message_parameters":{"Table":"string","DB":"string","DeleteData":"JSON+各id與其關聯的所有刪除的資料，若全部刪除失敗則無此Response","deletestatus":"array+各筆資料刪除狀態，若全部刪除成功則無此Response"},
        "API_example":{
            "deletestatus": [
                "Error '(place.id = 3)' doesn't existed"
            ],
            "APIS": "DELETE /api/IOT/1.0/my/RelatedPG/place",
            "OperationTime": "0.111",
            "BytesTransferred": 272,
            "DB": "MYSQL",
            "System": "IOT",
            "DeleteData": {
                "2": {
                    "dep": [],
                    "site": [],
                    "dev": [],
                    "pla": [
                        2
                    ],
                    "PG_database": [],
                    "sensor": []
                }
            },
            "Table": "place",
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

    if not (tableName == "department" or tableName == "site" or tableName == "place" or tableName == "device"):
        dicRet["Response"] = "Try another api for update {}".format(tableName)
        return jsonify( **dicRet)
    
    if not VerifyDataStrLawyer(request.data).verify_json():
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    post_parameter = ["id"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)

    correspondence_table = {"department":"dep","site":"site","place":"pla","device":"dev"}
    
    #多筆資料刪除的狀態
    deletestatus = [] 
    #刪除資料列表
    delete_dataDict = {}
    #各表主鍵id field
    thistableidfield = "{}_id".format(tableName)

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

        deletetargetTable = Table(tableName , metadata, autoload=True)

        if not isinstance(reqdataDict.get("id"),list):
            dicRet["Response"] = "Error type of 'id',it must be an Array"
            return jsonify( **dicRet)

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        postDataKEYList = reqdataDict.get("id")
        postDataCount = len(postDataKEYList)
        if not postDataKEYList:
            dicRet["Response"] = "id : '{}' can't be Null".format(postDataKEYList)
            return jsonify( **dicRet)

        for j in range(len(postDataKEYList)):
            if not isinstance(postDataKEYList[j],int):
                dicRet["Response"] = "Error type of 'id' data : '{}' ,it must be a Integer".format(postDataKEYList[j])
                return jsonify( **dicRet)

            #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
            query_field = getattr(deletetargetTable.c,thistableidfield)
            postKeyList.append('({} = {})'.format(query_field,postDataKEYList[j]))

        #每一筆刪除資料的where條件陣列
        whereDict = [] 
        for i in range(postDataCount):
            #以間隔方式一一抓取
            whereDict.append(postKeyList[i::postDataCount])

        #每一筆刪除資料的where條件str
        for i in range(len(whereDict)):
            thisid = postDataKEYList[i]
            check_data_existed = False
            #以&來join陣列
            whereStr = " & ".join(whereDict[i])
            for row in sess.execute(deletetargetTable.select(text(whereStr))):
                drow = AdjustDataFormat().format(dict(row.items()))
                this_noumenon_type = drow["noumenon_type"]
                this_noumenon_id = drow["noumenon_id"]
                this_dbname = drow["db_name"]
                check_data_existed = True
            
            if check_data_existed:
                thisdelete_fail = False
                delete_dataDict[thisid] = {}
                #抓取隸屬於此次欲刪除id的所有下階關係列表，要一併刪除
                noumenon_sensorList,deepnoumenon_sensorList,noumenonDict = _retrieve_noumenon_list(metadata,sess,tableName,thisid,[],[],{"dep":[],"site":[],"pla":[],"dev":[]},True)
                delete_dbnameList = []
                for key,value in noumenonDict.items():
                    for i in value:
                        _,catch_dbname = retrieve_noumenon_dbname(metadata,sess,key,i)
                        delete_dbnameList.append(catch_dbname)
                #去重
                delete_dbnameList = list(set(delete_dbnameList))
                thisidPG_database = []
                #判斷此id是否有自己的資料庫
                if this_dbname is not None:
                    #直接刪除抓到的delete_dbnameList 資料庫列表
                    #並集 set(b)|set(a) | set(b).union(a)
                    if list(set(delete_dbnameList).union([this_dbname])):
                        resultmsg = delete_database(list(set(delete_dbnameList).union([this_dbname])),SYSTEM)
                        if resultmsg != "ok":
                            deletestatus.append("Error '{}'".format(resultmsg))
                            thisdelete_fail = True
                        else:
                            thisidPG_database = list(set(delete_dbnameList).union([this_dbname]))
                else:
                    #抓取此id的隸屬資料庫
                    thisid_existed,this_dbname = retrieve_noumenon_dbname(metadata,sess,this_noumenon_type,this_noumenon_id)
                    #刪除下階的資料庫
                    #差集 set(b)-set(a) | set(b).difference(a)
                    if list(set(delete_dbnameList).difference([this_dbname])):
                        resultmsg = delete_database(list(set(delete_dbnameList).difference([this_dbname])),SYSTEM)
                        if resultmsg != "ok":
                            deletestatus.append("Error '{}'".format(resultmsg))
                            thisdelete_fail = True
                        else:
                            thisidPG_database = list(set(delete_dbnameList).difference([this_dbname]))
                
                if not thisdelete_fail:
                    #刪除postgresql noumenon_sensorList資料表
                    if noumenon_sensorList: delete_tables(noumenon_sensorList,this_dbname,SYSTEM)
                    delete_dataDict[thisid]["PG_database"] = thisidPG_database
                    #加入自己id
                    noumenonDict[correspondence_table[tableName]].append(thisid)
                    #刪除mysql資料
                    _delete_mysql_data(SYSTEM, thistableidfield, sess, metadata, deepnoumenon_sensorList, noumenonDict)

                    delete_dataDict[thisid].update(deepcopy(noumenonDict))
                    delete_dataDict[thisid]["sensor"] = deepnoumenon_sensorList
                else:
                    delete_dataDict = {}
            else:
                deletestatus.append("Error '{}' doesn't existed".format(whereStr))
            
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
        
    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    if deletestatus:
        dicRet["deletestatus"] = deletestatus
    
    if delete_dataDict:
        dicRet["DeleteData"] =  delete_dataDict

    dicRet["Response"] = err_msg 
    dicRet["Table"] = tableName 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}