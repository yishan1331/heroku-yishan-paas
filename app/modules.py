# -*- coding: utf-8 -*-
#Description
"""
==============================================================================
created    : 05/21/2020

Last update: 05/21/2020

Developer: Yishan Tsai 

Lite Version 1 @Yishan05212020

Filename: modules.py

Description: Common modules
==============================================================================
"""
#=======================================================
# System level modules
#=======================================================
#{{{
#Yishan 11062019 引入Counter來找出list
from collections import Counter, Mapping, Iterable
from time import strftime 
from copy import deepcopy
from functools import wraps #Yishan@011112020 add for Decorators

#08382019@Yishan add for 加密password
#import hashlib
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

from sqlalchemy import *

#=======================================================
# User-defined modules
#=======================================================
#{{{
from app import *
#}}}

#=======================================================
# regular expression
# Date: 09112019 Yishan
# 防止SQL Injection
#=======================================================
#{{{ class RegularExpression()
class RegularExpression():
    def __init__(self,data):
        self.data = data
        #一次過濾所有標點符號 https://juejin.im/post/5d50c132f265da03de3af40b
        #return re.sub('\W+', '', self.data).replace("_", '')
        #過濾常見標點符號，逗號","不過濾(SAPIDOSYSTEM需求) https://blog.csdn.net/Dongfnag_HU/article/details/85076819
        #reexp = '!;:?"\'#$%&()*+\\/\\\<=>@^_`\[\]{|}~-' 
        self.reexp = '!;:?"\'#$%&*\\\<=>@^`\[\]{|}~'

    # def re_search(self):
        #s = re.compile(r'[’!"#$%&\'()*+,-./:;<=>?@\[\]^_`{|}~？ ，。（）《》]')
        #return re.sub(s,"",self.data)
        #if bool(s.search(self.data)): #有特殊符號
        #    return True
        #else:
        #    return False

    def re_sub(self):
        return re.sub(r'[{}]+'.format(self.reexp),"",self.data)
#}}}

#=======================================================
# convert data type
# Date: 09122019 Yishan
# 轉換data型態
#=======================================================
#{{{ class ConvertData()
class ConvertData():
    #def __init__(self,data):
    #    self.data = data

    def convert(self,data):
        self.data = data
        if isinstance(self.data, basestring):
            #進行過濾非法字元
            # return str(RegularExpression(self.data).re_sub())
            return str(self.data)
        elif isinstance(self.data, Mapping):
            return dict(map(self.convert, self.data.iteritems()))
        elif isinstance(self.data, Iterable):
            return type(self.data)(map(self.convert, self.data))
        else:
            return self.data
#}}}

#=======================================================
# Definition: to do adjust format commonuse function(調整從資料庫查回來的指定類型欄位格式)
# Date: 03312020@Yishan
#=======================================================
#{{{class AdjustDataFormat()
class AdjustDataFormat():
    def format(self,drow):
        import decimal
        self.drow = drow
        for key,value in self.drow.items():
            if isinstance(value, datetime):
                self.drow[key]= value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, date):
                self.drow[key]= value.strftime('%Y-%m-%d')     
            if isinstance(value, decimal.Decimal):
                self.drow[key]= float(value)
            #Yishan@11192020 將型態是str、unicode的取消檢查verify_json 
            #(之前會檢查並轉換成json obj方便使用者使用，但若遇到全數字的字串，會一併轉成數字，會導致格式錯誤，故取消此動作)
            # if (isinstance(value, str) or isinstance(value, unicode)) and VerifyDataStrLawyer(value).verify_json():
            #     self.drow[key]= json.loads(value)
        # return self.drow
        return ConvertData().convert(self.drow)
#}}}

#=======================================================
# 檢查各式字串格式合法
# Date: 06122020 Yishan
#=======================================================
#{{{ class VerifyDataStrLawyer()
class VerifyDataStrLawyer():
    def __init__(self,data_str):
        self.data_str = data_str
    
    def _check_none(self):
        if self.data_str is None:
            return False
        return True

    def verify_date(self, is_date=False):
        if not (isinstance(self.data_str,str) or isinstance(self.data_str,unicode)): return False
        status = True
        if is_date:
            formatstr = "%Y-%m-%d"
        else:
            formatstr = "%Y-%m-%d %H:%M:%S"

        try:
            datetime.strptime(self.data_str, formatstr)
        except ValueError:
            try:
                datetime.strptime(self.data_str, '%Y-%m-%d %H:%M:%S.%f') 
            except ValueError:
                status = False
        return status     

    def verify_json(self, check_dict=False):
        is_illegal = True
        is_dict = False
        try:
            json.loads(self.data_str)
            is_dict = isinstance(json.loads(self.data_str),dict)
        except ValueError as e:
            is_illegal = False

        if check_dict:
            return is_illegal,is_dict
        return is_illegal
#}}}

#=======================================================
# Definition: 加解密class
# Date: 20190828@Yishan
# length = 16
# AES_IV = uID
# count = len(AES_IV)
# if count < length:
#     add = length - (count % length)
#     AES_IV = AES_IV + ('0' * add)
# else:
#     if count != 16:
#         AES_IV = AES_IV[:16]

# AES = Prpcrypt(dicConfig.get('aes_key'),AES_IV)
# AESEN_PWD = AES.encrypt(pwdStr)
#=======================================================
#{{{ class Prpcrypt()
class Prpcrypt():
    def __init__(self, key,iv,system):
        self.key = key #這裏密鑰key 長度必須為16（AES-128）、24（AES-192）、或32（AES-256）Bytes 長度.目前AES-128足夠用

        #初始化時將iv整理成16bytes
        if len(iv) < 16:
            add = 16 - (len(iv) % 16)
            iv = iv + ('0' * add)
        elif len(iv) != 16:
            #抓倒數16位
            iv = iv[len(iv)-16:len(iv)]
        self.iv = iv #iv必為16Bytes

        self.mode = AES.MODE_CBC
        self.system = system
    
    #加密函數，如果text(密碼)不是16的倍數【加密文本text必須為16的倍數！】，那就補足為16的倍數
    def encrypt(self, text):
        try:
            cryptor = AES.new(self.key, self.mode, self.iv)
            count = len(text)
            #目前最大長度設定到32
            if 16 < count < 32:
                length = 32
            elif count < 16:
                length = 16
            add = length - (count % length)
            text = text + ('\0' * add)
            self.ciphertext = cryptor.encrypt(text)
            #因為AES加密時候得到的字符串不一定是ascii字符集的，輸出到終端或者保存時候可能存在問題
            #所以這裏統一把加密後的字符串轉化為16進制字符串
            return True,b2a_hex(self.ciphertext)
        except Exception as e:
            return False,appPaaS.catch_exception(e,sys.exc_info(),self.system)
    
    #解密後，去掉補足的空格用strip() 去掉
    def decrypt(self, text):
        try:
            cryptor = AES.new(self.key, self.mode, self.iv)
            plain_text = cryptor.decrypt(a2b_hex(text))
            return True,plain_text.rstrip('\0')
        except Exception as e:
            return False,appPaaS.catch_exception(e,sys.exc_info(),self.system)
#}}}

#=======================================================
# Type transformation 
# Date: 06112020 Yishan
# sqlalchemy data type object
#=======================================================
#{{{ class _TypeToSqlType()
class _TypeToSqlType():
    def __init__(self,data):
        self.data = data
    
    def sqlalchemy_sqltype(self):
        __TYPE_TO_SQLTYPE_DICT = {
            'BIGINTEGER': BigInteger, #mysql預設長度20,postgresql沒長度(資料庫的最大值吧)
            'INTEGER': Integer, #mysql預設長度11,postgresql沒長度(資料庫的最大值吧)
            'SMALLINTEGER': SmallInteger, #mysql預設長度6,postgresql沒長度(資料庫的最大值吧)
            'MYSQL_INTEGER': mysql.INTEGER(display_width=self.set_datalength["int_length"]), #mysql預設長度11,postgresql沒長度(資料庫的最大值吧)
            # 'Float': sqlalchemy.Float,
            # 'Double': sqlalchemy.DOUBLE,
            'BOOLEAN': Boolean,
            'VARCHAR': VARCHAR(length=self.set_datalength["str_length"]),
            'NVARCHAR': NVARCHAR(length=self.set_datalength["str_length"]),
            'TIMESTAMP': TIMESTAMP(timezone=False),
            'DATETIME': DateTime(timezone=False),
            'JSON': JSON,
            # 'Date' : sqlalchemy.Date,
            'NUMERIC' : Numeric(precision=self.set_datalength["precision"],scale=self.set_datalength["scale"]),
            'DECIMAL' : DECIMAL(precision=self.set_datalength["precision"],scale=self.set_datalength["scale"])
        }
        return __TYPE_TO_SQLTYPE_DICT[self.data["type"].upper()]
        #How to create integer of a certain length with Sqlalchemy? -> use sqlalchemy.dialects.mysql.INTEGER(display_width)
        #https://stackoverflow.com/questions/36942506/how-to-create-integer-of-a-certain-length-with-sqlalchemy

    def catch_data_type_length(self):
        data_length_to_sqltypeDict = {
            "precision":18,
            "scale":5,
            "int_length":11,
            "str_length":512
        }
        self.set_datalength = data_length_to_sqltypeDict
        data_type = self.data["type"].upper()
        length = self.data["length"]

        if length != "":
            length = str(length).split(".")
            if len(length) == 1:
                if data_type in ("VARCHAR","NVARCHAR"):
                    self.set_datalength["str_length"] = int(length[0])
                elif data_type in ("INTEGER","BIGINTEGER","SMALLINTEGER","MYSQL_INTEGER"):
                    self.set_datalength["int_length"] = int(length[0])
            elif len(length) == 2:
                if data_type in ("NUMERIC","DECIMAL"):
                    if length[0] != "":
                        self.set_datalength["precision"] = int(length[0])
                    if length[1] != "":
                        self.set_datalength["scale"] = int(length[1])
                    
        return self.sqlalchemy_sqltype()
        #https://blog.csdn.net/Miracle_ps/article/details/105461239 python類中函數相互調用方法

    def get_primary_key(self):
        if self.data["primarykey"] in ("true","True","TRUE","true_autoinc"):
            return True
        else:
            return False

    def get_auto_increment(self):
        if self.data["type"].upper() in ("INTEGER","BIGINTEGER","SMALLINTEGER","MYSQL_INTEGER") and self.data["primarykey"] == "true_autoinc":
            return True
        else:
            return False

    def get_nullable(self):
        if self.data["nullable"] in ("true","True","TRUE"):
            return True
        else:
            return False

    def get_server_default(self):
        if self.data.get("default") is None:
            return None
        else:
            return self.data["default"]
#}}}


# class _WorkerThreadQueue(threading.Thread):
#     def __init__(self, queue, num, lock, get):
#         threading.Thread.__init__(self)
#         self.queue = queue
#         self.num = num
#         self.lock = lock
#         self.get = get
#         print "=====init===="
#         print self.get
#         print "============="

#     def run(self):
#         for i in range(self.get):
#             print "now queue size -> ",self.queue.qsize()
#             print "this worker -> ",self.num
#             if self.queue.qsize() > 0:
#                 msg = self.queue.get()

#                 # 取得 lock
#                 self.lock.acquire()
#                 print "Lock acquired by Worker %d" % self.num

#                 # # 不能讓多個執行緒同時進的工作
#                 # print "Worker %d: %s" % (self.num, msg)
#                 # time.sleep(1)

#                 self.lock.release()
#                 # 釋放 lock
#                 print "Lock released by Worker %d" % self.num

#=======================================================
# SqlValidator
# Date: 07212020 Yishan
# use module : sqlvalidator(not support python2.7)
#=======================================================
#{{{ class SqlValidator()
class SqlValidator():
    #Yishan 07212020 add for SQL queries semantic validation (Not support fot python2.7)
    #https://github.com/David-Wobrock/sqlvalidator
    # import sqlvalidator
    def __init__(self,sql):
        self.sql = sql
    
    def validation(self):
        sql_query = sqlvalidator.parse(self.sql)
        if not sql_query.is_valid():
            return False,sql_query.errors
        else:
            True,"validation successful"
#}}}

#=======================================================
# Api_Sqlsyntax_Action
# Date: 07142020 Yishan
# common use for api:sqlsyntax action
#=======================================================
#{{{ class Api_Sqlsyntax_Action()
class ApiSqlsyntaxActions():
    def __init__(self,data):
        self.data = data

    #---------------------------------------------------------
    # 整理組合sqlsyntax api的符號條件語法
    #---------------------------------------------------------
    #{{{
    def sqlalchemy_symbol_condition(self):
        self.query_config = {
            "and":and_,
            "or":or_
        }
        symbolDict = {
            "equal":self.__equal,
            "notequal":self.__notequal,
            "greater":self.__greater,
            "less":self.__less,

            "leftlike":self.__like,
            "notleftlike":self.__like,
            "leftlikein":self.__like,
            "leftlikenotin":self.__like,
            "like":self.__like,
            "notlike":self.__like,
            "likein":self.__like,
            "likenotin":self.__like,
            "rightlike":self.__like,
            "notrightlike":self.__like,
            "rightlikein":self.__like,
            "rightlikenotin":self.__like,
            
            "between":self.__between,
            "in":self.__in,
            "notin":self.__notin
        }
        return symbolDict[self.data["symbol"]]()

    def __equal(self):
        if self.data["value"] in ("null","Null","NULL"): return self.__is()
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) == self.data["value"])
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) == self.data["value"]))
    
    def __is(self):
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).is_(None))
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).is_(None)))

    def __notequal(self):
        if self.data["value"] in ("null","Null","NULL"): return self.__isnot()
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) != self.data["value"])
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) != self.data["value"]))
    
    def __isnot(self):
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).isnot(None))
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).isnot(None)))

    def __greater(self):
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) > self.data["value"])
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) > self.data["value"]))

    def __less(self):
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) < self.data["value"])
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]) < self.data["value"]))

    def __like(self):
        if self.data["symbol"] in ["like","notlike"]:
            thisvalue = "%{}%".format(self.data["value"])
        elif self.data["symbol"] in ["leftlike","notleftlike"]:
            thisvalue = "%{}".format(self.data["value"])
        elif self.data["symbol"] in ["rightlike","notrightlike"]:
            thisvalue = "{}%".format(self.data["value"])
        elif re.search(r'in',self.data["symbol"]):
            if re.search(r'left',self.data["symbol"]):
                thisvalue = ["%{}".format(i) for i in self.data["value"]]
            elif re.search(r'right',self.data["symbol"]):
                thisvalue = ["{}%".format(i) for i in self.data["value"]]
            else:
                thisvalue = ["%{}%".format(i) for i in self.data["value"]]

        if self.data["db"] == "mssql" and (self.data["schemaDict"][self.data["key"]] in ("TIMESTAMP","DATETIME")):
            if re.search(r'not',self.data["symbol"]):
                return self.__adjust_like_in_sql("mssqltime_not", thisvalue)
            return self.__adjust_like_in_sql("mssqltime", thisvalue)

        if self.data["db"] == "postgres" and (self.data["schemaDict"][self.data["key"]] in ("TIMESTAMP WITHOUT TIME ZONE","INTEGER")):
            if re.search(r'not',self.data["symbol"]):
                return self.__adjust_like_in_sql("postgrestime_not", thisvalue)
            return self.__adjust_like_in_sql("postgrestime", thisvalue)

        if re.search(r'not',self.data["symbol"]):
            return self.__adjust_like_in_sql("notlike", thisvalue)
        return self.__adjust_like_in_sql("like", thisvalue)
    
    def __between(self):
        if self.data["num"] == 0:
            return or_(between(getattr(self.data["query_table"].c,self.data["key"]),self.data["value"][0],self.data["value"][1]))
        return or_(self.data["wheresql"],or_(between(getattr(self.data["query_table"].c,self.data["key"]),self.data["value"][0],self.data["value"][1])))

    def __in(self):
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).in_(self.data["value"]))
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).in_(self.data["value"])))

    def __notin(self):
        if self.data["num"] == 0:
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).notin_(self.data["value"]))
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).notin_(self.data["value"])))
    #}}}

    def __adjust_like_in_sql(self, which, valuedata):
        type_config = {
            "mssqltime":"CONVERT(varchar(512),{},121) LIKE '{}'",
            "mssqltime_not":"CONVERT(varchar(512),{},121) NOT LIKE '{}'",
            "postgrestime":"{} ::text LIKE '{}'",
            "postgrestime_not":"{} ::text NOT LIKE '{}'"
        }
        if re.search(r'time',which):
            if isinstance(valuedata,list):
                multilikeaqlstr = or_(*[text(type_config[which].format(getattr(self.data["query_table"].c,self.data["key"]),value)) for value in valuedata])
                if self.data["wheresql"] != "":
                    return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](multilikeaqlstr))
                return self.query_config[self.data["query_operator"]](multilikeaqlstr)

            if self.data["num"] == 0:
                return self.query_config[self.data["query_operator"]](text(type_config[which].format(getattr(self.data["query_table"].c,self.data["key"]),valuedata)))
            return self.query_config[self.data["query_operator"]](text(self.data["wheresql"]),self.query_config[self.data["query_operator"]](text(type_config[which].format(getattr(self.data["query_table"].c,self.data["key"]),valuedata))))
        
        if isinstance(valuedata,list):
            multilikeaqlstr = ""
            if which == "like": 
                multilikeaqlstr = or_(*[getattr(self.data["query_table"].c,self.data["key"]).like(value) for value in valuedata])
            else:
                multilikeaqlstr = or_(*[getattr(self.data["query_table"].c,self.data["key"]).notlike(value) for value in valuedata])
            
            if self.data["wheresql"] != "":
                return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](multilikeaqlstr))
            return self.query_config[self.data["query_operator"]](multilikeaqlstr)

        if self.data["num"] == 0:
            if which == "like":
                return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).like("{}".format(valuedata)))
            return self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).notlike("{}".format(valuedata)))
        if which == "like":
            return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).like("{}".format(valuedata))))
        return self.query_config[self.data["query_operator"]](self.data["wheresql"],self.query_config[self.data["query_operator"]](getattr(self.data["query_table"].c,self.data["key"]).notlike("{}".format(valuedata))))

    #---------------------------------------------------------
    # 檢查request.data的參數是否存在且正確
    # 儲存成變數供接續動作使用
    #---------------------------------------------------------
    #{{{
    #Yishan 10072019 增加symbols，用於比較運算子，包含=(equal),!=(notequal),>(greater),<(less))
    def check_post_parameter(self):
        return self._ppexist()
    
    def _ppexist(self):
        if self.data["isjoin"]:
            this_parameter = globalvar.JOIN_SQLSYNTAX_PARAMETER
        else:
            this_parameter = globalvar.SQLSYNTAX_PARAMETER

        if not check_post_parameter_exist(self.data["request_data"],this_parameter):
            return False,"Missing post parameters : '{}'".format(this_parameter)
        
        #先將unicode data change to str
        self.data["request_data"] = AdjustDataFormat().format(self.data["request_data"])

        return self._pptype()

    def _pptype(self):
        datatype = {unicode:"String",list:"Array",dict:"Object"}
        if self.data["isjoin"]:
            this_parameter = globalvar.JOIN_SQLSYNTAX_PARAMETER
        else:
            this_parameter = globalvar.SQLSYNTAX_PARAMETER
        #if type error,return error and correct type,put in errpostdatatype
        errpostdatatype = []
        for key,value in this_parameter.items():
            #不為""
            if self.data["request_data"].get(key) != "":
                #檢查格式是否正確
                if not isinstance(self.data["request_data"].get(key),value):
                    err_msg = "Error type of '{}',it must be a {}".format(key,datatype[value])
                    errpostdatatype.append(err_msg)
        else:
            if len(errpostdatatype) != 0:
                return False,errpostdatatype
            else:
                return self._setvariable()
    
    def _setvariable(self):
        if not self.data["isjoin"]:
            result = {
                "table":self.data["request_data"].get("table").encode("utf8").strip(),
                "fields":self.data["request_data"].get("fields"),
                "where":self.data["request_data"].get("where"),
                "orderby":self.data["request_data"].get("orderby"),
                "limit":self.data["request_data"].get("limit"),
                "symbols":self.data["request_data"].get("symbols"),
                "intervaltime":self.data["request_data"].get("intervaltime"),
                "subquery":self.data["request_data"].get("subquery"),
                "union":self.data["request_data"].get("union")
            }
        else:
            result = {
                "tables":self.data["request_data"].get("tables"),
                "fields":self.data["request_data"].get("fields"),
                "where":self.data["request_data"].get("where"),
                "join":self.data["request_data"].get("join"),
                "jointype":self.data["request_data"].get("jointype"),
                "orderby":self.data["request_data"].get("orderby"),
                "limit":self.data["request_data"].get("limit"),
                "symbols":self.data["request_data"].get("symbols"),
                "subquery":self.data["request_data"].get("subquery")
            }
        
        return True,result
    #}}}
#}}}

#---------------------------------------------------------
# 整理判斷sqlsyntax where條件是否正確
#---------------------------------------------------------
#{{{_WhereSqlsyntaxActions()
class _WhereSqlsyntaxActions():
    def __init__(self,sess,metadata,key,value,which_condition,reqdataDict,subquery,fieldList,schemaDict,symbolstoStrDict,query_table,wheresqlList,db,isjoin,system):
        self.apicondition = False
        self.sess = sess
        self.metadata = metadata
        self.key = key
        self.value = value
        self.which_condition = which_condition
        self.reqdataDict = reqdataDict
        self.subquery = subquery
        self.fieldList = fieldList
        self.schemaDict = schemaDict
        self.symbolstoStrDict = symbolstoStrDict
        self.query_table = query_table
        self.wheresqlList = wheresqlList
        self.db = db
        self.isjoin = isjoin
        self.system = system

    def whereschema(self):
        try:
            #判斷where進來的key是否與資料表欄位相符
            if self.key not in self.fieldList:
                return False,"Unknown column '{}' in 'field list'".format(self.key)

            #判斷where進來的key是否為JSON欄位
            if self.schemaDict[self.key] == "JSON": 
                return False,"where condition does not support json field '{}'".format(self.key)

            if self.symbolstoStrDict.get(self.key) is None:
                return False,"The symbol key '{}' does not match {}" .format(self.symbolstoStrDict.keys(),self.key)

            #where value&symbol value皆為list，否則return
            if not ((isinstance(self.value,list) and isinstance(self.symbolstoStrDict[self.key],list))):
                return False,"error type of where '{}' or symbol '{}' input , it must be an Array".format(self.value,self.symbolstoStrDict[self.key])

            if len(self.symbolstoStrDict[self.key]) != len(self.value):
                return False,"The number of 'symbol data' : '{}' does not match 'where data' : '{}'" .format(self.symbolstoStrDict[self.key],self.value)

            return self.composewheresql()

        except Exception as e:
            return False,appPaaS.catch_exception(e,sys.exc_info(),self.system)
    
    def apiconditionschema(self,this):
        try:
            if self.value[this].split("_")[1] == "":
                return False,"error type of subquery condition , must be : subcondition_x"

            # if int(self.value[this].split("_")[1]) < self.condition_num:
            #     return False,"next condition number '{}' must be greater this condition number '{}'".format(int(self.value[this].split("_")[1]),self.condition_num)

            if not isinstance(self.subquery,dict):
                return False,"'request.data.subquery : {}' it must be an Object".format(self.subquery)
            
            if self.subquery.get(self.value[this]) is None:
                return False,"'request.data.subquery' missing key : '{}'".format(self.value[this])

            if not (isinstance(self.symbolstoStrDict[self.key][this],str) and (self.symbolstoStrDict[self.key][this].split("_")[0] in globalvar.SQLSYNTAX_SUBQUERY_OPERATOR)):
            # if not (isinstance(self.symbolstoStrDict[self.key][this],str) and (self.symbolstoStrDict[self.key][this].split("_")[0] in ["in","notin"])):
                # return False,"子查詢的symbol : '{}' 必須為字串且必須為以下其中一個 : {}".format(self.symbolstoStrDict[self.key][this].split("_")[0],["in","notin"])
                return False,"子查詢的symbol : '{}' 必須為字串且必須為以下其中一個 : {}".format(self.symbolstoStrDict[self.key][this].split("_")[0],globalvar.SQLSYNTAX_SUBQUERY_OPERATOR)

            action_status,action_result = ApiSqlsyntaxActions({"request_data":self.subquery[self.value[this]],"isjoin":self.isjoin}).check_post_parameter()
            if not action_status:
                return False,action_result
            
            subqueryfileds_msg = "子查詢回傳的欄位只能有一個"
            subqueryfileds_onlyone = True
            #子查詢回傳的欄位只能有一個，否則父查詢會有錯誤
            if isinstance(action_result["fields"],list):
                if len(action_result["fields"]) != 1:
                    subqueryfileds_onlyone = False
            elif isinstance(action_result["fields"],dict):
                if len(action_result["fields"].values()[0]) != 1:
                    subqueryfileds_onlyone = False
            elif isinstance(action_result["fields"],str) or isinstance(action_result["fields"],unicode):
                subqueryfileds_onlyone = False

            if not subqueryfileds_onlyone:
                return False,subqueryfileds_msg

            return True,action_result

        except Exception as e:
            return False,appPaaS.catch_exception(e,sys.exc_info(),self.system)

    def composewheresql(self):
        try:
            for c in range(len(self.value)):
                if isinstance(self.value[c],str):
                    self.apicondition = re.search(r'subcondition_',self.value[c])

                if self.apicondition:
                    status,result = self.apiconditionschema(c)
                    if not status:
                        return False,result
                    
                    if not self.isjoin:
                        this_sqlsyntax_actions_status,this_sqlsyntax_actions_result = sqlsyntax_params_actions(result,self.value[c],self.reqdataDict,self.sess,self.metadata,self.db,self.isjoin,self.system,is_subquery=True,is_union=False)
                        if not this_sqlsyntax_actions_status:
                            return False,this_sqlsyntax_actions_result
                    else:
                        this_sqlsyntax_actions_status,this_sqlsyntax_actions_result = join_sqlsyntax_params_actions(result,self.value[c],self.reqdataDict,self.sess,self.metadata,self.db,self.isjoin,self.system,is_subquery=True)
                        if not this_sqlsyntax_actions_status:
                            return False,this_sqlsyntax_actions_result
                    
                    thisvalue = this_sqlsyntax_actions_result
                    thissymbol = self.symbolstoStrDict[self.key][c].split("_")[0]
                    #所有運算子預設為or
                    query_operator = "or"
                    if len(self.symbolstoStrDict[self.key][c].split("_")) > 1:
                        query_operator = self.symbolstoStrDict[self.key][c].split("_")[1]
                else:
                    thisvalue = self.value[c]

                    #判斷where進來的key是否為時間欄位且不為null
                    if (not self.value[c] in ("null","Null","NULL")) and self.schemaDict[self.key] in ("TIMESTAMP","DATETIME","TIMESTAMP WITHOUT TIME ZONE"):
                        this_time_parameter = self.value[c]
                        if not isinstance(self.value[c],list):
                            this_time_parameter = [self.value[c]]
                        #判斷value list內皆為合法時間字串
                        for i in this_time_parameter:
                            if not VerifyDataStrLawyer(i).verify_date():
                                return False,"error 'where' parameter input, date str '{}' is illegal".format(i)

                    #檢查symbols是否合法
                    if self.symbolstoStrDict[self.key][c].split("_")[0] not in globalvar.SQLSYNTAX_OPERATOR:
                        return False,"error 'symbols' parameter input '{}', not in {}" .format(self.symbolstoStrDict[self.key][c],globalvar.SQLSYNTAX_OPERATOR)

                    #檢查symbols query_operator是否為and或or
                    if len(self.symbolstoStrDict[self.key][c].split("_")) > 1 and self.symbolstoStrDict[self.key][c].split("_")[1] not in ["and","or"]:
                        return False,"error 'symbols' parameter input '{}' -> operator '{}' not in ['and','or']" .format(self.symbolstoStrDict[self.key][c],self.symbolstoStrDict[self.key][c].split("_")[1])
                    
                    #檢查symbols中只要有in必須為陣列(in\notin\likein\likenotin\leftlikein\leftlikenotin\rightlikein\rightlikenotin)
                    if re.search(r'in',self.symbolstoStrDict[self.key][c].split("_")[0]):
                        if not isinstance(self.value[c],list):
                            return False,"error type of 'symbols' parameter input '{}', it must be an Array" .format(self.value[c])
                    else:
                        if (isinstance(self.value[c],list) or isinstance(self.value[c],dict)):
                            return False,"error type of 'symbols' parameter input '{}', it can't be an Array or Object" .format(self.value[c])
                    
                    # thissymbol = self.symbolstoStrDict[self.key][c]
                    thissymbol = self.symbolstoStrDict[self.key][c].split("_")[0]
                    #所有運算子預設為or
                    query_operator = "or"
                    if len(self.symbolstoStrDict[self.key][c].split("_")) > 1:
                        query_operator = self.symbolstoStrDict[self.key][c].split("_")[1]
                if c == 0:
                    whereor = ApiSqlsyntaxActions({"num":c,"query_table":self.query_table,"key":self.key,"symbol":thissymbol,"value":thisvalue,"wheresql":"","db":self.db,"schemaDict":self.schemaDict,"query_operator":query_operator}).sqlalchemy_symbol_condition()
                else:
                    whereor = ApiSqlsyntaxActions({"num":c,"query_table":self.query_table,"key":self.key,"symbol":thissymbol,"value":thisvalue,"wheresql":whereor,"db":self.db,"schemaDict":self.schemaDict,"query_operator":query_operator}).sqlalchemy_symbol_condition()
            else:
                if 'whereor' in locals().keys():
                    self.wheresqlList.append(whereor)
            return True,self.wheresqlList

        except Exception as e:
            return False,appPaaS.catch_exception(e,sys.exc_info(),self.system)
#}}}

#---------------------------------------------------------
# 整理組合sqlsyntax(field,where,order by,limit,intervaltime)並查詢
#---------------------------------------------------------
#{{{sqlsyntax_params_actions()
def sqlsyntax_params_actions(parameters,which_condition,reqdataDict,sess,metadata,db,isjoin,system,is_subquery=False,is_union=False):
    """
    一般多條件sql語法組合器

    Args:
        parameters: api parameters(table,fields,where,orderby,limit,symbols,intervaltime,subquery,union)
        which_condition: this condition number
        reqdataDict: api request data
        sess: database connect session
        metadata: database connect metadata
        db: which kind of database
        isjoin: 是否為join查詢
        system: 使用之系統名稱
        is_subquery: 是否為子查詢
        is_union: 是否為聯合查詢
    Returns:
        [0]: status(狀態，True/False)
        [1]: data(返回的資料，False: 錯誤訊息/True: sql語法或查詢結果)
    """
    table = parameters["table"]
    fields = parameters["fields"]
    where = parameters["where"]
    orderby = parameters["orderby"]
    limit = parameters["limit"]
    symbols = parameters["symbols"]
    intervaltime = parameters["intervaltime"]
    subquery = parameters["subquery"]
    union = parameters["union"]
    try:
        #check table existed or not
        if not retrieve_table_exist(metadata,table,system):
            return False,"Table '{}' doesn't exist".format(table)

        query_table = Table(table , metadata, autoload=True)

        #desc table schema
        desc_table_return = desc_table(metadata,table,system,selectDB=db)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        schemaDict = desc_table_return[3]
        if desc_table_status != 'ok':
            return False,desc_table_status

        recList = []
        #---------------------------------------------------------
        # field
        #---------------------------------------------------------
        #{{{
        if fields != "":
            if len(fields) == 0:
                return False,"error 'fields' parameter input, can't Null"

            #判斷fields是不是table的schema
            if len(fields) != len(list(set(fieldList).intersection(set(fields)))):
                fieldsnomatch = map(str,list(set(fields).difference(set(fieldList))))
                #如果difference()出來是空的，表示fields是符合schema但重複輸入，返回error
                if len(fieldsnomatch) != 0:
                    err_msg = "Unknown column \'{}\' in 'field list'".format(fieldsnomatch)
                else:
                    err_msg = "fields {} is duplicate".format(fields)

                return False,err_msg

            finalselect = [getattr(query_table.c,fields[i])for i in range(len(fields))]
        else:
            finalselect = [query_table]

        #}}}
        #---------------------------------------------------------
        # where
        #---------------------------------------------------------
        #{{{
        whereList = []
        wherecombineList = []
        if where != "":
            if len(where) == 0:
                return False,"error 'where' parameter input, can't Null"

            if symbols == "":
                return False,"error 'symbols' parameter input, can't Null"

            if len(symbols) != len(where):
                return False,"The number of {} data does not match {}" .format(symbols,where)

            #unicode dict change to str dict
            wheretoStrDict = ConvertData().convert(where)
            symbolstoStrDict = ConvertData().convert(symbols)
            for key,value in wheretoStrDict.items():
                if symbolstoStrDict.get(key) is None:
                    return False,"The symbol key '{}' does not match {}" .format(symbolstoStrDict.keys(),key)

                thisreqdataDict = deepcopy(reqdataDict)
                if subquery != "":
                    thisreqdataDict = thisreqdataDict[which_condition]["subquery"]

                if key != "combine":
                    notcombine_action = _WhereSqlsyntaxActions(sess,metadata,key,value,which_condition,thisreqdataDict,subquery,fieldList,schemaDict,symbolstoStrDict,query_table,whereList,db,isjoin,system)
                    status,whereList = notcombine_action.whereschema()
                    if not status:
                        return False,whereList
                else:
                    for i in range(len(value)):
                        whereorcombineList = []
                        for combine_key,combine_value in value[i].items():

                            combine_action = _WhereSqlsyntaxActions(sess,metadata,combine_key,combine_value,which_condition,thisreqdataDict,subquery,fieldList,schemaDict,symbolstoStrDict["combine"][i],query_table,whereorcombineList,db,isjoin,system)
                            status,whereorcombineList = combine_action.whereschema()
                            if not status:
                                return False,whereorcombineList

                        else:
                            wherecombine = and_(*(ii for ii in whereorcombineList))
                        wherecombineList.append(wherecombine)
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
                return False,"error 'orderby' parameter input, can't Null"

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
                return False,errpostorderbyparameter

            #以fieldList與orderby[1]，intersection()比較有無相同，且數量是否相等
            if len(orderbyAY) != len(list(set(fieldList).intersection(set(orderbyAY)))):
                #如果difference()出來是空的，表示orderby是符合schema但重複輸入，返回error
                orderbynomatch = map(str,list(set(orderbyAY).difference(set(fieldList))))
                if len(orderbynomatch) != 0:
                    err_msg = "orderby fields {} does not existed".format(orderbynomatch)
                else:
                    err_msg = "orderby fields {} is duplicate".format(orderby)
                return False,err_msg

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
        setlimitStart = 0
        if limit != "":
            #檢查post limit length是否為2
            if len(limit) == 2:
                #判斷limit[0],limit[1]皆為正整數
                try:
                    if db == "mssql":
                        if int(limit[0]) != 0 and finalorderby == "":
                            return False,"MSSQL requires an order_by when using an OFFSET or a non-simple LIMIT clause"

                    if int(limit[0]) >= 0 and int(limit[1]) >= 0:
                        # if db == "mssql":
                        #     setlimitStart = int(limit[0])
                        #     limitStart = 0
                        #     limitEnd = int(limit[0])+int(limit[1])
                        # else:
                        limitStart = int(limit[0])
                        limitEnd = int(limit[1])
                    else:
                        return False,"limit number {} is must be a Positive Integer".format(limit)

                except ValueError:
                    return False,"limit number {} is must be a Positive Integer".format(limit)

            else:
                if limit[0] != "ALL":
                    return False,"error length of limit number {}".format(limit)
                    
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
        wherentervaltimeList = []
        if intervaltime != "":
            intervaltimetoStrDict = intervaltime
            for timekey,timevalue in intervaltimetoStrDict.items():
                if not ((schemaDict[timekey] == "TIMESTAMP") or (schemaDict[timekey] == "DATETIME") or (schemaDict[timekey] == "TIMESTAMP WITHOUT TIME ZONE") or (schemaDict[timekey] == "DATE")):
                    return False,"error 'intervaltime' parameter input '{}' schema is not TIMESTAMP or DATETIME or DATE".format(timekey)
                
                if not isinstance(timevalue,list):
                    return False,"error 'intervaltime' parameter input, '{}' it must be an Array".format(timevalue)
                
                for c in range(len(timevalue)):
                    if not isinstance(timevalue[c],list):
                        return False,"error 'intervaltime' parameter input, '{}' it must be an Array".format(timevalue[c])

                    #判斷timevalue[c][0],timevalue[c][1]皆為合法時間字串
                    for timestr in timevalue[c]:
                        if not VerifyDataStrLawyer(timestr).verify_date():
                            return False,"error 'intervaltime' parameter input, date str '{}' is illegal".format(timestr)

                    #檢查post intervaltime childtime length是否為2
                    if len(timevalue[c]) != 2:
                        return False,"error 'intervaltime' parameter input '{}', must have a start time and an end time".format(timevalue[c])

                    if datetime.strptime(timevalue[c][1], "%Y-%m-%d %H:%M:%S") < datetime.strptime(timevalue[c][0], "%Y-%m-%d %H:%M:%S"):
                        return False,"error 'intervaltime' parameter input, start date str '{}' need smaller than end date str '{}'".format(timevalue[c][0],timevalue[c][1])
                    
                    if c == 0:
                        intervaltimeor = ApiSqlsyntaxActions({"num":c,"query_table":query_table,"key":timekey,"symbol":"between","value":timevalue[c],"wheresql":""}).sqlalchemy_symbol_condition()
                    else:
                        intervaltimeor = ApiSqlsyntaxActions({"num":c,"query_table":query_table,"key":timekey,"symbol":"between","value":timevalue[c],"wheresql":intervaltimeor}).sqlalchemy_symbol_condition()
                else:
                    wherentervaltimeList.append(intervaltimeor)
        #}}}
        #---------------------------------------------------------
        # union
        #---------------------------------------------------------
        #{{{
        union_sqlsyntax_actions_result = ""
        if union != "":
            if union[0].split("_")[1] == "":
                return False,"error type of union query condition , must be : condition_x"
            
            if int(union[0].split("_")[1]) < int(which_condition.split("_")[1]):
                return False,"next condition number '{}' must be greater this condition number '{}'".format(int(union[0].split("_")[1]),int(which_condition.split("_")[1]))
            
            if reqdataDict.get(union[0]) is None:
                return False,"'request.data' missing key : '{}'".format(union[0])

            union_action_status,union_action_result = ApiSqlsyntaxActions({"request_data":reqdataDict[union[0]],"isjoin":False}).check_post_parameter()
            if not union_action_status:
                return False,union_action_result

            union_sqlsyntax_actions_status,union_sqlsyntax_actions_result = sqlsyntax_params_actions(union_action_result,union[0],reqdataDict,sess,metadata,db,isjoin,system=system,is_subquery=is_subquery,is_union=True)
            if not union_sqlsyntax_actions_status:
                return False,union_sqlsyntax_actions_result
        #}}}
        #---------------------------------------------------------
        # sess.execute(sqlStr)
        #---------------------------------------------------------
        finalquerywhere = and_(or_(*(i for i in wherecombineList)),
                                and_(*(i for i in whereList)),
                                and_(*(i for i in wherentervaltimeList))\
                            )
        
        #postgresql json欄位不能使用distinct()，會有錯誤
        # sqlStr = select([finalselect]).distinct().\
        sqlStr = select(finalselect).\
                        select_from(query_table).\
                            where(finalquerywhere).\
                            order_by(*finalorderby).\
                            limit(limitEnd).offset(limitStart)
        # print "~~~~sqlStr compile~~~~"
        # print sqlStr.compile(compile_kwargs={"literal_binds": True})

        #若是子查詢，This version of MariaDB doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
        #Yishan@10292020 postgres＆mssql子查詢可以使用limit
        if is_subquery or is_union:
            if db == "mysql":
                sqlStr = select(finalselect).\
                            select_from(query_table).\
                                where(finalquerywhere).\
                                order_by(*finalorderby)
            # print "~~~~is_subquery or is_union sqlStr compile~~~~"
            # print sqlStr.compile(compile_kwargs={"literal_binds": True})
            if union_sqlsyntax_actions_result != "":
                sqlStr = sqlStr.union(union_sqlsyntax_actions_result)
                
            return True,sqlStr

        if union_sqlsyntax_actions_result != "":
            finalsql = sqlStr.union(union_sqlsyntax_actions_result)
        else:
            finalsql = sqlStr

        for row in sess.execute(finalsql):
            drow = AdjustDataFormat().format(dict(row.items()))
            recList.append(drow)

        return True,[recList[setlimitStart:],finalsql]

    except Exception as e:
        return False,appPaaS.catch_exception(e,sys.exc_info(),system)

    # except pymysql.Warning as e:
    #     print "========="
    #     print e
    #     error = traceback.format_exc()
    #     print "========="
    #     print error
    #     return False,sys.exc_info()
#}}}

#---------------------------------------------------------
# 整理組合join sqlsyntax(fields,where,join,jointype,limit,tables,symbols,orderby)並查詢
#---------------------------------------------------------
#{{{join_sqlsyntax_params_actions()
def join_sqlsyntax_params_actions(parameters,which_condition,reqdataDict,sess,metadata,db,isjoin,system,is_subquery=False):
    """
    join多條件sql語法組合器

    Args:
        parameters: api parameters(tables,fields,where,join,jointype,orderby,limit,symbols,subquery)
        which_condition: this condition number
        reqdataDict: api request data
        sess: database connect session
        metadata: database connect metadata
        db: which kind of database
        isjoin: 是否為join查詢
        system: 使用之系統名稱
        is_subquery: 是否為子查詢
    Returns:
        [0]: status(狀態，True/False)
        [1]: data(返回的資料，False: 錯誤訊息/True: sql語法或查詢結果)
    """
    tables = parameters["tables"]
    fields = parameters["fields"]
    where = parameters["where"]
    join = parameters["join"]
    jointype = parameters["jointype"]
    orderby = parameters["orderby"]
    limit = parameters["limit"]
    symbols = parameters["symbols"]
    subquery = parameters["subquery"]
    recList = []
    try:
        #---------------------------------------------------------
        # tables
        #---------------------------------------------------------
        #{{{
        #check table existed or not
        if db != "postgres":
            if tables == "":
                return False,"'tables' parameter can't be Null"

            if join != "" and len(tables) < 2:
                return False,"至少要有兩個table"

            for i in range(len(tables)):
                if not retrieve_table_exist(metadata,tables[i],system):
                    return False,"Table '{}' doesn't exist".format(tables[i])
        #}}}

        #---------------------------------------------------------
        # field
        #---------------------------------------------------------
        #{{{
        fieldcolumnList = []
        tempfieldcolumnList = []
        if fields != "":
            if len(fields) == 0:
                return False,"error 'fields' parameter input, can't Null"

            for fieldskey,fieldsvalue in fields.items():
                if not fieldskey in tables:
                    return False,"error 'fields key {}' parameter input".format(fieldskey)

                desc_table_return = desc_table(metadata,fieldskey,system,selectDB=db)
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]
                if desc_table_status != 'ok':
                    return False,desc_table_status

                fieldsvalueList = []
                if isinstance(fieldsvalue,list):
                    fieldsvalueList = fieldsvalue
                else:
                    if fieldsvalue != "":
                        return False,"Error type of '{}',it must be an Array".format(fieldsvalue)

                    fieldsvalueList = fieldList

                if len(fieldsvalueList) != len(list(set(fieldList).intersection(set(fieldsvalueList)))):
                    fieldsnomatch = map(str,list(set(fieldsvalueList).difference(set(fieldList))))
                    #如果difference()出來是空的，表示fields是符合schema但重複輸入，返回error
                    if len(fieldsnomatch) != 0:
                        err_msg = "Unknown column \'{}\' in 'field list'".format(fieldsnomatch)
                    else:
                        err_msg = "fields {} is duplicate".format(fieldsvalueList)
                    return False,err_msg

                for i in range(len(fieldsvalueList)):
                    tempfieldcolumnList.append(getattr(Table(fieldskey ,metadata, autoload=True).c,fieldsvalueList[i]).label(fieldskey+"$"+fieldsvalueList[i]))
                    fieldcolumnList.append("{}".format(getattr(Table(fieldskey ,metadata, autoload=True).c,fieldsvalueList[i])))
        else:
            for i in range(len(tables)):
                desc_table_return = desc_table(metadata,tables[i],system,selectDB=db)
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]

                if desc_table_status != 'ok':
                    return False,desc_table_status

                for j in range(len(fieldList)):
                    tempfieldcolumnList.append(getattr(Table(tables[i] ,metadata, autoload=True).c,fieldList[j]).label(tables[i]+"$"+fieldList[j]))
                    fieldcolumnList.append("{}".format(getattr(Table(tables[i] ,metadata, autoload=True).c,fieldList[j])))

        finalselect = tempfieldcolumnList
        #}}}
        #---------------------------------------------------------
        # where
        #---------------------------------------------------------
        #{{{
        whereList = []
        wherecombineList = []
        if where != "":
            if len(where) == 0:
                return False,"error 'where' parameter input, can't Null"

            if symbols == "":
                return False,"error 'symbols' parameter input, can't Null"

            if len(symbols) != len(where):
                return False,"The number of {} data does not match {}" .format(symbols,where)

            #unicode dict change to str dict
            wheretoStrDict = ConvertData().convert(where)
            symbolstoStrDict = ConvertData().convert(symbols)
            
            for wherekey,wherevalue in wheretoStrDict.items():
                if not isinstance(wherevalue,dict):
                    return False,"error 'where value : {}' parameter input , must be an Object".format(wherevalue)

                if not wherekey in tables:
                    return False,"error 'where key {}' parameter input".format(wherekey)
                
                if symbolstoStrDict.get(wherekey) is None:
                    return False,"The symbol key '{}' does not match {}" .format(symbolstoStrDict.keys(),wherekey)

                #desc table schema
                desc_table_return = desc_table(metadata,wherekey,system,selectDB=db)
                desc_table_status = desc_table_return[0]
                fieldList = desc_table_return[1]
                schemaDict = desc_table_return[3]

                if desc_table_status != 'ok':
                    return False,desc_table_status
                
                query_table = Table(wherekey , metadata, autoload=True)

                for wherevalue_key,wherevalue_value in wherevalue.items():
                    if symbolstoStrDict[wherekey].get(wherevalue_key) is None:
                        return False,"The symbol key '{}' does not match {}" .format(symbolstoStrDict[wherekey].keys(),wherevalue_key)
                    
                    if wherevalue_key != "combine":
                        notcombine_action = _WhereSqlsyntaxActions(sess,metadata,wherevalue_key,wherevalue_value,which_condition,reqdataDict,subquery,fieldList,schemaDict,symbolstoStrDict[wherekey],query_table,whereList,db,isjoin,system)
                        status,whereList = notcombine_action.whereschema()
                        if not status:
                            return False,whereList
                    else:
                        for i in range(len(wherevalue_value)):
                            whereorcombineList = []
                            for combine_key,combine_value in wherevalue_value[i].items():
                                combine_action = _WhereSqlsyntaxActions(sess,metadata,combine_key,combine_value,which_condition,reqdataDict,subquery,fieldList,schemaDict,symbolstoStrDict[wherekey]["combine"][i],query_table,whereorcombineList,db,isjoin,system)
                                status,whereorcombineList = combine_action.whereschema()
                                if not status:
                                    return False,whereorcombineList

                            else:
                                wherecombine = and_(*(ii for ii in whereorcombineList))
                            wherecombineList.append(wherecombine)
        else:
            finalquerywhere = ""
        #}}}
        #---------------------------------------------------------
        # jointype
        #---------------------------------------------------------
        #{{{
        #Yishan@05082020 sql join types
        jointypeDict = {"inner":False,"left":True}
        #}}}
        #---------------------------------------------------------
        # join
        #---------------------------------------------------------
        #{{{
        joinkeyList = []
        joincolumnList = []
        # if condition_num == 1 and join == "":
        #     return False,"'join' parameter can't be Null"

        if join != "":
            join = ConvertData().convert(join)
            joinkeyList0 = join.keys()[0]
            if not isinstance(join[join.keys()[0]],list):
                #一定要用陣列包
                return False,"Error type of '{}',it must be an Array".format(join[join.keys()[0]])

            for i in join[join.keys()[0]]:
                response, msg, key, value = adjust_dict_for_joinapi(metadata=metadata,tables=tables,masterKey=joinkeyList0,data=i,joinkeyList=joinkeyList,joincolumnList=joincolumnList,system=system)
                if not response:
                    return False,msg
            else:
                joinkeyList = key
                joincolumnList = value


            wherejoinSql = Table(joinkeyList0 ,metadata, autoload=True)
            setjump = 0
            for i in range(len(joinkeyList)):
                if not isinstance(joinkeyList[i],list):
                    if jointype.get("{}_{}".format(joinkeyList0,joinkeyList[i])) is None:
                        return False,"missing the jointype key '{}_{}'" .format(joinkeyList0,joinkeyList[i])

                    isouter = jointypeDict[jointype["{}_{}".format(joinkeyList0,joinkeyList[i])]]
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
                    if jointype.get("{}_{}".format(joinkeyList[i][0],joinkeyList[i][1])) is None:
                        return False,"missing the jointype key '{}_{}'" .format(joinkeyList[i][0],joinkeyList[i][1])

                    isouter = jointypeDict[jointype["{}_{}".format(joinkeyList[i][0],joinkeyList[i][1])]]
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
            else:
                finalwherejoinSql = wherejoinSql
        else:
            #若沒有使用join，抓tables的第一個value當select_from
            finalwherejoinSql = Table(tables[0] ,metadata, autoload=True)
        #}}}
        #---------------------------------------------------------
        # order by
        #---------------------------------------------------------
        #{{{
        orderbytableList = []
        orderbycolumnList = []
        orderbyTCdist = {}
        orderbyAY = []
        orderbyDA = ""
        checkorderbycolumnduplicate = []
        if orderby != "":
            if len(orderby) == 0:
                dicRet["Response"] = err_msg
                return False,"error 'orderby' parameter input, can't Null"

            if str(orderby[0]) != "asc" and str(orderby[0]) != "desc":
                return False,"error 'orderby' parameter input \'{}\',must be asc or desc".format(orderby[0])

            #先判斷orderby list是否為奇數陣列，但長度不為１
            if not (len(orderby) % 2 == 1 and len(orderby) != 1):
                return False,"error 'orderby' parameter input {}, must be an odd array and miss table & column ex:['asc','table','column']".format(orderby)

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
                        return False,"Unknown column \'{}\' in 'field list'".format(orderbyTC)

                    #檢查table name是否存在
                    if orderby[i] not in tables:
                        return False,"table \'{}\' doesn't existed".format(orderby[i])
                        
                    orderbytableList.append(orderby[i])
                else:
                    desc_table_return = desc_table(metadata,orderby[i-1],system)
                    desc_table_status = desc_table_return[0]
                    fieldList = desc_table_return[1]
                    keyList = desc_table_return[2]

                    if desc_table_status != 'ok':
                        return False,desc_table_status

                    if orderby[i] not in fieldList:
                        return False,"Unknown column \'{}\' in 'field list'".format(orderby[i])

                    orderbycolumnList.append(orderby[i])

            for key,value in orderbyTCdist.items():
                checkduplicatecolumndict = dict(Counter(value))
                checkorderbycolumnduplicate = [key for key2,value2 in checkduplicatecolumndict.items()if value2 > 1]

            if len(checkorderbycolumnduplicate) != 0:
                return False,"orderby fields {} is duplicate".format(orderbycolumnList)

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
        setlimitStart = 0
        if limit != "":
            #檢查post limit length是否為2
            if len(limit) == 2:
                #判斷limit[0],limit[1]皆為正整數
                try:
                    if db == "mssql":
                        if int(limit[0]) != 0 and finalorderby == "":
                            return False,"MSSQL requires an order_by when using an OFFSET or a non-simple LIMIT clause"

                    if int(limit[0]) >= 0 and int(limit[1]) >= 0:
                        # if db == "mssql":
                        #     setlimitStart = int(limit[0])
                        #     limitStart = 0
                        #     limitEnd = int(limit[0])+int(limit[1])
                        # else:
                        limitStart = int(limit[0])
                        limitEnd = int(limit[1])
                    else:
                        return False,"limit number {} is must be a Positive Integer".format(limit)

                except ValueError:
                    return False,"limit number {} is must be a Positive Integer".format(limit)

            else:
                return False,"error length of limit number {}".format(limit)
        else:
            limitStart = 0
            #若無限制預設查100筆
            limitEnd = 100
        #}}}
        #---------------------------------------------------------
        # sess.execute(sqlStr)
        #---------------------------------------------------------        
        finalquerywhere = and_(or_(*(i for i in wherecombineList)),
                                and_(*(i for i in whereList))\
                            )
        
        sqlStr = select(finalselect).\
                    select_from(finalwherejoinSql).\
                        where(finalquerywhere).\
                        order_by(*finalorderby).\
                        limit(limitEnd).offset(limitStart)
        # print "~~~~sqlStr compile~~~~"
        # print sqlStr.compile(compile_kwargs={"literal_binds": True})

        #若是子查詢，This version of MariaDB doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
        #Yishan@10292020 postgres＆mssql子查詢可以使用limit
        if is_subquery:
            if db == "mysql":
                sqlStr = select(finalselect).\
                        select_from(finalwherejoinSql).\
                            where(finalquerywhere).\
                            order_by(*finalorderby)
            # print "~~~~subquery sqlStr compile~~~~"
            # print sqlStr.compile(compile_kwargs={"literal_binds": True})
            return True,sqlStr
        
        for row in sess.execute(sqlStr):
            drow = AdjustDataFormat().format(dict(row.items()))
            recList.append(drow)

        return True,[recList[setlimitStart:],sqlStr]

    except Exception as e:
        return False,appPaaS.catch_exception(e,sys.exc_info(),system)

    # except pymysql.Warning as e:
    #     print e
    #     error = traceback.format_exc()
    #     print error
    #     return False,sys.exc_info()
#}}}

#=======================================================
# Definition: 計時修飾器
# Date: 06172020@Yishan
#=======================================================
#{{{
def timeit(func):
    def wrapper(*args,**kwargs):
        print "==========================="
        print "Now use function '{}'".format(func.__name__)
        start = time.clock()
        print "start time: {}".format(start)
        print "*args: {}".format(args)
        print "**kwargs: {}".format(kwargs)
        result = func(*args,**kwargs)
        end = time.clock()
        print "end time: {}".format(end)
        print "used time: {:.10f}".format(end-start)
        print "==========================="
        return result
    return wrapper

@timeit
def check_uri_parameter_exist_(request,uri_parameter):
    print "*****************"
    for i in uri_parameter:
        if not request.args.get(i):
            return False,"Missing uri parameters : '{}'".format(i)
        if i == "uid":
            if request.args.get(i) not in globalvar.XXXUSER[globalvar.SERVERIP]:
                return False,"user:None has no privillege to query morder list"
    print "*****************"
    return True,"ok"
#}}}

#=======================================================
# Definition: 測試利用裝飾器包裝- 檢查api uri parameter 是否有傳入
# Date: 11112020@Yishan
#=======================================================
#{{{def DecoratorCheckUriParameterExist(sqlfilename,quarter,setquery)
class DecoratorCheckUriParameterExist(object):
    def __init__(self, request,uri_parameter):
        self.request = request
        self.uri_parameter = uri_parameter

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print '~~~~wrapper~~~~'
            for i in self.uri_parameter:
                if not self.request.args.get(i):
                    return jsonify( **{"Response":"Missing uri parameters : '{}'".format(i)})                                                                                                                                          
            return func(*args, **kwargs)
        return wrapper
#}}}

#=======================================================
# Definition: 裝飾器- 每個request前先連結資料庫to do oauth2
# Date: 11242020@Yishan
#=======================================================
#{{{def DecoratorOauth2ConnectDB()
class DecoratorOauth2ConnectDB(object):
    def __init__(self, need_to_require_oauth=True):
        self.need_to_require_oauth = need_to_require_oauth

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import oauth2.oauth2
            import redis
            print func.__name__
            try:
                DbSession,metadata,engine= appPaaS.getDbSessionType(system="PaaS",echo=True)
                if DbSession is None:
                    return jsonify( **{"Response":engine})

                sess = DbSession()
                print sess

                POOL = redis.ConnectionPool(host="127.0.0.1",port="6379",db=15,password="sapido")
                dbRedis = redis.Redis(connection_pool=POOL)

                authorization = oauth2.oauth2.config_oauth(sess,dbRedis)
                if not self.need_to_require_oauth:
                    return func(authorization,*args, **kwargs)
                return func(*args, **kwargs)
                
            finally:
                if 'DbSession' in locals().keys() and DbSession is not None:
                    sess.close()
                    DbSession.remove()
                    engine.dispose()
        return wrapper
#}}}

#=======================================================
# Definition: 測試資料庫是否成功連上
# Date: 01072021@Yishan
#=======================================================
#{{{def check_dbconnect_success(DbSession,metadata,engine)
def check_dbconnect_success(sess, system, doLoggerHandler=True):
    """
    測試資料庫是否成功連上(若連上且查詢成功代表資料庫存在)

    Args:
        sess: database connect session
        system: 使用之系統名稱
    Returns:
        [0]: status(狀態，True/False)
        [1]: err_msg(返回訊息)
    """
    status = False
    err_msg = "ok"
    try:
        for _ in sess.execute("select 1 as is_alive"):
            status = True
        if not status: raise Exception
    except Exception as e:
        err_msg = appPaaS.catch_exception(e, sys.exc_info(), system, doLoggerHandler=doLoggerHandler)
    finally:
        sess.close()
        return status,err_msg

#=======================================================
# Definition: 檢查api uri parameter 是否有傳入
# Date: 05082020@Yishan
#=======================================================
#{{{def check_uri_parameter_exist(sqlfilename,quarter,setquery)
def check_uri_parameter_exist(request,uri_parameter):
    """
    檢查api uri parameter 是否有傳入

    Args:
        request: api request data
        uri_parameter: list of api uri required parameter
    Returns:
        [0]: status(狀態，True/False)
        [1]: message(返回訊息)
    """
    for i in uri_parameter:
        if not request.args.get(i):
            return False,"Missing uri parameters or is Null : '{}'".format(i)
        if i == "uid":
            if request.args.get(i) not in globalvar.XXXUSER[globalvar.SERVERIP]:
                return False,"user:{} has no privillege to query morder list".format(request.args.get(i))
    return True,"ok"
#}}}

#=======================================================
# Definition: 檢查api post parameter 是否有傳入
# Date: 05082020@Yishan
#=======================================================
#{{{def check_post_parameter_exist(sqlfilename,quarter,setquery)
def check_post_parameter_exist(reqdataDict,post_parameter):
    """
    檢查api post parameter 是否有傳入

    Args:
        reqdataDict: api request data
        post_parameter: list of api post data required parameter
    Returns:
        status(狀態，True/False)
    """
    for i in post_parameter:
        if reqdataDict.get(i) is None:
            return False
    return True
#}}}

#=======================================================
# Definition: 檢查api post parameter 是否有傳入&格式是否正確
# Date: 05052021@Yishan
#=======================================================
#{{{def check_uri_parameter_format(sqlfilename,quarter,setquery)
def check_post_parameter_exist_format(reqdataDict,post_parameter):
    """  
    檢查api post parameter 是否有傳入&格式是否正確

    Args:
        reqdataDict: api request data
        post_parameter: list of api post data required parameter
    Returns:
        status(狀態，True/False)
    """
    for key,value in post_parameter.items():
        if reqdataDict.get(key) is None:
            return False
        legitimate = False
        for i in value:
            if isinstance(reqdataDict.get(key),i):
                legitimate = True 
        else:
            if not legitimate: return False
    return True 
#}}}

#=======================================================
# Definition: 檢查資料庫是否存在
# Date: 06092020@Yishan
#=======================================================
# {{{ def retrieve_database_exist(dbName)
def retrieve_database_exist(system, dbName="", forRawData="mysql", _appPaaS=None):
    """
    檢查資料庫是否存在

    Args:
        system: 使用之系統名稱
        dbName: 資料庫名稱
        forRawData: which kind of database
    Returns:
        [0]: status(存在與否，True/False)
        [1]: err_msg(返回訊息)
    """
    existed = True
    err_msg = "ok"
    if dbName == "":
        thisDB = globalvar.DBCONFIG[forRawData.upper()]
        dbName = dicConfig.get(thisDB+"Dbname_"+system)
        # if forRawData == "mysql":
        #     dbName = appPaaS.dicConfig.get("dbiMgmDbEntity_SAPIDOSYSTEM")
        # elif forRawData == "mssql":
        #     dbName = appPaaS.dicConfig.get("dbiMssqlDbEntity_SAPIDOSYSTEM")
    if _appPaaS is None:_appPaaS = appPaaS
    try:
        DbSession,metadata,engine = _appPaaS.getDbSessionType(dbName=dbName, forRawData=forRawData, system=system)
        if DbSession is None:
            existed = False
            err_msg = engine
    except Exception as e:
        err_msg = _appPaaS.catch_exception(e,sys.exc_info(),system)
        existed = False
    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()

        return existed,err_msg
# }}}

#=======================================================
# Definition: to check table existed or not
# Date: 09052019@Yishan
#=======================================================
#{{{def retrieve_table_exist(metadata,tableName,system,doLoggerHandler=True)
def retrieve_table_exist(metadata,tableName,system,doLoggerHandler=True):
    tableexisted = False
    try:
        #Yishan@12262019 add param only for反射指定表
        metadata.reflect(only=[tableName],views=True) #Yishan@10202020 views : If True, also reflect views.
        tableList = ConvertData().convert(metadata.tables.keys())
        if tableName in tableList: tableexisted = True
    except Exception as e:
        appPaaS.catch_exception(e,sys.exc_info(),system,doLoggerHandler=doLoggerHandler)
    finally:
        return tableexisted
#}}}

#=======================================================
# Definition: to desc mysql table
# Date: 09052019@Yishan
#=======================================================
#{{{def desc_table(metadata,tableName,system,havetime=True,selectDB="mysql")
def desc_table(metadata,tableName,system,havetime=True,selectDB="mysql"):
    fieldList = []
    keyList = []
    schemaDict = {}
    defaultDict = {}
    nullableDict = {}
    prikeyisTime = False
    try:
        #Yishan@12262019 add param only for反射指定表
        metadata.reflect(only=[tableName],views=True) #Yishan@10202020 views : If True, also reflect views.)
        for table in metadata.tables.values():
            if table.name == tableName:
                for column in table.c:
                    if column.server_default:
                        defaultDict[column.name] = True
                    else:
                        defaultDict[column.name] = False

                    if column.nullable:
                        nullableDict[column.name] = True
                    else:
                        nullableDict[column.name] = False

                    if havetime:
                        fieldList.append(column.name)
                    else:
                        if column.name != globalvar.CREATETIME[globalvar.SERVERIP][selectDB] and column.name != globalvar.UPLOADTIME[globalvar.SERVERIP][selectDB]:
                            fieldList.append(column.name)

                    if column.primary_key == True:
                        keyList.append(column.name)

                    if check_user_defined_type(column):
                        if selectDB != "postgres":
                            thistype = str(column.type).split(" COLLATE ")[0]
                            if selectDB == "mysql":
                                #判斷欄位是否為json，MYSQL裡的json型態為LONGTEXT.....
                                if re.search(r'LONGTEXT.',thistype):
                                    thistype = "JSON"
                            elif selectDB == "mssql":
                                #判斷欄位是否為json，MSSQL裡的json型態為NVARCHAR(max)，查出來會只有NVARCHAR，所以若為NVARCHAR就是json
                                if thistype == "NVARCHAR":
                                    thistype = "JSON"
                        else:
                            thistype = str(column.type)
                            if (column.primary_key) and (str(column.type) == "TIMESTAMP WITHOUT TIME ZONE"):
                                prikeyisTime = True
                    else:
                        thistype = "UserDefinedType"
                        
                    schemaDict[column.name] = thistype
        err_msg = "ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),system)

    finally:
        return [err_msg,fieldList,keyList,schemaDict,defaultDict,prikeyisTime,nullableDict]
#}}}

#=======================================================
# Definition: get column type加上try execpt避免遇到UserDefinedType會出錯程式無法進行
# Date: 01222020@Yishan
#=======================================================
#{{{ def check_user_defined_type(column):
def check_user_defined_type(column):
    try:
        thistype = column.type
        return True
    except Exception as e:
        return False
#}}}

#=======================================================
# Definition: adjust_dict_for_joinapi(join table api dict->需要的array格式)
# Date: 05082020@Yishan
#=======================================================
#{{{def adjust_dict_for_joinapi(metadata,tables,data,joinkeyList,joincolumnList,system,Flag=True,fatherkey="",masterKey="",selectDB="mysql")
def adjust_dict_for_joinapi(metadata,tables,data,joinkeyList,joincolumnList,system,Flag=True,fatherkey="",masterKey="",selectDB="mysql"):
    if isinstance(data,str):
        return True,"ok",joinkeyList,joincolumnList
    else:
        for key,value in data.items():
            tempList = []
            tempList2 = []
            if key not in tables:
                err_msg = "table '{}' doesn't existed".format(key)
                return False,err_msg,joinkeyList,joincolumnList

            if Flag:
                joinkeyList.append(key)
            else:
                if fatherkey != "":
                    tempList2.extend([fatherkey,key])
                else:
                    tempList2.append(key)
                joinkeyList.append(tempList2)
                tempList2 = []

            if isinstance(value,str):
                result,msg = _check_field_exist(metadata,selectDB,system,[key],[value])
                if not result:
                    err_msg = msg
                    return False,err_msg,joinkeyList,joincolumnList

                joincolumnList.append(value)
                return adjust_dict_for_joinapi(metadata=metadata,tables=tables,data=value,joinkeyList=joinkeyList,joincolumnList=joincolumnList,system=system)
            else:
                if len(value.keys()) == 1:
                    if masterKey != "":
                        result,msg = _check_field_exist(metadata,selectDB,system,[masterKey,key],[value.keys()[0],value.values()[0]])
                    else:
                        if fatherkey != "":
                            result,msg = _check_field_exist(metadata,selectDB,system,[fatherkey,key],[value.keys()[0],value.values()[0]])
                    if not result:
                        err_msg = msg
                        return False,err_msg,joinkeyList,joincolumnList
                        
                    joincolumnList.extend([value.keys()[0],value.values()[0]])
                else:
                    for key2,value2 in value.items():
                        if key2 != "JOIN":
                            if isinstance(value2,str):
                                if masterKey != "":
                                    result,msg = _check_field_exist(metadata,selectDB,system,[masterKey,key],[key2,value2])
                                else:
                                    if fatherkey != "":
                                        result,msg = _check_field_exist(metadata,selectDB,system,[fatherkey,key],[key2,value2])
                                if not result:
                                    err_msg = msg
                                    return False,err_msg,joinkeyList,joincolumnList

                                tempList.extend([key2,value2])
                    else:
                        if tempList:
                            joincolumnList.append(tempList)
                            tempList = []
                        if 'JOIN' in value:
                            return adjust_dict_for_joinapi(metadata=metadata,tables=tables,data=value["JOIN"],joinkeyList=joinkeyList,joincolumnList=joincolumnList,Flag=False,fatherkey=key,system=system)
        else:
            return adjust_dict_for_joinapi(metadata=metadata,tables=tables,data="",joinkeyList=joinkeyList,joincolumnList=joincolumnList,system=system)
#}}}

#=======================================================
# Definition: 檢查資料表欄位是否正確(存在) (for join table api)
# Date: 05082020@Yishan
#=======================================================
#{{{def _check_field_exist(sqlfilename,quarter,setquery)
def _check_field_exist(metadata,selectDB,system,table,column):
    for i in range(len(table)):
        desc_table_return = desc_table(metadata,table[i],system,selectDB=selectDB)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        schemaDict = desc_table_return[3]
        if desc_table_status != 'ok':
            err_msg = desc_table_status
            return False,err_msg

        if column[i] not in fieldList:
            err_msg = "Unknown column '{}' in table -> {} ".format(column[i],table[i])
            return False,err_msg
        
        if schemaDict[column[i]] == "JSON":
            err_msg = "join condition does not support json field => table : '{}' field : '{}'".format(table[i],column[i])
            return False,err_msg
    
    return True,"ok"
#}}}

#=======================================================
# Definition: 建立database
# Date: 06092020@Yishan
#=======================================================
# {{{ def create_database(dbName)
def create_database(system, dbName, forRawData="postgres", _appPaaS=None):
    status = True
    if forRawData != "postgres":
        return "Only PostgreSQL DataBase can create new database"

    # retrieve_status,retrieve_result = retrieve_database_exist(system, dbName=dbName, forRawData=forRawData)
    # if retrieve_status:
    #     return retrieve_result
    if _appPaaS is None:_appPaaS = appPaaS
    try:
        if forRawData == "postgres":
            default_dbName = "postgres"
        else:
            default_dbName = dbName
        
        DbSession,_,engine = _appPaaS.getDbSessionType(dbName=default_dbName,forRawData=forRawData,system=system)
        print "~~~~~~~~~~"
        print DbSession
        print engine
        if DbSession is None:
            #表示連接資料庫有問題
            return False,engine

        engcon = engine.connect()

        if forRawData == "postgres":
            dbName = dbName.lower()

        engcon.execute('commit')
        engcon.execute('create database {}'.format(dbName))
        engcon.execute('commit')
        err_msg="ok"
    
    except Exception as e:
        print "======e======"
        print e
        strExcInfo = str(sys.exc_info()[1][0])
        if "exists" in strExcInfo and dbName in strExcInfo:
            err_msg = "ok"
        else:
            err_msg = _appPaaS.catch_exception(e,sys.exc_info(),system)
            status = False
    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            engcon.close()
            DbSession.remove()
            engine.dispose()

    print "~~~~~~~create_database~~~~~~~"
    print status
    print err_msg
    return status,err_msg
# }}}

#=======================================================
# Definition: 
# 1. To check if dbName is existed
# 2. create a raw data table within dbName
#=======================================================
# {{{ def create_table
def create_table(table_name, attrList, table_comment, system, dbName="", forRawData="postgres",doLoggerHandler=True):
    # retrieve_status,retrieve_result = retrieve_database_exist(system, dbName=dbName, forRawData=forRawData)
    # if not retrieve_status:
    #     return False, retrieve_result
    
    try:
        err_msg = "error"
        DbSession,metadata,engine = appPaaS.getDbSessionType(dbName=dbName,forRawData=forRawData,echo=True,system=system)
        if DbSession is None:
            #表示連接資料庫有問題
            return False,engine

        sess = DbSession()

        if forRawData == "postgres":
            attrList = sorted(attrList, key=lambda k: k['primarykey'],reverse=True)
            TIMESTAMP_TABLE_SPEC = {"name":globalvar.UPLOADTIME[globalvar.SERVERIP][forRawData],"type":"TIMESTAMP","length":"","default":func.current_timestamp(6),"primarykey":"true","nullable":"","comment":"上傳時間"}
            #將時間欄位放在第一
            attrList.insert(0,TIMESTAMP_TABLE_SPEC)

        elif forRawData == "mysql":
            attrList = sorted(attrList, key=lambda k: k['primarykey'],reverse=True)
            TIMESTAMP_TABLE_SPEC = [
                {"name":globalvar.CREATETIME[globalvar.SERVERIP][forRawData],"type":"TIMESTAMP","length":"","default":func.current_timestamp(),"primarykey":"","nullable":"","comment":"建立時間"},
                {"name":globalvar.UPLOADTIME[globalvar.SERVERIP][forRawData],"type":"TIMESTAMP","length":"","default":text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),"primarykey":"","nullable":"","comment":"修改時間"}
            ]
            #將時間欄位放在最後
            attrList.extend(TIMESTAMP_TABLE_SPEC)
        else:
            attrList = sorted(attrList, key=lambda k: k['primarykey'],reverse=True)
            TIMESTAMP_TABLE_SPEC = [
                {"name":globalvar.CREATETIME[globalvar.SERVERIP][forRawData],"type":"DateTime","length":"","default":func.now(),"primarykey":"","nullable":"","comment":"建立時間"},
                {"name":globalvar.UPLOADTIME[globalvar.SERVERIP][forRawData],"type":"DateTime","length":"","default":func.now(),"primarykey":"","nullable":"","comment":"修改時間"}
            ]
            #將時間欄位放在最後
            attrList.extend(TIMESTAMP_TABLE_SPEC)
            #https://stackoverflow.com/questions/13370317/sqlalchemy-default-datetime

        create_table = Table(table_name, metadata,
                    PrimaryKeyConstraint(mssql_clustered=True),
                    comment = table_comment,
                    # Column("seq", BigInteger, primary_key=True),
                    *((Column(attrList[i]['name'], _TypeToSqlType(attrList[i]).catch_data_type_length(),\
                        primary_key = _TypeToSqlType(attrList[i]).get_primary_key(),\
                        autoincrement = _TypeToSqlType(attrList[i]).get_auto_increment(),\
                        server_default = _TypeToSqlType(attrList[i]).get_server_default(),\
                        nullable = _TypeToSqlType(attrList[i]).get_nullable(),\
                        comment = attrList[i]["comment"])) \
                    for i in range(len(attrList))\
                    )\
                )
        #https://stackoverflow.com/questions/6992321/how-to-set-default-on-update-current-timestamp-in-mysql-with-sqlalchemy
        create_table.create()
        metadata.create_all()
        if forRawData == "mssql":
            #建資料表與欄位描述
            #https://blog.csdn.net/StupidBird003/article/details/64562683
            #https://social.technet.microsoft.com/Forums/zh-TW/23fe9d4f-2d03-4253-8cdb-64100e229252/3553121839229142030929992sql35486278612231224314314353603926009?forum=sqlservermanagementzhcht
            mssql_table_comment_sqlstr = "sp_addextendedproperty 'MS_Description','{}','SCHEMA','dbo','TABLE','{}',null,null".format(table_comment,table_name)
            sess.execute(mssql_table_comment_sqlstr)
            for i in range(len(attrList)):
                mssql_column_comment_sqlstr = "sp_addextendedproperty 'MS_Description','{}','SCHEMA','dbo','TABLE','{}','COLUMN','{}';".format(attrList[i]["comment"],table_name,attrList[i]["name"])
                sess.execute(mssql_column_comment_sqlstr)
            sess.commit()
        err_msg = "ok"
    
    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),system,doLoggerHandler=doLoggerHandler)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            sess.close()
            DbSession.remove()
            engine.dispose()

            if err_msg == "ok":
                return True, "ok"
            else:
                return False,err_msg
# }}}

#=======================================================
# Definition:
# 1. To check if dbName is existed
# 2. delete a dbName
#=======================================================
# {{{ def delete_database
def delete_database(dbName,system,forRawData="postgres"):
    for i in dbName:
        retrieve_status,retrieve_result = retrieve_database_exist(system, dbName=i, forRawData=forRawData)
        if not retrieve_status:
            return retrieve_result

    try:
        DbSessionRaw,metadata,engineRaw = appPaaS.getDbSessionType(dbName="postgres",forRawData=forRawData,system=system)
        if DbSessionRaw is None:
            #表示連接資料庫有問題
            return engineRaw

        engcon = engineRaw.connect()

        for i in dbName:
            engcon.execute('commit')
            engcon.execute('drop database if exists {}'.format(i))
            engcon.execute('commit')
            err_msg="ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),system)

    finally:
        if DbSessionRaw is not None:
            engcon.close()
            DbSessionRaw.remove()
            engineRaw.dispose()

    return err_msg
# }}}

#=======================================================
# Definition:
# 1. To check if dbName is existed
# 2. delete a raw data table within dbName
#=======================================================
# {{{ def delete_tables
def delete_tables(tbName, dbName, system, forRawData="postgres"):
    err_msg = "error"
    # retrieve_status,retrieve_result = retrieve_database_exist(system, dbName=dbName, forRawData=forRawData)
    # if not retrieve_status:
    #     return retrieve_result

    try:
        DbSession,metadata,engine = appPaaS.getDbSessionType(dbName=dbName,forRawData=forRawData,system=system)
        if DbSession is None:
            #表示連接資料庫有問題
            return engine

        for i in tbName:
            del_table = Table(i , metadata, autoload=True)
            del_table.drop()
            err_msg="ok"

    except Exception as e:
        err_msg = appPaaS.catch_exception(e,sys.exc_info(),system)

    finally:
        if 'DbSession' in locals().keys() and DbSession is not None:
            DbSession.remove()
            engine.dispose()

    return err_msg
# }}}

#=======================================================
# Definition: 抓取隸屬編號的資料庫名稱
# Date: 05292020@Yishan
#=======================================================
# {{{ def retrieve_noumenon_dbname(metadata,sess)
def retrieve_noumenon_dbname(metadata,sess,noumenontype,noumenonid):
    thisid_existed = False
    catch_dbname = ""
    tableDict = {
        "dep":"department",
        "site":"site",
        "pla":"place",
        "dev":"device"
    }

    if tableDict.get(noumenontype) is not None:
        thistable = Table(tableDict[noumenontype] , metadata, autoload=True)
        #各表主鍵id field
        thistableidfield = "{}_id".format(tableDict[noumenontype])
        for row in sess.query(thistable).filter(getattr(thistable.c, thistableidfield) == noumenonid).all():
            drow = AdjustDataFormat().format(row._asdict())
            thisid_existed = True
            catch_dbname = drow["db_name"]
            if drow["db_name"] is None:
                if ((drow["noumenon_type"] != "" or drow["noumenon_type"] is not None) and (drow["noumenon_id"] is not None)):
                    return retrieve_noumenon_dbname(metadata,sess,drow["noumenon_type"],drow["noumenon_id"])
        
    return thisid_existed,catch_dbname
# }}}

#=======================================================
# Definition: 裝飾器包裝- 檢查content_type
# Date: 11262020@Yishan
#=======================================================
#{{{def decorator_check_content_type()
def decorator_check_content_type(request,access_content_type="application/json"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            #切割;charset=utf-8，有無都可
            if request.content_type.split(";")[0] != access_content_type:
                return jsonify( **{"Response":"Invalid content-type. Must be '{}'".format(access_content_type)})
            return func(*args, **kwargs)
        return wrapper
    return decorator
#}}}

#=======================================================
# Definition: 裝飾器-將特定可允許使用的system列表更新至func.__doc__內
# Date: 12162020 Yishan
# Update: 05202021 Yishan
# https://stackoverflow.com/questions/10307696/how-to-put-a-variable-into-python-docstring
#=======================================================
#{{{def decorator_update_docstring_parameter()
def decorator_update_docstring_parameter(**kwargs):
    def decorator(func):
        if func.__doc__ is not None and VerifyDataStrLawyer(func.__doc__).verify_json():
            variable_docstrings = {}
            for a, b in kwargs.items():
                variable_docstrings[a] = b
                
            doc_obj = json.loads(func.__doc__)
            doc_obj.update(variable_docstrings)
            func.__doc__ = json.dumps(doc_obj)
        return func
    return decorator
# }}}

#=======================================================
# Definition: 
# 1.裝飾器-進入api function前先檢查此api是否允許this client system
# 2.若ACCESS_SYSTEM_LIST為None表示以globalvar預設的SYSTEMLIST為合法系統列表
# Date: 05202021 Yishan
#=======================================================
#{{{def decorator_check_legal_system(ACCESS_SYSTEM_LIST=None)
def decorator_check_legal_system(SYSTEM=None,ACCESS_SYSTEM_LIST=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            systemlist = ACCESS_SYSTEM_LIST
            if systemlist is None:
                systemlist = globalvar.SYSTEMLIST[globalvar.SERVERIP]
            if SYSTEM is not None and SYSTEM not in systemlist:
                return jsonify( **{"Response":"system : '{}' has no privillege to use this API".format(SYSTEM)})

            for k, v in kwargs.items():
                if k == "SYSTEM" and v not in systemlist:
                    return jsonify( **{"Response":"system : '{}' has no privillege to use this API".format(v)})
            return func(*args, **kwargs)
        return wrapper
    return decorator
# }}}

#=======================================================
#
#=======================================================
#{{{def disconnect_database()
def disconnect_database(dbSess=None, dbSession=None, dbEngine=None):
    if dbSess is not None:
        dbSess.close()
        print "~~~~~~~~disconnect_database dbsess over~~~~~~~"
    if dbSession is not None:
        dbSession.remove()
        print "~~~~~~~~disconnect_database dbSession over~~~~~~~"
    if dbEngine is not None:
        dbEngine.dispose()
        print "~~~~~~~~disconnect_database dbEngine over~~~~~~~"
# }}}

#=======================================================
# Definition: 整合通用新增函式(mysql、mssql)
# Date: 03262021 Yishan
#=======================================================
#{{{def commonuse_register_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, selectDB):
def commonuse_register_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, selectDB):
    #多筆資料新增的狀態
    insertstatus = [] 
    #此資料表的主鍵為id(流水號，自動產生)
    thisPRIisid = False
    nextPRIid = None
    HavePRI = True

    try:
        #check table existed or not
        if not retrieve_table_exist(metadata, tableName, SYSTEM):
            return {"err_msg":"Table '{}' doesn't exist".format(tableName)}
        
        #desc table schema
        desc_table_return = desc_table(metadata, tableName, SYSTEM, havetime=False, selectDB=selectDB)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        keyList = desc_table_return[2]
        schemaDict = desc_table_return[3]
        defaultDict = desc_table_return[4]
        nullableDict = desc_table_return[6]

        if desc_table_status != 'ok':
            return {"err_msg":desc_table_status}
        
        registertargetTable = Table(tableName , metadata, autoload=True)

        if not keyList:
            HavePRI = False
            postDataKEYtostrList = ConvertData().convert(reqdataDict)
            noKeyPostDataList = []
            for i in range(len(postDataKEYtostrList.values())):
                for q in range(len(postDataKEYtostrList.values()[i])):
                    temp = {}
                    temp[postDataKEYtostrList.keys()[i]] = postDataKEYtostrList.values()[i][q]
                    if i == 0:
                        noKeyPostDataList.append(temp)
                    else:
                        noKeyPostDataList[q].update(temp)
                        #add time
                        # noKeyPostDataList[q].update({globalvar.CREATETIME[globalvar.SERVERIP][selectDB]:datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                        # noKeyPostDataList[q].update({globalvar.UPLOADTIME[globalvar.SERVERIP][selectDB]:datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            
            sess.execute(registertargetTable.insert().values(noKeyPostDataList))
            sess.commit()
            return {"err_msg":"ok"}

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        for i in range(len(keyList)): 
            #有任何主鍵沒post到，return error
            if reqdataDict.get(keyList[i]) is None:
                return {"err_msg":"primary key is necessary"}
            
            if not isinstance(reqdataDict.get(keyList[i]),list):
                return {"err_msg":"Error type of '{}',it must be an Array".format(keyList[i])}

            #把unicode list 轉成 str list，才能抓到list內的各內容
            postDataKEYtostrList = map(str,reqdataDict.get(keyList[i]))
            #判斷主鍵為空陣列回覆error
            if not postDataKEYtostrList:
                return {"err_msg":"primary key {} can't be None".format(keyList[i])}

            postDataCount = len(postDataKEYtostrList)
            thisseq = -1
            for j in range(postDataCount):
                #微型系統的baccount表id不為流水號
                if tableName not in ("baccount","user") and keyList[i] == "id":
                    thisPRIisid = True
                    if postDataKEYtostrList[j] != "":
                        return {"err_msg":"primary key '{}'為自動地增值，放空值即可".format(keyList[i])}
                    
                    auto_increment_number_sql = 'SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_NAME = "{}";'.format(tableName)
                    #抓取自動新增的下一個id
                    nextPRIid = sess.execute(auto_increment_number_sql).fetchall()[0][0]

                if keyList[i] != "seq":
                    query_field = getattr(registertargetTable.c, keyList[i])
                    if isinstance(postDataKEYtostrList[j],str):
                        postKeyList.append("{} = '{}'".format(query_field,postDataKEYtostrList[j]))
                    else:
                        postKeyList.append("{} = {}".format(query_field,postDataKEYtostrList[j]))
                else:
                    dataexist = sess.query(registertargetTable).count()
                    columnAttr = getattr(registertargetTable.c, "seq")
                    if dataexist != 0:
                        for row in sess.query(getattr(registertargetTable.c,"seq")).order_by(desc(getattr(registertargetTable.c,"seq"))).limit(1):
                            thisseq = row[0]

                    nextPRIid = int(thisseq)+(j+1)
                    postKeyList.append('({} = {})'.format(columnAttr,nextPRIid))

        #每一筆新增資料的where條件陣列
        whereDict = [postKeyList[i::postDataCount] for i in range(postDataCount)]

        #每一筆新增資料的where條件str
        for i in range(len(whereDict)):
            check_data_existed = False
            if not thisPRIisid:
                #以&來join陣列
                whereStr = " and ".join(whereDict[i])
                for row in sess.execute(registertargetTable.select(text(whereStr))):
                    check_data_existed = True

            #獲取目前的i
            thisNum = i
            #各筆資料的所有Data dict
            postDataList = {}

            if not check_data_existed:
                for x in range(len(fieldList)):
                    #判斷有defaule值的欄位且無丟資料，則跳過loop
                    if defaultDict[fieldList[x]] and reqdataDict.get(fieldList[x]) is None:
                        continue

                    #有任何欄位沒post到，return error，排除有dafault值的欄位
                    if (reqdataDict.get(fieldList[x]) is None) and (not defaultDict[fieldList[x]]):
                        return {"err_msg":"{} missing post some fields : '{}'".format(tableName,fieldList[x])}

                    #檢查所有欄位格式不為list，return error
                    if not isinstance(reqdataDict.get(fieldList[x]),list):
                        return {"err_msg":"Error type of '{}',it must be an Array".format(fieldList[x])}

                    postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                    #postDatatostrList = map(str,reqdataDict.get(fieldList[x]))

                    if len(postDatatostrList) != postDataCount:
                        return {"err_msg":"The number of input data does not match"}
                    
                    #Yishan@12252020 排除有default值或可允許null的欄位，不檢查是否有值
                    if (not (defaultDict[fieldList[x]] or nullableDict[fieldList[x]])) and (postDatatostrList[thisNum] is None):
                        return {"err_msg":"{} data can't be None".format(fieldList[x])}
                    
                    if fieldList[x] == "seq":
                        postDataList['seq'] = int(thisseq)+(i+1)
                    else:
                        #needRE = False
                        if tableName in ("baccount","user") or fieldList[x] != "id":
                            postDataList[fieldList[x]] = postDatatostrList[thisNum]
                        #    if postDatatostrList[thisNum] is not None:
                        #        if (not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int))) and \
                        #            ((not VerifyDataStrLawyer(postDatatostrList[thisNum]).verify_json()) and (schemaDict[fieldList[x]] not in ("TIMESTAMP","DATETIME","DATE"))):
                        #            #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                        #            #Yishan@12252020 判斷此欄位是否為時間型態，若是取消re替代
                        #            needRE = True
                        #    if needRE:
                        #        postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                        #    else:
                        #        postDataList[fieldList[x]] = postDatatostrList[thisNum]

                if tableName not in  ("baccount","mrp_recpl_wire_furnacecode","mrp_recpl"):
                    #add time
                    postDataList[globalvar.CREATETIME[globalvar.SERVERIP][selectDB]] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    postDataList[globalvar.UPLOADTIME[globalvar.SERVERIP][selectDB]] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                sess.execute(registertargetTable.insert().values(postDataList))
                sess.commit()
            else:
                insertstatus.append(whereStr)

        if len(insertstatus) != 0:
            return {"err_msg":"ok", "insertstatus":"Error: {} ID ({}) existed".format(tableName," , ".join(insertstatus)),"nextPRIid":nextPRIid}
        return {"err_msg":"ok","nextPRIid":nextPRIid}

    except Exception as e:
        return {"err_msg":appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)}
#}}}

#=======================================================
# Definition: 整合通用修改函式(mysql、mssql)
# Date: 03262021 Yishan
#=======================================================
# {{{ commonuse_update_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, selectDB):
def commonuse_update_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, selectDB):
    #多筆資料更新的狀態
    updatestatus = [] 
    try:
        #check table existed or not
        if not retrieve_table_exist(metadata, tableName, SYSTEM):
            return ["Table '{}' doesn't exist".format(tableName)]

        #desc table schema
        desc_table_return = desc_table(metadata, tableName, SYSTEM, havetime=True, selectDB=selectDB)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        keyList = desc_table_return[2]
        schemaDict = desc_table_return[3]
        defaultDict = desc_table_return[4]
        nullableDict = desc_table_return[6]

        if desc_table_status != 'ok':
            return [desc_table_status]

        updatetargetTable = Table(tableName , metadata, autoload=True)

        if not keyList:
            return ["Error 此資料表找不到主鍵"]

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        #Yishan 08182020 確保若是多主鍵，每個主鍵post的data length一樣
        checkpostDataCount = 0
        for i in range(len(keyList)):
            if reqdataDict.get("old_"+ keyList[i]) is None:
                return ["primary key is necessary and format of the primary key must be 'old_xxx'"]
            
            if not isinstance(reqdataDict.get("old_"+ keyList[i]),list):
                return ["Error type of '{}',it must be an Array".format("old_"+ keyList[i])]

            postDataKEYtostrList = reqdataDict.get("old_"+ keyList[i])
            if not postDataKEYtostrList:
                return ["error 'primary key' parameter input '{}', can't Null".format("old_"+ keyList[i])]

            #檢查第一個資料的屬性，若不為數字就把unicode list 轉成 str list，才能抓到list內的各內容
            if not isinstance(reqdataDict.get("old_"+ keyList[i])[0],int):
                postDataKEYtostrList = map(str,postDataKEYtostrList)

            postDataCount = len(postDataKEYtostrList)
            if i == 0:
                checkpostDataCount = postDataCount

            if (i != 0) and (postDataCount != checkpostDataCount):
                return ["error 'Composite Primary Key' parameter input '{}', Length does not match".format(reqdataDict.get("old_"+ keyList[i]))]

            for j in range(postDataCount):
                #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                query_field = getattr(updatetargetTable.c,keyList[i])
                if isinstance(postDataKEYtostrList[j],str):
                    postKeyList.append("{} = '{}'".format(query_field,postDataKEYtostrList[j]))
                else:
                    postKeyList.append("{} = {}".format(query_field,postDataKEYtostrList[j]))
                    
        #每一筆更新資料的where條件陣列
        whereDict = [postKeyList[i::postDataCount] for i in range(postDataCount)]

        #每一筆更新資料的where條件str
        for i in range(len(whereDict)):
            check_data_existed = False
            #以&來join陣列
            whereStr = " and ".join(whereDict[i])
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
                            return ["The primary key can't be updated"]
                        
                        if not isinstance(reqdataDict.get(fieldList[x]),list):
                            return ["Error type of '{}',it must be an Array".format(fieldList[x])]

                        postDatatostrList = ConvertData().convert(reqdataDict.get(fieldList[x]))
                        if len(postDatatostrList) != postDataCount:
                            return ["The number of input data does not match"]

                        #Yishan@12252020 排除有default值或可允許null的欄位，不檢查是否有值
                        if (not (defaultDict[fieldList[x]] or nullableDict[fieldList[x]])) and (postDatatostrList[thisNum] is None):
                            return ["{} data can't be None".format(fieldList[x])]

                        #needRE = False
                        #if postDatatostrList[thisNum] is not None:
                        #    if (not (isinstance(postDatatostrList[thisNum],dict) or isinstance(postDatatostrList[thisNum],float) or isinstance(postDatatostrList[thisNum],int))) and \
                        #        ((not VerifyDataStrLawyer(postDatatostrList[thisNum]).verify_json()) and (schemaDict[fieldList[x]] not in ("TIMESTAMP","DATETIME","DATE"))):
                        #        #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                        #        #Yishan@12252020 判斷此欄位是否為時間型態，若是取消re替代
                        #        needRE = True
                        #if needRE:
                        #    postDataList[fieldList[x]] = re.sub(r'[:]',"-",postDatatostrList[thisNum])
                        #else:
                        #    postDataList[fieldList[x]] = postDatatostrList[thisNum]
                        postDataList[fieldList[x]] = postDatatostrList[thisNum]
                            
                if not postDataList:
                    updatestatus.append("Error '{}' 更新失敗：沒有給予任何資料欄位".format(whereStr))
                else:
                    sess.execute(updatetargetTable.update().where(text(whereStr)).values(postDataList))
                    sess.commit()
            else:
                updatestatus.append("Error '{}' doesn't existed".format(whereStr))

        if updatestatus:
            return ["ok", updatestatus]
        return ["ok"]

    except Exception as e:
        return [appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)]
# }}}

#=======================================================
# Definition: 整合通用刪除函式(mysql、mssql)
# Date: 03262021 Yishan
#=======================================================
# {{{ commonuse_delete_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, selectDB)
def commonuse_delete_integration_myms(reqdataDict, sess, metadata, tableName, SYSTEM, selectDB):
    #是否有使用time參數
    timeflag = False
    #多筆資料刪除的狀態
    deletestatus = [] 
    deletestatusmsg = ""

    try:
        #check table existed or not
        if not retrieve_table_exist(metadata, tableName, SYSTEM):
            return ["Table '{}' doesn't exist".format(tableName)]

        #desc table schema
        desc_table_return = desc_table(metadata, tableName, SYSTEM, havetime=True, selectDB=selectDB)
        desc_table_status = desc_table_return[0]
        fieldList = desc_table_return[1]
        keyList = desc_table_return[2]

        if desc_table_status != 'ok':
            return [desc_table_status]

        deletetargetTable = Table(tableName , metadata, autoload=True)

        #判斷是否有使用time參數
        if reqdataDict.get("timeflag") is not None:
            timeflag = True
            if not isinstance(reqdataDict.get("timeflag"),dict):
                return ["Error type of '{}',it must be an Object".format(reqdataDict.get("timeflag"))]
            
            if len(reqdataDict.get("timeflag").keys()) > 1:
                return ["系統只接受一個時間欄位"]
            
            if reqdataDict.get("timeflag").keys()[0] not in fieldList:
                return ["時間欄位 '{}' 不存在".format(reqdataDict.get("timeflag").keys()[0])]

            where_time_attr = getattr(deletetargetTable.c,reqdataDict.get("timeflag").keys()[0])

            timevalue = reqdataDict.get("timeflag").values()[0]
            if not isinstance(timevalue,list):
                return ["Error type of '{}',it must be an Array".format(timevalue)]
            
            if not timevalue:
                return ["error 'timeflag' parameter input, '{}' can't Null".format(timevalue)]

            #判斷timevalue[0],timevalue[1]皆為合法時間字串
            for timestr in timevalue:
                if not VerifyDataStrLawyer(timestr).verify_date():
                    return ["error 'timeflag' parameter input, date str '{}' is illegal".format(timestr)]

            where_time_start = timevalue[0]

            if len(timevalue) == 1:
                where_time_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                if datetime.strptime(timevalue[1], "%Y-%m-%d %H:%M:%S") < datetime.strptime(timevalue[0], "%Y-%m-%d %H:%M:%S"):
                    return ["error 'timeflag' parameter input, start date str '{}' need smaller than end date str '{}'".format(timevalue[0],timevalue[1])]

                where_time_end = timevalue[1]
        
        if timeflag:
            sess.execute(deletetargetTable.delete().where(between(where_time_attr,where_time_start,where_time_end)))
            sess.commit()
            return ["ok"]

        #以抓取到的keyList列表去跟POST的Data比對，並合併成同一個陣列
        postKeyList = []
        #檢查是否主鍵Data數量相同
        setPKdatanum = ""

        if not keyList:
            return ["Error 此資料表找不到主鍵"]

        for i in range(len(keyList)):
            if reqdataDict.get(keyList[i]) is not None:
                if not isinstance(reqdataDict.get(keyList[i]),list):
                    return ["Error type of '{}',it must be an Array".format(keyList[i])]

                #把unicode list 轉成 str list，才能抓到list內的各內容
                postDataKEYtostrList = map(str,reqdataDict.get(keyList[i]))
                #判斷主鍵為空陣列回覆error
                if not postDataKEYtostrList:
                    return ["primary key {} can't be None".format(keyList[i])]

                postDataCount = len(postDataKEYtostrList)
                #第一次for loop PRI，確定輸入的主鍵資料數量是相同的
                if isinstance(setPKdatanum,str):
                    setPKdatanum = postDataCount
                else:
                    if setPKdatanum != postDataCount:
                        return ["The number of input data does not match"]
                    
                for j in range(postDataCount):
                    query_field = getattr(deletetargetTable.c,keyList[i])
                    if isinstance(postDataKEYtostrList[j],str):
                        postKeyList.append("{} = '{}'".format(query_field,postDataKEYtostrList[j]))
                    else:
                        postKeyList.append("{} = {}".format(query_field,postDataKEYtostrList[j]))
                    # #Yishan@09102019 data裡有: 會導致UnicodeDecodeError，所以利用re替代掉
                    # postKeyList.append('({} = \"{}\")'.format(query_field,re.sub(r'[:]',"-",postDataKEYtostrList[j])))

        #檢查是否都沒input PRI
        if len(postKeyList) == 0:
            return ["At least one primary key is necessary"]

        #每一筆刪除資料的where條件陣列
        whereDict = [] 
        for i in range(postDataCount):
            #以間隔方式一一抓取
            whereDict.append(postKeyList[i::postDataCount])

        #每一筆刪除資料的where條件str
        for i in range(len(whereDict)):
            check_data_existed = False
            #以&來join陣列
            whereStr = " and ".join(whereDict[i])
            for row in sess.execute(deletetargetTable.select(text(whereStr))):
                check_data_existed = True

            if check_data_existed:
                sess.execute(deletetargetTable.delete().where(text(whereStr)))
                sess.commit()
            else:
                deletestatus.append(whereStr)
        
        if deletestatus:
            return ["ok", "Error: {} ID ({}) existed".format(tableName," , ".join(deletestatus))]
        return ["ok"]

    except Exception as e:
        return [appPaaS.catch_exception(e,sys.exc_info(),SYSTEM)]
# }}}

__all__ = [
    'RegularExpression','ConvertData','AdjustDataFormat',
    'VerifyDataStrLawyer','Prpcrypt','ApiSqlsyntaxActions',
    'sqlsyntax_params_actions','join_sqlsyntax_params_actions',
    'DecoratorCheckUriParameterExist','DecoratorOauth2ConnectDB',
    'check_dbconnect_success','check_uri_parameter_exist',
    'check_post_parameter_exist','check_post_parameter_exist_format','retrieve_database_exist',
    'retrieve_table_exist','desc_table','check_user_defined_type',
    'adjust_dict_for_joinapi','create_database','create_table',
    'delete_database','delete_tables','retrieve_noumenon_dbname',
    'decorator_check_content_type','decorator_update_docstring_parameter','decorator_check_legal_system',
    'commonuse_register_integration_myms','commonuse_update_integration_myms',
    'commonuse_delete_integration_myms'
]