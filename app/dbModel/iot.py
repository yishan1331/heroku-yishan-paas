# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7
#sql_utility Module Description
"""
==============================================================================
created    : 03/23/2017
Last update: 04/21/2017
Developer: Wei-Chun Chang 
Lite Version 2 @Yishan08032019
API Version 1.0
 
Filename: sql_utility.py
Description: basically, all writes to the module will be opened to users who has authorized 
    1. register a sensor 
    2. query a sensor's basic info.
    3. query sensor raw data
       queryFirst/queryLast/queryRows
    4. post sensor raw data
Total = 2 APIs
==============================================================================
"""

#=======================================================
#system level modules
#=======================================================
# {{{
import sys, hashlib
from sqlalchemy import Table, Column, Integer, Float, Boolean, String, Text, TIMESTAMP, DateTime, JSON, Date, Numeric
from sqlalchemy.orm import mapper
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as types
from sqlalchemy.sql import func
# }}}

#=======================================================
#global-defined variables
#=======================================================
# {{{
#Construct a base class for declarative class definitions.
Base = declarative_base()
# }}}

#=======================================================
# special API to generate Raw Data DB 
# a privileges for super user
#=======================================================
# {{{ def genRawDBName(depID):
def genRawDBName(dbID, typeName):
        return typeName + "_" + hashlib.md5(dbID).hexdigest()[:29]
# }}}

# {{{ class Sensor(Base)
class Sensor(Base):
    __tablename__ = 'sensor'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    sensor_type = Column(Boolean)
    noumenon_type = Column(String)
    noumenon_id = Column(Integer)
    sensor_raw_table = Column(String)
    sensor_attr = Column(JSON)
    note = Column(String)
    creator = Column(String)
    modifier = Column(String)
    created_at = Column(DateTime) 
    updated_at = Column(DateTime)
# }}}

# {{{ class User(Base) 春日
class User(Base):
    __tablename__ = 'user'
    user_id = Column(String, primary_key=True)
    cus_id = Column(Integer)
    pwd = Column(String)
    name = Column(String)
    email = Column(String)  #unit
    access_list = Column(JSON)  #unit
    creator = Column(String)
    modifier = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
# }}} 

# class LxmlXMLType(types.UserDefinedType):
#     from lxml import etree
#     def get_col_spec(self):
#         return 'XML'

#     def bind_processor(self, dialect):
#         def process(value):
#             if value is not None:
#                 if isinstance(value, str):
#                     return value
#                 else:
#                     return etree.tostring(value)
#             else:
#                 return None
#         return process

#     def result_processor(self, dialect, coltype):
#         def process(value):
#             if value is not None:
#                 value = etree.fromstring(value)
#             return value
#         return process
#https://stackoverflow.com/questions/43333410/sqlalchemy-declaring-custom-userdefinedtype-for-xml-in-mssql

class ElementTreeXMLType(types.UserDefinedType):
    import xml.etree.ElementTree as etree
    def get_col_spec(self):
        return 'XML'

    def bind_processor(self, dialect):
        def process(value):
            if value is not None:
                if isinstance(value, str):
                    return value
                else:
                    return etree.tostring(value)
            else:
                return None
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is not None:
                value = etree.fromstring(value)
            return value
        return process
#https://stackoverflow.com/questions/16153512/using-postgresql-xml-data-type-with-sqlalchemy

#=======================================================
# 動態變數新增預設機台感測器資料表
# Date: 01112021@Yishan
# https://stackoverflow.com/questions/54646044/sqlalchemy-tablename-as-a-variable
#=======================================================
#{{{ def create_default_device_models(device_serial_number):
def create_default_device_models(device_serial_number):
    class DeviceMain(Base):
        __tablename__ = device_serial_number+"_main"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        mcks_op_temp = Column(Numeric(18,5), comment="主曲軸操作側溫度")
        mcks_cus_temp = Column(Numeric(18,5), comment="主曲軸剪斷側溫度")
        msld_op_temp = Column(Numeric(18,5), comment="主滑台操作側溫度")
        msld_cus_temp = Column(Numeric(18,5), comment="主滑台剪斷側溫度")
        stnk_lub_temp = Column(Numeric(18,5), comment="副油箱潤滑油溫度")
        mcks_op_flow = Column(Numeric(18,5), comment="主曲軸操作側流量")
        mcks_cus_flow = Column(Numeric(18,5), comment="主曲軸剪斷側流量")
        msld_op_flow = Column(Numeric(18,5), comment="主滑台操作側流量")
        msld_cus_flow = Column(Numeric(18,5), comment="主滑台剪斷側流量")
        cus_lup_out_oprs = Column(Numeric(18,5), comment="剪斷側潤滑泵輸出油壓")
        msld_lup_out_oprs = Column(Numeric(18,5), comment="主滑台潤滑泵輸出油壓")
        cus_end_oprs = Column(Numeric(18,5), comment="剪斷側油壓末端油壓")
        msld_end_oprs = Column(Numeric(18,5), comment="主滑台油壓末端油壓")
        tri_comb_aprs = Column(Numeric(18,5), comment="三點組合空壓")
        pko_sfpin_aprs = Column(Numeric(18,5), comment="前沖安全銷空壓")
        clp_spr_aprs = Column(Numeric(18,5), comment="夾仔空壓彈簧空壓")
        dko_sfpin_aprs = Column(Numeric(18,5), comment="後通安全銷空壓")
        trim_aprs = Column(Numeric(18,5), comment="整頭空壓")
        fedw_aprs = Column(Numeric(18,5), comment="送料輪空壓")
        clg_aprs = Column(Numeric(18,5), comment="冷卻油管舉起空壓")
        postub_aprs = Column(Numeric(18,5), comment="後牙管空壓")
        trx_jaw_aprs = Column(Numeric(18,5), comment="三軸夾爪空壓")
        clp_aprs = Column(Numeric(18,5), comment="夾仔空壓")
        mcg_revsp = Column(Numeric(18,5), comment="機器轉速")
        aut_level = Column(Numeric(18,5), comment="副油箱油位")
        clut_brk_cnt = Column(Integer, comment="離合器煞車計數")
        cnt1 = Column(Integer, comment="計數器1累計值")
        cnt2 = Column(Integer, comment="計數器2累計值")
        #27個燈號
        lub_press_slder = Column(Integer, comment="潤滑油壓(主滑台側)")
        abn_pneu_press = Column(Integer, comment="氣壓")
        overload = Column(Integer, comment="電流")
        abn_driver = Column(Integer, comment="伺服驅動器")
        pko_sfbolt = Column(Integer, comment="前沖安全銷")
        ko_sfbolt = Column(Integer, comment="後沖安全銷")
        lub_press_cutoff = Column(Integer, comment="潤滑油壓(剪斷側)")
        prob_tran_float = Column(Integer, comment="挟台")
        prob_sf_door = Column(Integer, comment="安全門")
        lub_overflow = Column(Integer, comment="潤滑油")
        abn_temp_slder = Column(Integer, comment="溫度")
        abn_lub_flow = Column(Integer, comment="潤滑油量")
        abn_brk_pla_clut = Column(Integer, comment="離合器煞車距離")
        hyd_press_rscrpi_lck = Column(Integer, comment="油壓鎖後牙管")
        abn_forg = Column(Integer, comment="BRANKAMP壓造")
        sh_feed = Column(Integer, comment="短寸")
        finish_cnt = Column(Integer, comment="計數")
        mtr_end = Column(Integer, comment="材料")
        hyd_press_grpse_lck = Column(Integer, comment="鎖挟台油壓")
        oper_door = Column(Integer, comment="操作門")
        die_blkwed_hyd_oil_press = Column(Integer, comment="油壓模座契型塊")
        die_blkcyl_hyd_oil_press = Column(Integer, comment="油壓模座油壓缸")
        pun_blkcyl_hyd_oil_press = Column(Integer, comment="油壓沖具座油壓缸")
        oil_level_low = Column(Integer, comment="油量(副油箱)")
        mat_wgt = Column(Integer, comment="材料秤重")
        sf_window = Column(Integer, comment="安全視窗")
        motor_brk = Column(Integer, comment="馬達繼電器")
        opr = Column(Integer, comment="機台運轉狀態")
        error_code = Column(JSON, comment="異常代碼")

        __table_args__ = {'comment': '主機台'}  # 表註釋 #https://www.cnblogs.com/shengulong/p/9989618.html

    class DeviceEmeter(Base):
        __tablename__ = device_serial_number+"_emeter"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        current = Column(Numeric(18,5), comment="當前電流值")
        cur_cubr = Column(Numeric(18,5), comment="電流不平衡率")
        cur_chdr = Column(Numeric(18,5), comment="電流諧波失真率")
        voltage = Column(Numeric(18,5), comment="當前電壓值")
        volt_vubr = Column(Numeric(18,5), comment="電壓不平衡率")
        volt_chdr = Column(Numeric(18,5), comment="電壓諧波失真率")
        frequency = Column(Numeric(18,5), comment="頻率")
        TPF = Column(Numeric(18,5), comment="總功率因數")
        RELEC = Column(Numeric(18,5), comment="實功電能")
        RPWD_cur = Column(Numeric(18,5), comment="實功功率需量 - 當前")
        RPWD_pred = Column(Numeric(18,5), comment="實功功率需量 - 預測")
        RPWD_peak = Column(Numeric(18,5), comment="實功功率需量 - 峰值")
        power_peak = Column(Numeric(18,5), comment="功率峰值")
        power = Column(Numeric(18,5), comment="功率")

        __table_args__ = {'comment': '智慧電表'}  # 表註釋

    class DeviceVibmotor(Base):
        __tablename__ = device_serial_number+"_vibMotor"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        FFT = Column(Numeric(18,5), comment="FFT")
        vibspeed_x = Column(Numeric(18,5), comment="振動速度－X軸")
        vibspeed_y = Column(Numeric(18,5), comment="振動速度－Y軸")
        vibspeed_z = Column(Numeric(18,5), comment="振動速度－Z軸")
        # FFT_config = Column(ElementTreeXMLType, comment="FFT讀取設定")
        FFT_config = Column(JSON, comment="FFT讀取設定")

        __table_args__ = {'comment': '振動主馬達'}  # 表註釋

    class DeviceVibbearing(Base):
        __tablename__ = device_serial_number+"_vibBearing"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        FFT = Column(Numeric(18,5), comment="FFT")
        vibspeed_x = Column(Numeric(18,5), comment="振動速度－X軸")
        vibspeed_y = Column(Numeric(18,5), comment="振動速度－Y軸")
        vibspeed_z = Column(Numeric(18,5), comment="振動速度－Z軸")
        # FFT_config = Column(ElementTreeXMLType, comment="FFT讀取設定")
        FFT_config = Column(JSON, comment="FFT讀取設定")

        __table_args__ = {'comment': '振動連座軸承'}  # 表註釋

    class DeviceServod(Base):
        __tablename__ = device_serial_number+"_servoD"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        # err_code = Column(ElementTreeXMLType, comment="故障訊息")
        err_code = Column(JSON, comment="故障訊息")

        __table_args__ = {'comment': '伺服驅動器'}  # 表註釋
    
    class DeviceLoadCell(Base):
        __tablename__ = device_serial_number+"_loadCell"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        wire_weight = Column(Numeric(18,5), comment="線材重量")

        __table_args__ = {'comment': '荷重元'}  # 表註釋
    
    class DeviceSmb(Base):
        __tablename__ = device_serial_number+"_smb"

        upload_at = Column(DateTime, primary_key=True, server_default=func.current_timestamp(6))
        curr_up_traffic = Column(Integer, comment="當前上傳流量")
        curr_down_traffic = Column(Integer, comment="當前下載流量")

        __table_args__ = {'comment': 'SMB紀錄'}  # 表註釋
    
    return DeviceMain, DeviceEmeter, DeviceVibmotor, DeviceVibbearing, DeviceServod, DeviceLoadCell, DeviceSmb
#}}}

def create_default_device_table(app,device_serial_number):
    mysql_status = False
    err_msg = "ok"
    try:
        mysql_sensor_data = [
            {
                "name":device_serial_number+"主機台",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_main",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
            {
                "name":device_serial_number+"智慧電表",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_emeter",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
            {
                "name":device_serial_number+"振動主馬達",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_vibMotor",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
            {
                "name":device_serial_number+"振動連座軸承",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_vibBearing",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
            {
                "name":device_serial_number+"伺服驅動器",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_servoD",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
            {
                "name":device_serial_number+"荷重元",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_loadCell",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
            {
                "name":device_serial_number+"SMB紀錄",
                "sensor_type":0,
                "noumenon_type":"site",
                "noumenon_id":1,
                "sensor_raw_table":device_serial_number+"_smb",
                "sensor_attr":"",
                "note":"Created by PaaS",
                "creator":0,
                "modifier":0,
            },
        ]
        DbSession_mysql,metadata_mysql,engine_mysql= app.getDbSessionType(system="IOT")
        if DbSession_mysql is None:
            #表示連接資料庫有問題
            return False,engine_mysql

        sess_mysql = DbSession_mysql()

        SensorTable = Table("sensor", metadata_mysql,  autoload=True)
        for i in mysql_sensor_data:
            if not sess_mysql.query(SensorTable).filter(getattr(SensorTable.c, "sensor_raw_table") == i["sensor_raw_table"]).count():
                sess_mysql.execute(SensorTable.insert().values(i))
        sess_mysql.commit()
        mysql_status = True

    except Exception as e:
        print "~~~~Exception mysql insert~~~~"
        print e
        err_msg = app.catch_exception(e,sys.exc_info(),"IOT")
        print err_msg

    finally:
        if 'DbSession_mysql' in locals().keys() and DbSession_mysql is not None:
            sess_mysql.close()
            DbSession_mysql.remove()
            engine_mysql.dispose()
    
    if not mysql_status:
        return False,err_msg

    try:
        DbSession_pg,metadata,engine_pg= app.getDbSessionType(system="IOT",dbName="site2",forRawData="postgres",echo=True)
        if DbSession_pg is None:
            print "~~~~~db connect fail before_first_request~~~~"
            print engine_pg
            return False,engine_pg

        sess_pg = DbSession_pg()
        
        clscreate = create_default_device_models(device_serial_number)
        # print "~~~clscreate~~~"
        # print clscreate
        for i in clscreate:
            # print "~~~i~~~"
            # print i
            # print i.__dict__
            # print i.__tablename__
            # print i.__table__
            if not engine_pg.dialect.has_table(engine_pg, i.__tablename__): 
                # print "create"
                i.__table__.create(engine_pg)
            # else:
            #     print "existed"
            #     i.__table__.drop(engine_pg)

        # metadata.create_all(engine)
        return True,"ok"

    except Exception as e:
        print "~~~~Exception before_first_request~~~~"
        print e
        err_msg = app.catch_exception(e,sys.exc_info(),"IOT")
        print err_msg
        return False,err_msg

    finally:
        if 'DbSession_pg' in locals().keys() and DbSession_pg is not None:
            sess_pg.close()
            DbSession_pg.remove()
            engine_pg.dispose()

#=======================================================
# Translate dictionary constraint to statement used in create table SQL
#=======================================================
# {{{ def TransConstraint(attrDic):
def TransConstraint(attrDict):
    fName = attrDict['name']
    conStr = ''
    if attrDict.has_key('lower') and attrDict.has_key('upper'):
        conStr = "{} >= {} AND {} <= {}".format(   \
        fName ,attrDict['lower'], fName, attrDict['upper'])
    elif attrDict.has_key('lower'):
        conStr = "{} >= {}".format(fName,attrDict['lower'])
    elif attrDict.has_key('upper'):
        conStr = "{} <= {}".format(fName,attrDict['upper'])
    else:
        conStr = ''

    return conStr
# }}}

# {{{ def map_class_to_table(cls, table, entity_name, **kw):
def map_class_to_table(cls, table, entity_name, **kw):
    newcls = type(entity_name, (cls, ), {})
    mapper(newcls, table, **kw)
    return newcls
# }}}

# {{{ def fieldNameNormalize(strColName):
def fieldNameNormalize(strColName):
    return strColName.strip().lower().replace(' ','_').replace('-','_')
# }}}

# {{{ def dictSchemaToNameTypeConstraintsTuple(schemaDict):
def dictSchemaToNameTypeConstraintsTuple(schemaDict):
    # schemaDict to raw data table mapping (one-to-one)
    import logging
    logging.getLogger('fappYott').info(schemaDict)
    lstColNames = []
    lstTypeObj = []
    lstConstrain = []
    if schemaDict.has_key('name'):
        # colname = schemaDict['name'].lower().replace(' ','_')
        colname = fieldNameNormalize(schemaDict['name'])
        coltype = schemaDict['type']
        lstColNames.append(colname)
        lstTypeObj.append( TYPE_TO_SQLTYPE_DICT[coltype] )

        if schemaDict.has_key('lower_bound') \
            and schemaDict.has_key('upper_bound'):
            str1 = "{} >= {} AND {} <= {}".format(   \
                colname ,schemaDict['lower_bound'], colname, schemaDict['upper_bound'])
        elif schemaDict.has_key('lower_bound'):
            str1 = "{} >= {}".format(colname,schemaDict['lower_bound'])
        elif schemaDict.has_key('upper_bound'):
            str1 = "{} <= {}".format(colname,schemaDict['upper_bound'])
        else:
            str1 = ''

        lstConstrain.append(str1)
    maxColumnsInRawtable = 500 # have seen ~ 309 sensors in an single machine profile
    for iCol in xrange(1,maxColumnsInRawtable):
        if schemaDict.has_key('name%d'%(iCol)):
            # colname = schemaDict['name%d'%(iCol)].lower().replace(' ','_')
            colname = fieldNameNormalize(schemaDict['name%d'%(iCol)])
            coltype = schemaDict['type%d'%(iCol)]
            lstColNames.append(colname)
            lstTypeObj.append( TYPE_TO_SQLTYPE_DICT[coltype] )

            if schemaDict.has_key('lower_bound%d'%(iCol)) \
                and schemaDict.has_key('upper_bound%d'%(iCol)):
                str2 = "{} >= {} AND {} <= {}".format(   \
                    colname ,schemaDict['lower_bound%d'%(iCol)], colname, schemaDict['upper_bound%d'%(iCol)])

            elif schemaDict.has_key('lower_bound%d'%(iCol)):
                str2 = "{} >= {}".format(colname,schemaDict['lower_bound%d'%(iCol)])
            elif schemaDict.has_key('upper_bound%d'%(iCol)):
                str2 = "{} <= {}".format(colname,schemaDict['upper_bound%d'%(iCol)])
            else:

                str2 = ''
            lstConstrain.append(str2)

    return lstColNames, lstTypeObj,lstConstrain
# }}}