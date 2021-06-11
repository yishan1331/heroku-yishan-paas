# -*- coding: utf-8 -*-
#User module description
"""
==============================================================================
created    : 
Last update: 03/31/2021
Developer: Wei-Chun Chang 
Lite Version 2 @Yishan08212019
API Version 1.0

Filename: userHandle.py

Description: 

Total = 3 APIs
* wei@03272018 add an API(/api/VUESYSTEM/query/tableData): to retrieve all data in a table
==============================================================================
"""

#=======================================================
# System level modules
#=======================================================
# {{{
from sqlalchemy import *
import string
from random import randint,choice,sample
#08382019@Yishan add for 加密password
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
# }}}

#=======================================================
# User-defined modules
#=======================================================
# {{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
from app.dbModel.sapidosystem import Department
from app.dbModel.sapidosystem import User as sapidosystem_User
from app.dbModel.iot import User as iot_User
# }}}

ACCESS_SYSTEM_LIST = ["SAPIDOSYSTEM","IOT","CHUNZU","YS"]

#blueprint
USER_API = Blueprint('USER_API', __name__)

#=======================================================
# Definition: To retrieve sensor raw table name and other info.
# reserve for future usage
# return queryRec[] = [noumenonID, noumenonType, senRawTable, creatorID]
#=======================================================
#{{{ def _retrieve_senRawTable(sess, senID)
def _retrieve_senRawTable(sess,tableID,del_ID):
    if tableID == "Department":
        queryRecs = sess.query(Department.noumenonID,\
                    Department.noumenonType, \
                    Department.dbName,\
                    Department.depID). \
            filter(Department.depID == func.binary(del_ID)).\
            all()
    else:
        return ""

    if len(queryRecs) == 0:
        return "" #no ID has found
    else:
        return queryRecs[0]
#}}}

#=======================================================
# method to generate a user ID composite with 3 fields:
# 1. user name
# 2. Noumenon which a sensor is rooted
# 3. random int between 8 to 10 digits
#=======================================================
# {{{ def _generate_userID(userName,Noumenon):
def _generate_userID(sess):
    #vednor namingregualtion: userName_userDomain_time_randomNumber    
    #return "{}_{}_{}".format(uname,Noumenon, ''.join(choice(string.digits) for _ in range(randint(8,10))))
    condition = True
    uid = ""
    chars = string.ascii_uppercase + string.ascii_lowercase
    while condition:
        #uid = "{}_{}_{}".format(uname,Noumenon, ''.join(choice(string.digits) for _ in range(randint(8,10))))
        uid = "{}_{}".format(u''.join(choice(chars) for _ in range(randint(3,6))), u''.join(choice(string.digits) for _ in range(randint(4,7))))
        queryRecs = sess.query(User.uid).    \
                filter(User.uid == uid).  \
                all()
        if len(queryRecs) == 0: #No redundant id in the DB
            condition = False
    return uid
# }}}

#=======================================================
# method to generate a random password for a user
#=======================================================
# {{{ def generate Pwd Str():
def _generate_pwdstr():
    #8-10 chars mix with digits    
    return "{}".format(u''.join(choice(string.ascii_letters + string.digits) for _ in range(randint(6,10))))
#}}}

#=======================================================
# method to generate a random str for AES IV
#=======================================================
#{{{ def _get_random()
def _get_random(size):
    return "".join(sample(string.letters+string.digits,size))
# }}}

#=======================================================
# API to register a user{uname, noumenon, phone,uinfo}
# system will generate uid and pwd for user
# FOR MYSQL
#=======================================================
# {{{ USER_API.route('/api/<SYSTEM>/1.0/my/user/reg_User', methods = ['POST'])
@USER_API.route('/api/<SYSTEM>/1.0/my/user/reg_User', methods = ['POST'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def MYSQL_reg_User(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供註冊mysql一使用者帳號資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "uid":{"type":"String","requirement":"required","directions":"使用者帳號","example":"test"},
                "pwd":{"type":"String","requirement":"required","directions":"使用者密碼，不超過16 bytes，以免加密後密碼長度太長","example":"1234"},
                "uname":{"type":"String","requirement":"required","directions":"使用者名稱","example":"test"},
                "uinfo":{"type":"String","requirement":"required","directions":"使用者描述","example":"test"},
                "email":{"type":"String","requirement":"required","directions":"使用者公司信箱","example":"test@sapido.com.tw"},
                "noumenonType":{"type":"String","requirement":"required","directions":"隸屬類別","example":"site4"},
                "noumenonID":{"type":"String","requirement":"required","directions":"隸屬編號","example":"site4"},
                "accessList":{"type":"String","requirement":"required","directions":"個人權限編號","example":{"mes":true}},
                "creatorID":{"type":"String","requirement":"required","directions":"創建者ID","example":"site4"}
            }
        },
        "API_message_parameters":{"uid":"string","DB":"string"},
        "API_example":{
            "APIS": "POST /api/VUESYSTEM/1.0/my/user/reg_User",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "uid":"-----",
            "DB":"MYSQL"
        }
    }
    '''
    #}}}
    #-----------------------------------------------------------
    # method=POST a user 
    # wei@03152017 temporarily disable
    # for uid & pwd string checking
    # dicRet = appPaaS.preProcessRequest(request,system="VUESYSTEM")
    #-----------------------------------------------------------
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

    # retrieve user info from request followed the schema of table 'user' 
    # scenario: avoid to have identical user re-generate from ID generation
    # we need to check ID from DB first, if exist, then re-generate
    # another issue: what happen if "update A user" is added to the API?
    # possible to have a message from client to indicate it's a update or register operation
    # 04132017: need to double check if ulevel exists? Normally, the ulevel will come from client side
    # which was obtained by querying to PaaS server

    if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
        post_parameter = ["uID","pwd","uName","uInfo","email","noumenonType","noumenonID","accessList","creatorID"]
    else:
        post_parameter = ["user_id","cus_id","pwd","name","email","access_list","creator","modifier"]
        
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)    

    if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
        userID = reqdataDict.get("uID").encode('utf8').strip()
        pwd = reqdataDict.get("pwd").encode('utf8').strip()
        uName = reqdataDict.get("uName").encode('utf8').strip()
        uInfo = reqdataDict.get("uInfo").encode('utf8').strip()
        email = reqdataDict.get("email").encode('utf8').strip()
        noumenonType = reqdataDict.get("noumenonType").encode('utf8').strip()
        noumenonID = reqdataDict.get("noumenonID").encode('utf8').strip()
        accessList = reqdataDict.get("accessList")
        creatorID = reqdataDict.get("creatorID").encode('utf8').strip()
    else:
        userID = reqdataDict.get("user_id").encode('utf8').strip()
        cus_id = reqdataDict.get("cus_id")
        pwd = reqdataDict.get("pwd").encode('utf8').strip()
        name = reqdataDict.get("name").encode('utf8').strip()
        email = reqdataDict.get("email").encode('utf8').strip()
        access_list = reqdataDict.get("access_list")
        creator = reqdataDict.get("creator").encode('utf8').strip()
        modifier = reqdataDict.get("modifier").encode('utf8').strip()
    
    if len(pwd) > 16:
        dicRet["Response"] = "length of pwd need smaller than 16"
        return jsonify( **dicRet)

    try:
        DbSession,_,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
            queryRecs = sess.query(sapidosystem_User.uID).\
                    filter(sapidosystem_User.uID == func.binary(userID)).\
                    all()
        else:
            queryRecs = sess.query(iot_User.user_id).\
                    filter(iot_User.user_id == func.binary(userID)).\
                    all()

        if len(queryRecs) != 0:
            dicRet["Response"] = "Error: user id : '{}' existed".format(userID)
            return jsonify( **dicRet)

        AES_IV = userID
        AES = Prpcrypt(dicConfig.get('aes_key'), AES_IV, SYSTEM)
        status,AESEN_PWD = AES.encrypt(pwd)
        if not status:
            dicRet["Response"] = AESEN_PWD
            return jsonify( **dicRet)

        if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
            newUserRec = sapidosystem_User(uID = str(userID),\
                pwd = AESEN_PWD,\
                uName = uName,\
                uInfo = uInfo,\
                email = email,\
                noumenonType = noumenonType,\
                noumenonID = noumenonID,\
                accessList = accessList,\
                creatorID = creatorID)
        else:
            newUserRec = iot_User(user_id = str(userID),\
                cus_id = cus_id,\
                pwd = AESEN_PWD,\
                name = name,\
                email = email,\
                access_list = access_list,\
                creator = creator,\
                modifier = modifier)

        sess.add(newUserRec)
        sess.commit()

        err_msg = "ok" #done successfully:

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
# API to update a user{custID, cust_name, contID, countID, address, postcode}
# FOR MYSQL
#=======================================================
# {{{ USER_API.route('/api/<SYSTEM>/1.0/my/user/update_User', methods = ['PATCH'])
@USER_API.route('/api/<SYSTEM>/1.0/my/user/update_User', methods = ['PATCH'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def MYSQL_update_User(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供更新mysql一使用者基本資料服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "old_uid":{"type":"String","requirement":"required","directions":"原始使用者帳號","example":"test"},
                "new_uid":{"type":"String","requirement":"required","directions":"更新使用者帳號","example":"test2"},
                "pwd":{"type":"String","requirement":"required","directions":"使用者密碼，不超過16 bytes，以免加密後密碼長度太長","example":"2222"},
                "uname":{"type":"String","requirement":"required","directions":"使用者名稱","example":"test"},
                "uinfo":{"type":"String","requirement":"required","directions":"使用者描述","example":"test"},
                "email":{"type":"String","requirement":"required","directions":"使用者公司信箱","example":"test@sapido.com.tw"},
                "noumenonType":{"type":"String","requirement":"required","directions":"隸屬類別","example":"site4"},
                "noumenonID":{"type":"String","requirement":"required","directions":"隸屬編號","example":"site4"},
                "accessList":{"type":"String","requirement":"required","directions":"個人權限編號","example":"site4"}
            }
        },
        "API_message_parameters":{"userID":"string","userName":"string","DB":"string"},
        "API_example":{
            "APIS": "PATCH /api/VUESYSTEM/1.0/my/user/update_User",
            "OperationTime": "0.033",
            "Response": "ok",
            "BytesTransferred": 76,
            "userID":"AP3",
            "userName":"aaa",
            "DB":"MYSQL"
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

    #collect data items from a request
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)

    if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
        post_parameter = ["old_uID","new_uID","pwd","uName","uInfo","email","noumenonType","noumenonID","accessList","creatorID"]
    else:
        post_parameter = ["old_user_id","new_user_id","cus_id","pwd","name","email","access_list","modifier"]

    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)  

    if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
        old_userID = reqdataDict.get("old_uID").encode('utf8').strip()
        new_userID = reqdataDict.get("new_uID").encode('utf8').strip()
        uName = reqdataDict.get("uName").encode('utf8').strip()
        pwd = reqdataDict.get("pwd").encode('utf8').strip()
        uInfo = reqdataDict.get("uInfo").encode('utf8').strip()
        email = reqdataDict.get("email").encode('utf8').strip()
        noumenonType = reqdataDict.get("noumenonType").encode('utf8').strip()
        noumenonID =  reqdataDict.get("noumenonID").encode('utf8').strip()
        accessList = reqdataDict.get("accessList")
        creatorID = reqdataDict.get("creatorID").encode('utf8').strip()
    else:
        old_userID = reqdataDict.get("old_user_id").encode('utf8').strip()
        new_userID = reqdataDict.get("new_user_id").encode('utf8').strip()
        cus_id = reqdataDict.get("cus_id")
        pwd = reqdataDict.get("pwd").encode('utf8').strip()
        name = reqdataDict.get("name").encode('utf8').strip()
        email = reqdataDict.get("email").encode('utf8').strip()
        access_list = reqdataDict.get("access_list")
        modifier = reqdataDict.get("modifier").encode('utf8').strip()
            
    if len(pwd) > 16:
        dicRet["Response"] = "length of pwd need smaller than 16"
        return jsonify( **dicRet)

    try:
        DbSession,_,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
            queryRecs = sess.query(sapidosystem_User.uID).    \
                    filter(sapidosystem_User.uID == func.binary(old_userID)).  \
                    all()
                    
            updateUserRec = {
                "uID": new_userID,
                "uName":uName,
                "uInfo":uInfo,
                "email":email,
                "noumenonType":noumenonType,
                "noumenonID":noumenonID,
                "accessList":accessList,
                "creatorID":creatorID
            }
        else:
            queryRecs = sess.query(iot_User.user_id).    \
                    filter(iot_User.user_id == func.binary(old_userID)).  \
                    all()
                    
            updateUserRec = {
                "user_id": new_userID,
                "cus_id": cus_id,
                "name":name,
                "email":email,
                "access_list":access_list,
                "modifier":modifier
            }

        if len(queryRecs) == 0:
            dicRet["Response"] = "Error: user id : '{}' does not exist!".format(old_userID)
            return jsonify( **dicRet)

        AES_IV = str(new_userID)
        AES = Prpcrypt(dicConfig.get('aes_key'), AES_IV, SYSTEM)
        status,AESEN_PWD = AES.encrypt(pwd)
        if not status:
            dicRet["Response"] = AESEN_PWD
            return jsonify( **dicRet)
        
        updateUserRec["pwd"] = AESEN_PWD

        if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
            sess.query(sapidosystem_User).\
                filter(sapidosystem_User.uID == old_userID).\
                update(updateUserRec)
        else:
            sess.query(iot_User).\
                filter(iot_User.user_id == old_userID).\
                update(updateUserRec)
        sess.commit()
        err_msg = "ok"
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
# method to delete a user profile
# uid-> user with priority to operate this API
# del_uid -> uid to be deleted
# FOR MYSQL
#=======================================================
#{{{ @USER_API.route('/api/<SYSTEM>/1.0/my/user/delete_user', methods=['DELETE'])
@USER_API.route('/api/<SYSTEM>/1.0/my/user/delete_User', methods=['DELETE'])
@decorator_update_docstring_parameter(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
@decorator_check_legal_system(ACCESS_SYSTEM_LIST=list(set(globalvar.SYSTEMLIST[globalvar.SERVERIP]).intersection(set(ACCESS_SYSTEM_LIST))))
def MYSQL_delete_a_user(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除mysql一使用者基本資料的服務",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "uID":{"type":"String","requirement":"required","directions":"欲刪除的uID","example":"test"}
        },
        "API_message_parameters":{"userID":"string","DB":"string"},
        "API_example":{
            "APIS": "DELETE /api/VUESYSTEM/1.0/my/user/delete_User",
            "OperationTime": "0.021",
            "Response": "ok",
            "BytesTransferred": 683,
            "userID":"v002",
            "DB":"MYSQL"
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
    
    reqdataDict = json.loads(request.data)
    if isinstance(reqdataDict,type(u"")):
        reqdataDict = json.loads(reqdataDict)
    
    if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
        post_parameter = ["uID"]
    else:
        post_parameter = ["user_id"]
    if not check_post_parameter_exist(reqdataDict,post_parameter):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)    

    if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
        del_userID = reqdataDict.get("uID").encode('utf8').strip()
    else:
        del_userID = reqdataDict.get("user_id").encode('utf8').strip()

    try:
        #fill-in to object User for insertion
        DbSession,_,engine= appPaaS.getDbSessionType(system=SYSTEM)
        if DbSession is None:
            #表示連接資料庫有問題
            dicRet["Response"] = engine
            return jsonify( **dicRet)
        
        sess = DbSession()

        if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
            queryRecs = sess.query(sapidosystem_User.uID).    \
                    filter(sapidosystem_User.uID == func.binary(del_userID)).  \
                    all()
        else:
            queryRecs = sess.query(iot_User.user_id).    \
                    filter(iot_User.user_id == func.binary(del_userID)).  \
                    all()

        if len(queryRecs) != 0:
            dicRet["Response"] = "Error: user id : '{}' existed".format(del_userID)
            return jsonify( **dicRet)

        if globalvar.MYSQL_USER_ID[globalvar.SERVERIP] == "uID":
            sess.query(sapidosystem_User.uID).\
                filter(sapidosystem_User.uID == del_userID).\
                delete()
        else:
            sess.query(iot_User.user_id).\
                filter(iot_User.user_id == del_userID).\
                delete()

        sess.commit()
        err_msg = "ok"
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