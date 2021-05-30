# -*- coding: utf-8 -*-
#module description
"""
==============================================================================
created    : 
Last update: 03/31/2021
Developer: Yi-Shan Tsai 
Lite Version 2 @Yishan08212019
API Version 1.0

Filename: inMemoryDBHandle.py

Description: 連接redis api

Total = 8 APIs
==============================================================================
"""
#=======================================================
# System level modules
#=======================================================
#{{{
from sqlalchemy import *
#}}}

#=======================================================
# User-defined modules
#=======================================================
# {{{
from app import *
#Yishan@05212020 added for common modules
from app.modules import *
# }}}

#blueprint
INMEMORYDB_API = Blueprint('INMEMORYDB_API', __name__)

class _RedisQueryAction(object):
    def __init__(self,dbRedis,datatype,key):
        self.dbRedis = dbRedis
        self.datatype = datatype
        self.key = key

    def get_value(self):
        dataDict = {
            "string":self._string,
            "list":self._list, #lrange(0,-1)
            "set":self._set,
            "zset":self._zset, #zrange(0,-1)
            "hash":self._hash,
        }
        return dataDict[self.datatype]()
        
    def _string(self):
        return self.dbRedis.get(self.key)

    def _list(self):
        return self.dbRedis.lrange(self.key,0,-1)

    def _set(self):
        return self.dbRedis.smembers(self.key)

    def _zset(self):
        return self.dbRedis.zrange(self.key,0,-1)

    def _hash(self):
        return self.dbRedis.hgetall(self.key)

class _RedisInsertUpdateAction(object):
    def __init__(self, dbRedis, datatype, data, whichAction, setExpireTime):
        self.dbRedis = dbRedis
        self.datatype = datatype
        self.data = data
        self.whichAction = whichAction
        self.doAction = "update"
        if whichAction == "Insert":
            self.doAction = "add"

        self.setExpireTime = setExpireTime
        self.err_msg = []
    
    def set_value(self):
        dataDict = {
            "string":self._string,
            "list":self._list_set,
            "set":self._list_set,
            "zset":self._zset_hash,
            "hash":self._zset_hash,
        }
        return dataDict[self.datatype]()
        
    def _string(self):
        try:
            if self.setExpireTime:
                for key,value in self.data["data"].items():
                    if self.dbRedis.exists(key) and self.whichAction == "Insert":
                        self.err_msg.append("Failed to {} Key:'{}' because already exists".format(self.doAction,key))
                        continue

                    if not self.dbRedis.exists(key) and not self.whichAction == "Insert":
                        self.err_msg.append("Failed to {} Key:'{}' because does not exist".format(self.doAction,key))
                        continue

                    if isinstance(value,dict) or isinstance(value,list):
                        self.err_msg.append("Failed to {} Key:'{}' -> Value:'{}' because Value cannot be an Array or Object".format(self.doAction,key,value))
                        continue

                    if self.data["expire_time"].get(key) is None:
                        self.dbRedis.set(key,value)
                        self.err_msg.append("Key:'{}' doesn't have expire_time,but {} successfully with no expire_time".format(key,self.doAction))
                        continue

                    if not (isinstance(self.data["expire_time"][key],int) and self.data["expire_time"][key] > 0):
                        self.err_msg.append("Failed to add Key:'{}' beacuse expire_time:{} must be positive integer and greater than zero".format(key,self.data["expire_time"][key]))
                        continue

                    self.dbRedis.setex(key, self.data["expire_time"][key], value)
            else:
                self.dbRedis.mset(self.data["data"])
        except Exception as e:
            self.err_msg.append(str(e))

        return self.err_msg

    def _list_set(self):
        try:
            for key,value in self.data["data"].items():
                if self.dbRedis.exists(key) and self.whichAction == "Insert":
                    self.err_msg.append("Failed to {} Key:'{}' because already exists".format(self.doAction,key))
                    continue

                if not self.dbRedis.exists(key) and not self.whichAction == "Insert":
                    self.err_msg.append("Failed to {} Key:'{}' because does not exist".format(self.doAction,key))
                    continue

                if not isinstance(value,list):
                    self.err_msg.append("Failed to add Key:'{}' -> Value:'{}' because value must be an Array".format(key,value))
                    continue
                if not value:
                    self.err_msg.append("Failed to add Key:'{}' -> Value:'{}' because value cannot be empty.".format(key,value))
                    continue

                #若是更新key則先把key刪了再建一個新的
                if self.whichAction != "Insert": self.dbRedis.delete(key)

                if self.setExpireTime:
                    if self.data["expire_time"].get(key) is None:
                        self.dbRedis.rpush(key, *value) if self.datatype == "list" else self.dbRedis.sadd(key, *value)
                        self.err_msg.append("Key:'{}' doesn't have expire_time,but added successfully with no expire_time".format(key))
                        continue

                    if not (isinstance(self.data["expire_time"][key],int) and self.data["expire_time"][key] > 0):
                        self.err_msg.append("Failed to add Key:'{}' beacuse expire_time:{} must be positive integer and greater than zero".format(key,self.data["expire_time"][key]))
                        continue

                self.dbRedis.rpush(key, *value) if self.datatype == "list" else self.dbRedis.sadd(key, *value)
                if self.setExpireTime: self.dbRedis.expire(key,self.data["expire_time"][key])
        except Exception as e:
            self.err_msg.append(str(e))

        return self.err_msg

    def _zset_hash(self):
        try:
            for key,value in self.data["data"].items():
                if self.dbRedis.exists(key) and self.whichAction == "Insert":
                    self.err_msg.append("Failed to {} Key:'{}' because already exists".format(self.doAction,key))
                    continue

                if not self.dbRedis.exists(key) and not self.whichAction == "Insert":
                    self.err_msg.append("Failed to {} Key:'{}' because does not exist".format(self.doAction,key))
                    continue

                if not isinstance(value,dict):
                    self.err_msg.append("Failed to add Key:'{}' -> Value:'{}' because value must be an Object".format(key,value))
                    continue
                if not value:
                    self.err_msg.append("Failed to add Key:'{}' -> Value:'{}' because value cannot be empty.".format(key,value))
                    continue

                if self.datatype == "zset":
                    legalvalue = True
                    for i in value.values():
                        if not (isinstance(i,int) or isinstance(i,float)):
                            self.err_msg.append("Failed to add Key:'{}' -> Value:'{}' beacuse value's value must be an integer".format(key,value))
                            legalvalue = False
                            break
                    if not legalvalue: continue
                
                #若是更新key則先把key刪了再建一個新的
                if self.whichAction == "Put": self.dbRedis.delete(key)

                if self.setExpireTime:
                    if self.data["expire_time"].get(key) is None:
                        self.dbRedis.zadd(key, value) if self.datatype == "zset" else self.dbRedis.hmset(key, value)
                        self.err_msg.append("Key:'{}' doesn't have expire_time,but added successfully with no expire_time".format(key))
                        continue

                    if not (isinstance(self.data["expire_time"][key],int) and self.data["expire_time"][key] > 0):
                        self.err_msg.append("Failed to add Key:'{}' beacuse expire_time:{} must be positive integer and greater than zero".format(key,self.data["expire_time"][key]))
                        continue
                
                self.dbRedis.zadd(key, value) if self.datatype == "zset" else self.dbRedis.hmset(key, value)
                if self.setExpireTime: self.dbRedis.expire(key,self.data["expire_time"][key])
        except Exception as e:
            self.err_msg.append(str(e))

        return self.err_msg

def operate_CU_integration(reqdataDict, dbRedis, whichAction):
    if whichAction in ["Insert","Put"]:
        redis_key_type = ["string","list","set","zset","hash"]
    else:
        redis_key_type = ["zset","hash"]

    status = {}
    anydata = False
    for this_key_type in redis_key_type:
        if reqdataDict.get(this_key_type) is not None:
            anydata = True
            if not check_post_parameter_exist(reqdataDict.get(this_key_type),["data"]):
                status[this_key_type] = ["Data : {} ,Missing post parameters : '{}'".format(reqdataDict.get(this_key_type),post_parameter)]
                continue
            
            setExpireTime = False
            if "expire_time" in reqdataDict.get(this_key_type).keys(): setExpireTime = True
            #若key有要設定有效期限，則一筆一筆修改(較慢)，否則一次修改(較快)
            status[this_key_type] = _RedisInsertUpdateAction(dbRedis,this_key_type,reqdataDict.get(this_key_type),whichAction,setExpireTime).set_value()

    if not anydata:
        return False, "Faild to {},because no correct data".format(whichAction)
    return True, status

#=======================================================
# API to CommonUse query redis key
# Date: 12172020@Yishan
# FOR REDIS
#=======================================================
#{{{ INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Interval/<key>', methods = ['GET']), 
@INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/SpecificKey/<key>',  methods = ['GET'])
@decorator_check_legal_system()
def redis_commonuse_get_specific_key(SYSTEM, key):
    #{{{APIINFO
    '''
    {
        "API_application":"提供查詢redis資料庫指定key的值，若pattern為yes表示欲使用*、[]進行條件匹配查詢，例如：h*llo匹配hllo和heeeeello；h[ae]llo匹配hello和hallo，但不匹配hillo",
        "API_path_parameters":{"SYSTEM":"合法的系統名稱","key":"Key值"},
        "API_parameters":{"uid":"使用者帳號","pattern":"是否使用條件查詢(yes/no)"},
        "API_message_parameters":{"QueryValueData":"JSON","DB":"string"},
        "API_example":{
            "APIS": "GET /api/IOT/1.0/rd/CommonUse/Specific/test_zset",
            "OperationTime": "0.001",
            "DB": "REDIS",
            "System": "IOT",
            "BytesTransferred": 140,
            "QueryValueData": [
                "member",
                "dadsd"
            ],
            "Response": "ok"
        }
    }
    '''
    #}}}
    err_msg = "error"
    if SYSTEM == "test": SYSTEM = "IOT"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid","pattern"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    pattern = request.args.get("pattern").encode('utf-8') 
    if pattern not in ("yes","no"):
        dicRet["Response"] = "parameter: pattern -> {} must be yes or no".format(pattern)
        return jsonify( **dicRet)
    
    pattern = True if pattern == "yes" else False
    
    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result= appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)
        
        _keys = [key]
        if pattern: _keys = dbRedis.keys(key)

        contents = {}
        for i in _keys:
            if not dbRedis.exists(i):
                dicRet["Response"] = "Key : {} doesn't existed".format(i)
                return jsonify( **dicRet)
            
            redis_key_type = ["string","list","set","zset","hash"]

            this_key_type = dbRedis.type(i)
            if this_key_type not in redis_key_type:
                dicRet["Response"] = "Key : {} doesn't existed".format(i)
                return jsonify( **dicRet)
            
            contents[i] = _RedisQueryAction(dbRedis,this_key_type,i).get_value()
            if isinstance(contents[i],set): contents[i] = list(contents[i])
        
        if not pattern:
            dicRet["QueryValueData"] = contents[_keys[0]]
        else:
            dicRet["QueryValueData"] = contents

        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)

    dicRet["Response"] = err_msg
    dicRet["DB"] = "REDIS" 
    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse register redis key
# Date: 12172020@Yishan
# FOR REDIS
#=======================================================
# {{{ appPaaS.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['POST'])
@INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['POST'])
@decorator_check_legal_system()
def redis_commonuse_register(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供新增redis多個key&value資料",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "string":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "新增字符串形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲新增的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value只接受字串、數字、json字串類型；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲新增的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_string":123,"test_string2":"test"},"expire_time":{"test_string":60}}
                },
                "list":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "新增列表形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲新增的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為陣列且陣列的值只接受字串、數字、json字串類型；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲新增的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data": {"test_list1": [34123,"dwqad"]},"expire_time":{"test_list1":60,"test_list2":30}}
                },
                "set":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "新增無序集合形態的value，集合成員是唯一的，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲新增的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為陣列，陣列的值只接受字串、數字、json字串類型且不得重複；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲新增的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data": {"test_set1": [34123,"dwqad"]},"expire_time":{"test_set1":60}}
                },
                "zset":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "新增有序集合形態的value，集合成員是唯一的且都會關聯一個double 類型的分數，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲新增的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為物件，value物件的value必需為數字或浮點數；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲新增的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_zset": {"data1":22,"data2":10,"data3":20}},"expire_time":{"test_zset":60}}
                },
                "hash":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "新增JSON物件形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲新增的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為物件；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲新增的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_hash1":{"data1":"qqq","data2":10,"data3":20}},"expire_time":{"test_hash1":60}}
                }
            },
            "precautions":{
                "注意事項1":"data若有設定期限，則會data-key一一比對並逐一新增(速度較慢)；若無則一次新增(速度較快)"
            },
            "example":[
                {
                    "string": {
                        "data": {
                            "test_string1": 1.2,
                            "test_string2": ["sas",1321]
                        },
                        "expire_time":{
                            "test_string1":30
                        }
                    },
                    "list": {
                        "data": {
                            "test_list1": [34123,"dwqad"],
                            "test_list2": [{"data1":22,"data2":10,"data3":20},"afasfa"]
                        },
                        "expire_time":{
                            "test_list1":60,
                            "test_list2":30
                        }
                    },
                    "set": {
                        "data": {
                            "test_set1": [34123,"dwqad"],
                            "test_set2": ["tete","tete"]
                        },
                        "expire_time":{
                            "test_set1":15,
                            "test_set2":30
                        }
                    },
                    "zset": {
                        "data": {
                            "test_zset1": {"data1":"qqq","data2":10,"data3":20},
                            "test_zset2": {"data1":22,"data2":10,"data3":20}
                        },
                        "expire_time":{
                            "test_zset1":15
                        }
                    },
                    "hash": {
                        "data": {
                            "test_hash1": {"data1":"qqq","data2":10,"data3":20},
                            "test_hash2": ["tete","tete"]
                        },
                        "expire_time":{
                            "test_hash1":15,
                            "test_hash2":30
                        }
                    }
                }
            ]
        },
        "API_message_parameters":{"DB":"string","InsertStatus":"object+各類型資料新增狀態，若全部新增成功則無此Response"},
        "API_example":{
            "APIS": "POST /api/IOT/1.0/rd/CommonUse/Keys",
            "InsertStatus": {
                "hash": [
                    "Failed to add Key:'test_hash2' -> Value:'['tete', 'tete']' because value must be an Object"
                ],
                "string": [
                    "Invalid input of type: 'list'. Convert to a byte, string or number first."
                ],
                "zset": [
                    "Failed to add Key:'test_zset1' -> Value:'{'data1': 'qqq', 'data3': 20, 'data2': 10}' beacuse value's value must be an integer",
                    "Key:'test_zset2' doesn't have expire_time,but added successfully with no expire_time"
                ]
            },
            "BytesTransferred": 521,
            "OperationTime": "0.004",
            "DB": "REDIS",
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

    #collect data items from a request
    reqdataDict = ConvertData().convert(json.loads(request.data))

    #多筆資料新增的狀態
    insertstatus = {} 

    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result= appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)
        
        result, insertstatus = operate_CU_integration(reqdataDict, dbRedis, "Insert")
        if not result:
            dicRet["Response"] = insertstatus
            return jsonify( **dicRet)

        # anydata = False
        # for this_key_type in redis_key_type:
        #     if reqdataDict.get(this_key_type) is not None:
        #         anydata = True
        #         if not check_post_parameter_exist(reqdataDict.get(this_key_type),["data"]):
        #             insertstatus[this_key_type] = ["Data : {} ,Missing post parameters : '{}'".format(reqdataDict.get(this_key_type),post_parameter)]
        #             continue
                
        #         setExpireTime = False
        #         if "expire_time" in reqdataDict.get(this_key_type).keys(): setExpireTime = True
        #         #若key有要設定有效期限，則一筆一筆新增(較慢)，否則一次新增(較快)
        #         insertstatus[this_key_type] = _RedisInsertUpdateAction(dbRedis,this_key_type,reqdataDict.get(this_key_type),"Insert",setExpireTime).set_value()
        # else:
        #     if not anydata:
        #         dicRet["Response"] = "Faild to add,because no correct data"
        #         return jsonify( **dicRet)
        
        for key,value in insertstatus.items():
            if not value: del insertstatus[key]
        if insertstatus: dicRet["InsertStatus"] = insertstatus
        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
            
    dicRet["Response"] = err_msg
    dicRet["DB"] = "REDIS"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse register redis key
# Date: 12172020@Yishan
# FOR REDIS
#=======================================================
# {{{ INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['PUT'])
@INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['PUT'])
@decorator_check_legal_system()
def redis_commonuse_update_all(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供修改redis多個key&value資料，為全部更新",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "string":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改字符串形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value只接受字串、數字、json字串類型；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_string":123,"test_string2":"test"},"expire_time":{"test_string":60}}
                },
                "list":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改列表形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為陣列且陣列的值只接受字串、數字、json字串類型；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data": {"test_list1": [34123,"dwqad"]},"expire_time":{"test_list1":60,"test_list2":30}}
                },
                "set":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改無序集合形態的value，集合成員是唯一的，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為陣列，陣列的值只接受字串、數字、json字串類型且不得重複；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data": {"test_set1": [34123,"dwqad"]},"expire_time":{"test_set1":60}}
                },
                "zset":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改有序集合形態的value，集合成員是唯一的且都會關聯一個double 類型的分數，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為物件，value物件的value必需為數字或浮點數；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_zset": {"data1":22,"data2":10,"data3":20}},"expire_time":{"test_zset":60}}
                },
                "hash":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改JSON物件形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)",
                                "是否必需":"必要",
                                "注意事項":"value必須為物件；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_hash1":{"data1":"qqq","data2":10,"data3":20}},"expire_time":{"test_hash1":60}}
                }
            },
            "precautions":{
                "注意事項1":"data若有設定期限，則會data-key一一比對並逐一修改(速度較慢)；若無則一次修改(速度較快)"
            },
            "example":[
                {
                    "string": {
                        "data": {
                            "test_string1": 1.2,
                            "test_string2": ["sas",1321]
                        },
                        "expire_time":{
                            "test_string1":30
                        }
                    },
                    "list": {
                        "data": {
                            "test_list1": [34123,"dwqad"],
                            "test_list2": [{"data1":22,"data2":10,"data3":20},"afasfa"]
                        },
                        "expire_time":{
                            "test_list1":60,
                            "test_list2":30
                        }
                    },
                    "set": {
                        "data": {
                            "test_set1": [34123,"dwqad"],
                            "test_set2": ["tete","tete"]
                        },
                        "expire_time":{
                            "test_set1":15,
                            "test_set2":30
                        }
                    },
                    "zset": {
                        "data": {
                            "test_zset1": {"data1":"qqq","data2":10,"data3":20},
                            "test_zset2": {"data1":22,"data2":10,"data3":20}
                        },
                        "expire_time":{
                            "test_zset1":15
                        }
                    },
                    "hash": {
                        "data": {
                            "test_hash1": {"data1":"qqq","data2":10,"data3":20},
                            "test_hash2": ["tete","tete"]
                        },
                        "expire_time":{
                            "test_hash1":15,
                            "test_hash2":30
                        }
                    }
                }
            ]
        },
        "API_message_parameters":{"DB":"string","UpdateStatus":"object+各類型資料修改狀態，若全部修改成功則無此Response"},
        "API_example":{
            "APIS": "PUT /api/IOT/1.0/rd/CommonUse/Keys",
            "UpdateStatus": {
                "hash": [
                    "Failed to add Key:'test_hash2' -> Value:'['tete', 'tete']' because value must be an Object"
                ],
                "string": [
                    "Invalid input of type: 'list'. Convert to a byte, string or number first."
                ],
                "zset": [
                    "Failed to add Key:'test_zset1' -> Value:'{'data1': 'qqq', 'data3': 20, 'data2': 10}' beacuse value's value must be an integer",
                    "Key:'test_zset2' doesn't have expire_time,but added successfully with no expire_time"
                ]
            },
            "BytesTransferred": 521,
            "OperationTime": "0.004",
            "DB": "REDIS",
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

    #collect data items from a request
    reqdataDict = ConvertData().convert(json.loads(request.data))

    #多筆資料修改的狀態
    updatestatus = {} 

    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result= appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        result, updatestatus = operate_CU_integration(reqdataDict, dbRedis, "Put")
        if not result:
            dicRet["Response"] = updatestatus
            return jsonify( **dicRet)

        # anydata = False
        # for this_key_type in redis_key_type:
        #     if reqdataDict.get(this_key_type) is not None:
        #         anydata = True
        #         if not check_post_parameter_exist(reqdataDict.get(this_key_type),["data"]):
        #             updatestatus[this_key_type] = ["Data : {} ,Missing post parameters : '{}'".format(reqdataDict.get(this_key_type),post_parameter)]
        #             continue
                
        #         setExpireTime = False
        #         if "expire_time" in reqdataDict.get(this_key_type).keys(): setExpireTime = True
        #         #若key有要設定有效期限，則一筆一筆修改(較慢)，否則一次修改(較快)
        #         updatestatus[this_key_type] = _RedisInsertUpdateAction(dbRedis,this_key_type,reqdataDict.get(this_key_type),"Put",setExpireTime).set_value()
        # else:
        #     if not anydata:
        #         dicRet["Response"] = "Faild to add,because no correct data"
        #         return jsonify( **dicRet)
        
        for key,value in updatestatus.items():
            if not value: del updatestatus[key]
        if updatestatus: dicRet["UpdateStatus"] = updatestatus
        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
            
    dicRet["Response"] = err_msg
    dicRet["DB"] = "REDIS"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse register redis key
# Date: 12172020@Yishan
# FOR REDIS
#=======================================================
# {{{ INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['PATCH'])
@INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['PATCH'])
@decorator_check_legal_system()
def redis_commonuse_partial_update(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供修改redis型態為zset、hash的key資料，為部分更新",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "zset":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改有序集合形態的value，集合成員是唯一的且都會關聯一個double 類型的分數，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)，若key不存在會直接建立",
                                "是否必需":"必要",
                                "注意事項":"value必須為物件，value物件的value必需為數字或浮點數；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_zset": {"data1":22,"data2":10,"data3":20}},"expire_time":{"test_zset":60}}
                },
                "hash":{
                    "type":"Object",
                    "requirement":"optional",
                    "directions":[
                        "修改JSON物件形態的value，詳細內容格式請看'Show Details'",
                        {
                            "data":{
                                "說明":"欲修改的key&value(object)，若key不存在會直接建立",
                                "是否必需":"必要",
                                "注意事項":"value必須為物件；資料以字串型態儲存"
                            },
                            "expire_time":{
                                "說明":"欲修改的key之有效期限(object)",
                                "是否必需":"選填",
                                "注意事項":"若需要設定key的有效期限(秒)，key需對應data的key且value必須為正整數；不需要全部data的Key都同時設定期限，可選擇指定key"
                            }
                        }
                    ],
                    "example":{"data":{"test_hash1":{"data1":"qqq","data2":10,"data3":20}},"expire_time":{"test_hash1":60}}
                }
            },
            "precautions":{
                "注意事項1":"data若有設定期限，則會data-key一一比對並逐一修改(速度較慢)；若無則一次修改(速度較快)"
            },
            "example":[
                {
                    "zset": {
                        "data": {
                            "test_zset1": {"data1":50,"data2":10,"data3":20},
                            "test_zset2": {"data1":22,"data2":10,"data3":20}
                        },
                        "expire_time":{
                            "test_zset1":15
                        }
                    },
                    "hash": {
                        "data": {
                            "test_hash1": {"data1":"qqq","data2":10,"data3":20},
                            "test_hash2": {"data11":"qqq","data22":10,"data33":20}
                        },
                        "expire_time":{
                            "test_hash1":15,
                            "test_hash2":30
                        }
                    }
                }
            ]
        },
        "API_message_parameters":{"DB":"string","UpdateStatus":"object+各類型資料修改狀態，若全部修改成功則無此Response"},
        "API_example":{
            "APIS": "PATCH /api/IOT/1.0/rd/CommonUse/Keys",
            "UpdateStatus": {
                "hash": [
                    "Failed to add Key:'test_hash2' -> Value:'['tete', 'tete']' because value must be an Object"
                ],
                "zset": [
                    "Failed to add Key:'test_zset1' -> Value:'{'data1': 'qqq', 'data3': 20, 'data2': 10}' beacuse value's value must be an integer",
                    "Key:'test_zset2' doesn't have expire_time,but added successfully with no expire_time"
                ]
            },
            "BytesTransferred": 521,
            "OperationTime": "0.004",
            "DB": "REDIS",
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

    #collect data items from a request
    reqdataDict = ConvertData().convert(json.loads(request.data))

    #多筆資料修改的狀態
    updatestatus = {} 

    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result= appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        result, updatestatus = operate_CU_integration(reqdataDict, dbRedis, "Patch")
        if not result:
            dicRet["Response"] = updatestatus
            return jsonify( **dicRet)

        # anydata = False
        # for this_key_type in redis_key_type:
        #     if reqdataDict.get(this_key_type) is not None:
        #         anydata = True
        #         if not check_post_parameter_exist(reqdataDict.get(this_key_type),["data"]):
        #             updatestatus[this_key_type] = ["Data : {} ,Missing post parameters : '{}'".format(reqdataDict.get(this_key_type),post_parameter)]
        #             continue
                
        #         setExpireTime = False
        #         if "expire_time" in reqdataDict.get(this_key_type).keys(): setExpireTime = True
        #         #若key有要設定有效期限，則一筆一筆修改(較慢)，否則一次修改(較快)
        #         updatestatus[this_key_type] = _RedisInsertUpdateAction(dbRedis, this_key_type, reqdataDict.get(this_key_type), "Patch", setExpireTime).set_value()
        # else:
        #     if not anydata:
        #         dicRet["Response"] = "Faild to add,because no correct data"
        #         return jsonify( **dicRet)
        
        for key,value in updatestatus.items():
            if not value: del updatestatus[key]
        if updatestatus: dicRet["UpdateStatus"] = updatestatus
        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
            
    dicRet["Response"] = err_msg
    dicRet["DB"] = "REDIS"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse register redis key
# Date: 12172020@Yishan
# FOR REDIS
#=======================================================
# {{{ INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Hash/Keys/SpecificField', methods = ['PATCH'])
@INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Hash/Keys/SpecificField', methods = ['PATCH'])
@decorator_check_legal_system()
def redis_commonuse_hash_update_specific_field(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供修改redis Hash型態key的指定field值，為部分更新",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "key": {"type":"Object","requirement":"required","directions":"欲更新的key，value需為物件且value->key值必須存在才能更新","example":{"test":{"qq":111,"cc":"daa"}}},
            "precautions":{
                "注意事項1":"第一層與第二層的key必須存在"
            },
            "example":[
                {
                    "test":{
                        "qq":"sdfsdf",
                        "ww":"asdasd",
                        "cc":222,
                        "ss":"dsadas",
                        "rr":"dasd"
                    }
                }
            ]
        },
        "API_message_parameters":{"UpdateStatus":"object+各類型資料更新狀態，若全部更新成功則無此Response"},
        "API_example":{
            "Response": "ok",
            "APIS": "PATCH /api/IOT/1.0/rd/CommonUse/Hash/Keys/SpecificField",
            "OperationTime": "0.002",
            "BytesTransferred": 187,
            "DB": "REDIS",
            "System": "IOT",
            "UpdateStatus": {
                "test": [
                    "key:ss doesn't existed",
                    "key:cc doesn't existed"
                ]
            }
        }
    }
    '''
    #}}}
    err_msg = "error"
    if SYSTEM == "test": SYSTEM = "IOT"
    dicRet = appPaaS.preProcessRequest(request,system=SYSTEM)

    uri_parameter = ["uid"]
    result, result_msg = check_uri_parameter_exist(request,uri_parameter)
    if not result:
        dicRet["Response"] = result_msg
        return jsonify( **dicRet)
    
    is_illegal,is_dict = VerifyDataStrLawyer(request.data).verify_json(check_dict=True)
    if not (is_illegal and is_dict):
        dicRet["Response"] = "error input '{}' is illegal JSON".format(request.data)
        return jsonify( **dicRet)
    
    #collect data items from a request
    reqdataDict = ConvertData().convert(json.loads(request.data))

    #多筆資料修改的狀態
    updatestatus = {} 

    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result= appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)

        for key,value in reqdataDict.items():
            this_obj = {}
            if not dbRedis.exists(key):
                dicRet["Response"] = "Key : {} doesn't existed".format(key)
                return jsonify( **dicRet)
            
            if not isinstance(value,dict):
                dicRet["Response"] = "Error type of '{}',it must be an Object".format(value)
                return jsonify( **dicRet)

            updatestatus[key] = []

            for field,field_value in value.items():
                if field_value is not None:
                    if not dbRedis.hexists(key, field):
                        updatestatus[key].append("key:{} doesn't existed".format(field))
                    else:
                        this_value = field_value
                        if isinstance(field_value,dict) or isinstance(field_value,list): this_value = json.dumps(field_value)
                        this_obj[field] = this_value
            
            dbRedis.hmset(key, this_obj)
        
        for key,value in updatestatus.items():
            if not value: del updatestatus[key]
        if updatestatus: dicRet["UpdateStatus"] = updatestatus

        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
            
    dicRet["Response"] = err_msg
    dicRet["DB"] = "REDIS"

    return jsonify( **dicRet)
# }}}

#=======================================================
# API to CommonUse register redis key
# Date: 12172020@Yishan
# FOR REDIS
#=======================================================
# {{{ INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['DELETE'])
@INMEMORYDB_API.route('/api/<SYSTEM>/1.0/rd/CommonUse/Keys', methods = ['DELETE'])
@decorator_check_legal_system()
def redis_commonuse_delete(SYSTEM):
    #{{{APIINFO
    '''
    {
        "API_application":"提供刪除redis多個key",
        "API_parameters":{"uid":"使用者帳號"},
        "API_path_parameters":{"SYSTEM":"合法的系統名稱"},
        "API_postData":{
            "bodytype":"Object",
            "bodyschema":"{}",
            "parameters":{
                "keys":{"type":"Array","requirement":"required","directions":"欲刪除的key列表","example":"{'keys':[123,'test',....]}"}
            },
            "example":[
                {
                    "keys":[123,"1234"]
                }
            ]
        },
        "API_message_parameters":{"DB":"string"},
        "API_example":{
            "APIS": "DELETE /api/IOT/1.0/rd/CommonUse/Keys",
            "BytesTransferred": 521,
            "OperationTime": "0.004",
            "DB": "MSSQL",
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

    #collect data items from a request
    reqdataDict = ConvertData().convert(json.loads(request.data))

    if not check_post_parameter_exist(reqdataDict,["keys"]):
        dicRet["Response"] = "Missing post parameters : '{}'".format(post_parameter)
        return jsonify( **dicRet)
    
    if not isinstance(reqdataDict.get("keys"),list):
        dicRet["Response"] = "Error type of '{}',it must be an Array".format(reqdataDict.get("keys"))
        return jsonify( **dicRet)

    try:
        redis_db = globalvar.SYSTEMLIST[globalvar.SERVERIP].index(SYSTEM)
        dbRedis,_,result= appPaaS.getDbSessionType(system=SYSTEM,dbName=redis_db,forRawData="redis")
        if dbRedis is None:
            #表示連接資料庫有問題
            dicRet["Response"] = result
            return jsonify( **dicRet)
        
        dbRedis.delete(*reqdataDict.get("keys"))
        err_msg = "ok"
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)
            
    dicRet["Response"] = err_msg
    dicRet["DB"] = "REDIS"

    return jsonify( **dicRet)
# }}}