# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7
"""
==============================================================================
created    : 03/23/2017
Last update: 04/21/2017
Developer: Wei-Chun Chang 
Lite Version 2 @Yishan08032019
API Version 1.0
 
Filename: sapidosystem.py
Total 
==============================================================================
"""

#=======================================================
#system level modules
#=======================================================
 # {{{
import sys

from sqlalchemy import Column, Integer, Float, Boolean, String, Text, TIMESTAMP, DateTime, JSON, Date, Numeric
from sqlalchemy.orm import mapper
from sqlalchemy.ext.declarative import declarative_base
import hashlib
# }}}

#=======================================================
#user-defined modules
#=======================================================
# import web_utility

#=======================================================
#global-defined variables
#=======================================================
# {{{
#Construct a base class for declarative class definitions.
Base = declarative_base()
# }}}

#=======================================================
# Type transformation 
#=======================================================
# {{{ sqlalchemy data type object
# modified for fixing issue in mysql dialect

TypeToSqlTypeObject = {
    'Integer': Integer,
    'Float': Float,
#    'Double': sqlalchemy.DOUBLE,
    'Boolean': Boolean,
    'String': Text,
    'TIMESTAMP': TIMESTAMP,
    'JSON': JSON,
    'Date' : Date,
    'Numeric' : Numeric

}
# }}} 

#=======================================================
# special API to generate Raw Data DB 
# a privileges for super user
#=======================================================
# {{{ def genRawDBName(depID):
def genRawDBName(dbID, typeName):
        return typeName + "_" + hashlib.md5(dbID).hexdigest()[:29]
# }}}

#=======================================================
# Class: User, for table "user_mysql"
#=======================================================
# {{{ class User(Base)
class User(Base):
    __tablename__ = 'user'
    uID = Column(String, primary_key=True)
    pwd = Column(String)
    uName = Column(String)
    uInfo = Column(String)  #unit
    email = Column(String)  #unit
    accessList = Column(JSON)  #unit
    noumenonType = Column(String)
    noumenonID = Column(String)
    creatorID = Column(String)
    createTime = Column(DateTime)
    lastUpdateTime = Column(DateTime)
# }}} 

#=======================================================
# Class: Noumenon related roles, for table 
# 1. "department": 
# 2. "factory": 
# 3. "place": 
# 4. "device":  
#=======================================================
# {{{ class Department(Base)
class Department(Base):
    __tablename__ = 'department'
    depID = Column(String, primary_key=True)
    depName = Column(String)
    noumenonID = Column(String) #use for upper level component
    noumenonType = Column(String) #use for upper level component type
    accessList = Column(JSON) #use for users who have access right to the component
    depInfo = Column(String)
    creatorID = Column(String) #user who created the component
    dbName = Column(String)
    createTime = Column(DateTime) 
    lastUpdateTime = Column(DateTime)
# }}}

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
        lstTypeObj.append( TypeToSqlTypeObject[coltype] )

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
            lstTypeObj.append( TypeToSqlTypeObject[coltype] )

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