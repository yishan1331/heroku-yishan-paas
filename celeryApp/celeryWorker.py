from celery import Celery

from celeryConfig import BaseConfig as celeryConfig
from celeryConfig import readConfig

def celery_worker():
    print "======celery_worker========"
    dicConfig = readConfig()
    celery = Celery("sapidoPaaS",
        backend=dicConfig.get("celery_result_backend"),
        broker=dicConfig.get("celery_broker"),
        include=["celeryApp.celeryTasks"])
    celery.config_from_object(celeryConfig)
    print "======celery_worker end========"
    print celery
    return celery

celery = celery_worker()

# from celery.signals import worker_process_init, worker_process_shutdown

# db_conn = None

# @worker_process_init.connect
# def init_worker(**kwargs):
#     global db_conn
#     print('Initializing database connection for worker.')
#     DbSessionRaw,metaRaw,engineRaw = appPaaS.getDbSessionType(dbName=dbName, forRawData="postgres", system=system)


#     db_conn = db.connect(DB_CONNECT_STRING)


# @worker_process_shutdown.connect
# def shutdown_worker(**kwargs):
#     global db_conn
#     if db_conn:
#         print('Closing database connectionn for worker.')
#         db_conn.close()

celery.start()

# import apiPortal

__all__ = ['celery']