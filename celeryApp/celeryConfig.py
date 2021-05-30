# -*- coding: utf-8 -*-
"""
==============================================================================
created    : 02/08/2021

Last update: 02/08/2021

Developer: Yishan Tsai

Lite Version 1 @Yishan08032019

Filename: celeryconfig.py

Description: about celery configuration
==============================================================================
"""
from kombu import Queue
class BaseConfig(object):
    CELERY_ACCEPT_CONTENT= ['json']
    CELERY_TASK_SERIALIZER= 'json'
    CELERY_RESULT_SERIALIZER= 'json'
    CELERY_ENABLE_UTC=True
    CELERY_TIMEZONE='Asia/Taipei'

    # CELERY_ACKS_LATE=True, #https://kknews.cc/zh-tw/code/5v5vj52.html
    CELERYD_PREFETCH_MULTIPLIER=1
    CELERYD_MAX_TASKS_PER_CHILD=50 #memory leak
    CELERY_IGNORE_RESULT=True
    CELERY_STORE_ERRORS_EVEN_IF_IGNORED=True
    CELERY_TASK_CREATE_MISSING_QUEUES=False
    CELERY_QUEUES = {
        # Queue("default", routing_key = "default"),
        # Queue("queue1", routing_key = "high", queue_arguments={'maxPriority': 10}), #https://github.com/squaremo/amqp.node/issues/165
        Queue("H-queue1", routing_key = "high"),
        Queue("L-queue1", routing_key = "low")
    }
    CELERY_TASK_ROUTES = {
        'celeryApp.celeryTasks.celery_trigger_specific_program': {'queue': 'H-queue1','routing_key':'high'},
        'celeryApp.celeryTasks.celery_post_api_count_record': {'queue': 'L-queue1','routing_key':'low'},
        'celeryApp.celeryTasks.celery_send_email': {'queue': 'L-queue1','routing_key':'low'},
    }

def readConfig():
    import os, time
    import ConfigParser
    from app.globalvar import CONFIG as _CONFIG
    try:
        get_request_start_time = int(round(time.time()* 1000000))

        if not os.path.isfile('/var/www/spdpaas/config/deconstants_{}.conf'.format(str(get_request_start_time))):
            with os.popen('/usr/bin/openssl enc -aes-128-cbc -d -in /var/www/spdpaas/config/encconstants.conf -out /var/www/spdpaas/config/deconstants_{}.conf -pass pass:sapidotest2019'.format(str(get_request_start_time))) as osdecrypt:
                osdecrypt.read()

        CONFPATH = "/var/www/spdpaas/config/deconstants_{}.conf".format(str(get_request_start_time))

        CONFIG = ConfigParser.ConfigParser()
        CONFIG.read(CONFPATH)

        dicConfig = {
            "celery_broker":CONFIG.get('Celery', 'broker'),
            "celery_result_backend":CONFIG.get('Celery', 'result_backend'),
            "dbpostgres_ip":CONFIG.get(_CONFIG["SYSTEM"]["POSTGRESQL"],'ip'),
            "dbpostgres_port":CONFIG.get(_CONFIG["SYSTEM"]["POSTGRESQL"],'port'),
            "dbpostgres_user":CONFIG.get(_CONFIG["SYSTEM"]["POSTGRESQL"],'user'),
            "dbpostgres_password":CONFIG.get(_CONFIG["SYSTEM"]["POSTGRESQL"],'password')
        }
        return dicConfig
    
    except Exception as e:
        print "~~~~celery config error~~~~"
        print e
        return False

    finally:
        if os.path.isfile('/var/www/spdpaas/config/deconstants_{}.conf'.format(str(get_request_start_time))):
            with os.popen('/bin/rm /var/www/spdpaas/config/deconstants_{}.conf'.format(str(get_request_start_time))) as osrm:
                osrm.read()