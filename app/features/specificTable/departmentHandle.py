# -*- coding: utf-8 -*-
#Department Module Description
"""
==============================================================================
created    : 03/20/2017
Last update: 03/31/2021
Developer: Wei-Chun Chang 
Lite Version 2 @Yishan08212019
API version 1.0
 
Filename: departmentHandle.py

Description: basically, all writes to the module will be opened to superuser only, for others, can only query data
    1. register a department
    2. query Department basic info.
    3. query Department members
    4. query Department sensors
Total = 2 APIs
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
#{{{
from sqlalchemy import *
import string
from random import randint,choice
#}}}

#=======================================================
# User level modules
#=======================================================
#{{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
from app.dbModel.sapidosystem import Department,genRawDBName
#}}}

ACCESS_SYSTEM_LIST = ["SAPIDOSYSTEM"]

#blueprint
DEPARTMENT_API = Blueprint('DEPARTMENT_API', __name__)

#=======================================================
# A function to add userList to a specific department
#=======================================================
# {{{ query_userList(depID, db_Session)
def _query_user_list(depID, db_Session):
    queryRecs = sess.query(Department.accessList).    \
            filter(Department.depID == depID).  \
            all()
    if len(queryRecs) == 0: #No redundant id in the DB
        return ""
    else:
        return queryRecs
# }}}

#=======================================================
# method to generate a department ID composite with 2 fields:
# 1. random characters 3 - 5
# 2. sequence Number: A random int between 4 to 8 digits
#=======================================================
# {{{ def _generate_depID(depName,DB_session):
def _generate_depID(sess):
    #department naming regualtion: depName_randomNumber    
    #return "{}_{}".format(depName,Noumenon, ''.join(choice(string.digits) for _ in range(randint(8,10))))
    condition = True
    depID = ""
    chars = string.ascii_uppercase + string.ascii_lowercase
    while condition:
        depID = "dep{}_{}".format(u''.join(choice(chars) for _ in range(randint(3,5))),u''.join(choice(string.digits) for _ in range(randint(4,8))))
        queryRecs = sess.query(Department.depID).    \
                filter(Department.depID == depID).  \
                all()
        if len(queryRecs) == 0: #No redundant id in the DB
            condition = False
    return depID
# }}}

#=======================================================
# API to register basic info. for a department
# { dep-name, description info}
# system will generate depID 
# FOR MYSQL
#=======================================================
# {{{ DEPARTMENT_API.route('/api/<SYSTEM>/1.0/my/department/registerDep', methods = ['POST'])
@DEPARTMENT_API.route('/api/<SYSTEM>/1.0/my/department/registerDep', methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def MYSQL_reg_Department(SYSTEM):
    #{{{APIINFO
    """
    {
        "API_application":"提供註冊mysql一部門基本資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "depID":{"type":"String","requirement":"required","directions":"部門編號","example":"site4"},
                "depName":{"type":"String","requirement":"required","directions":"部門名稱","example":"site4"},
                "noumenonType":{"type":"String","requirement":"required","directions":"母體元件類別,fac/pla/dev,可為空字串","example":"pla"},
                "noumenonID":{"type":"String","requirement":"required","directions":"母體元件代號,須已註冊的元件,可為空字串","example":"pla4"},
                "accessList":{"type":"String","requirement":"required","directions":"群組權限編號","example":{"mes":true}},
                "depInfo":{"type":"String","requirement":"required","directions":"部門介紹","example":"site4"},
                "creatorID":{"type":"String","requirement":"required","directions":"使用者ID,須已註冊","example":"uid"},
                "creDB":{"type":"String","requirement":"required","directions":"需要開資料庫,內容限制:yes/no","example":"no"}
            }
        },
        "API_message_parameters":{
            "depID":"string",
            "depName":"string",
            "CreateDB":"string",
            "CreateorID":"string",
            "DB":"string"
        },
        "API_example":{
            "APIS": "POST /api/SAPIDOSYSTEM/1.0/my/department/registerDep",
            "OperationTime": "2.421",
            "BytesTransferred": 128,
            "Response": "ok",
            "depName":"DEPTry",
            "depID":"DEPTry_69804463",
            "CreateDB":"yes",
            "CreateorID":"",
            "DB":"MYSQL"
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
        
    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)
        
    post_parameter = ["depID","depName","noumenonType","noumenonID","accessList","depInfo","creatorID","creDB"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet) 
    
    depID = reqdataDict.get("depID").encode('utf8').strip() 
    depName =  reqdataDict.get("depName").encode('utf8').strip() 
    noumenonType = reqdataDict.get("noumenonType").encode('utf8').strip() 
    noumenonID = reqdataDict.get("noumenonID").encode('utf8').strip() 
    accessList = reqdataDict.get("accessList") 
    depInfo = reqdataDict.get("depInfo").encode('utf8').strip() 
    creatorID = reqdataDict.get("creatorID").encode('utf8').strip()
    creDB = reqdataDict.get("creDB").encode('utf8').strip()
    
    try:
        #fill-in to object Department for insertion
        DbSession,_,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()
        
        queryRecs = sess.query(Department.depID).    \
                filter(Department.depID == func.binary(depID)).  \
                all()

        err_msg = "error"
        
        if len(queryRecs) == 0:
            #---------------------------------------------------------
            # previous: before 02212019
            #     generate an ID for object
            #     with checking in the method, can quanrantee a unique object ID is generated
            #     depID = _generate_depID(sess)
            # current: 0221/2019
            #---------------------------------------------------------
            # call for Raw Data DB generation
            #---------------------------------------------------------
            if creDB in ('yes', 'Yes', 'YES'):
                dbName = ""
                dbName = genRawDBName(depID, "dep")
                if not app.dbEntityExisted(dbName,forRawData="postgres"):
                    app.createDbEntity(dbName,forRawData="postgres")
            else:
                dbName = ""

            newDepRec = Department(depID = depID, \
                    noumenonID = noumenonID, \
                    noumenonType = noumenonType, \
                    creatorID = creatorID, \
                    depName = depName, \
                    dbName = dbName,\
                    accessList = accessList, \
                    depInfo = depInfo) 

            sess.add(newDepRec)
            err_msg = "ok"   
            #commit insertion
            sess.commit()

            dicRet["dbName"] = dbName
        else:
            #update user data here
            depID = "-------"
            depTitle = "-------"
            err_msg = "department is exist"

        dicRet["depName"] = depName
        dicRet["CreateDB"] = creDB

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["Response"] = err_msg
    dicRet["depID"] = depID
    dicRet["CreatorID"] = creatorID
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to update a department
# Date: sandy@06202019
# FOR MYSQL
#=======================================================
# {{{ DEPARTMENT_API.route('/api/<SYSTEM>/1.0/my/department/update_Department', methods = ['PATCH'])
@DEPARTMENT_API.route('/api/<SYSTEM>/1.0/my/department/update_Department', methods = ['PATCH'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def MYSQL_update_Department(SYSTEM):
    #{{{APIINFO
    """
    {
        "API_application":"提供更新mysql一部門基本資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "depID":{"type":"String","requirement":"required","directions":"部門編號","example":"site4"},
                "depName":{"type":"String","requirement":"required","directions":"部門名稱","example":"site4"},
                "accessList":{"type":"String","requirement":"required","directions":"群組權限編號","example":{"mes":true}},
                "depInfo":{"type":"String","requirement":"required","directions":"部門介紹","example":"site4"}
            }
        },
        "API_message_parameters":{"depID":"string"},
        "API_example":{
            "APIS": "PATCH /api/SAPIDOSYSTEM/1.0/my/department/update_Department",
            "OperationTime": "2.421",
            "BytesTransferred": 128,
            "Response": "ok",
            "depID":"DEPTry_69804463",
            "DB":"MYSQL"
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

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    post_parameter = ["depID","depName","accessList","depInfo"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)    

    depID = reqdataDict.get("depID").encode('utf8').strip()

    try:
        DbSession,_,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        #check user id- use old ID if exists
        queryRecs = sess.query(Department.depID).    \
                filter(Department.depID == func.binary(depID)).  \
                all()

        #err_msg = "error"

        #sandy@06142019 add pay_rate for cost
        if len(queryRecs) == 0:
            err_msg = "department does not exist!"

        else:
            sess.query(Department.depID, Department.depName,Department.accessList, Department.depInfo). \
                    filter(Department.depID == depID).\
                    update({"depID": Department.depID, \
                            "depName": reqdataDict.get("depName").encode('utf8').strip(), \
                            "accessList":reqdataDict.get("accessList"), \
                            "depInfo":reqdataDict.get("depInfo").encode('utf8').strip()})
            err_msg = "ok" #done successfully

        #commit insertion
        sess.commit()

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

    dicRet["depID"] = depID
    dicRet["Response"] = err_msg 
    dicRet["DB"] = "MYSQL"

    return jsonify( **dicRet)
# }}}

