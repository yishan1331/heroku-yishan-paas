# -*- coding: utf-8 -*-
#Description
"""
==============================================================================
created    : 07/17/2020

Last update: 07/17/2020

Developer: Yishan Tsai 

Lite Version 1 @Yishan05212020

Filename: globalvar.py

Description: global variable
==============================================================================
"""

SERVERIP = "serverYS"

#支援使用的系統列表
SYSTEMLIST = {
    "server71": ["IOT","APIDOC"],
    "server75": ["SAPIDOSYSTEM","OQA","CRM","APIDOC"],
    "serverKSS": ["OQA","APIDOC"],
    "serverCZ": ["CHUNZU","APIDOC"],
    "serverYS": ["YS"]
}

#PaaS是否為container
ISCONTAINER = True
CONTAINER_API_HTML = "API"

PAAS_DASHBOARD_DBNAME = {
    "MYSQL":"w4gs1cezebsazytb",
    "POSTGRES":"de1rijvqmjhsgr",
}
#------------------------------------------------------
#Wei@10022018 adding the if-else for customer check
#For runnable version, the uid check for administor 
# of service, should be added to the database and set it up 
# when deployed to client
#支援使用uid列表
#---------------------------------------------------------
XXXUSER = {
    "server71": ["@sapido@PaaS","AOItest"],
    "server75": ["@sapido@PaaS"],
    "serverKSS": ["@sapido@PaaS"],
    "serverCZ": ["@sapido@PaaS"],
    "serverYS": ["@YS@PaaS"]
}
#各資料庫固定時間欄位
CREATETIME = {
    "server71": {"mysql":"created_at","mssql":"created_at"},
    "server75": {"mysql":"createTime","mssql":"created_at"},
    "serverKSS": {"mysql":"createTime","mssql":"created_at"},
    "serverCZ": {"mysql":"created_at","mssql":"created_at"},
    "serverYS": {"mysql":"createTime","mssql":"created_at"}
}
UPLOADTIME = {
    "server71": {"mysql":"updated_at","mssql":"update_at","postgres":"upload_at"},
    "server75": {"mysql":"lastUpdateTime","postgres":"upload_at","mssql":"update_at"},
    "serverKSS": {"mysql":"lastUpdateTime","postgres":"upload_at","mssql":"update_at"},
    "serverCZ": {"mysql":"updated_at","mssql":"update_at","postgres":"upload_at"},
    "serverYS": {"mysql":"lastUpdateTime","mssql":"update_at","postgres":"upload_at"}
}
MYSQL_USER_ID = {
    "server71": "user_id",
    "server75": "uID",
    "serverCZ": "user_id",
    "serverYS": "uID"
}

#logging模組要查看的log file列表
LOGFILELIST = {"uWSGI_LOG":{"filename":"spdpaas_uwsgi.log","path":"/var/log/uwsgi/"},"PaaS_LOG":{"filename":"log_sapidoPaaS","path":"/var/www/spdpaas/log/"}}

#SqlSyntax api的條件參數
SQLSYNTAX_PARAMETER = {"table":str,"fields":list,"where":dict,"orderby":list,"limit":list,"symbols":dict,"intervaltime":dict,"subquery":dict,"union":list}
JOIN_SQLSYNTAX_PARAMETER = {"tables":list,"fields":dict,"where":dict,"join":dict,"jointype":dict,"orderby":list,"limit":list,"symbols":dict,"subquery":dict}
SQLSYNTAX_OPERATOR = ["equal","notequal","greater","less","leftlike","notleftlike","leftlikein","leftlikenotin","like","notlike","likein","likenotin","rightlike","notrightlike","rightlikein","rightlikenotin","in","notin"]
SQLSYNTAX_SUBQUERY_OPERATOR = ["equal","notequal","greater","less","in","notin"]

#readConfig參數
DBCONFIG = {
    "MYSQL":"DBMYSQL",
    "POSTGRESQL":"DBPOSTGRES",
    "REDIS":"DBREDIS",
    "MSSQL":"DBMSSQL"
}
CONFIG = {
    #diff ip dbname
    "server71": {
        "IOT":{
            "MYSQL":["Mysql_IOT"],
            "MSSQL":["Mssql_IOT"]
        }
    },
    "server75": {
        "SAPIDOSYSTEM":{
            "MYSQL":["Mysql_SAPIDOSYSTEM"],
            "Email":"Email"
        },
        "OQA":{
            "MSSQL":["Mssql_OQA","Mssql_OQAdev"]
        },
        "CRM":{
            "MSSQL":["Mssql_CRM"]
        }
    },
    "serverKSS": {
        "OQA":{
            "MYSQL":["Mysql_OQA"],
            "MSSQL":["Mssql_OQA","Mssql_IOT"]
        }
    },
    "serverCZ": {
        "CHUNZU":{
            "MYSQL":["Mysql_CHUNZU"],
            "POSTGRESQL":["Postgresql_CHUNZU"],
            "REDIS":["Redis_CHUNZU"],
            "Email":"Email"
        }
    },
    "serverYS": {
        "YS":{
            "MYSQL":["Mysql_YS"],
            "POSTGRESQL":["Postgresql_YS"],
            "REDIS":["Redis_YS"],
            "Email":"Email"
        }
    }
}

__all__ = [
    'SERVERIP', 'SYSTEMLIST' , 'XXXUSER',
    'CREATETIME', 'UPLOADTIME', 'LOGFILELIST',
    'SQLSYNTAX_PARAMETER', 'JOIN_SQLSYNTAX_PARAMETER',
    'SQLSYNTAX_OPERATOR', 'DBCONFIG', 'CONFIG'
]