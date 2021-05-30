from celery import Celery

# from configuration import celeryConfig
from celeryConfig import BaseConfig as celeryConfig

def _flask_context_task(app, TaskBase):
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
            
    return ContextTask

def make_celery(app,dicConfig):
    celery = Celery(app.import_name,
        backend=dicConfig.get("celery_result_backend"),
        broker=dicConfig.get("celery_broker"))
    celery.config_from_object(celeryConfig)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    
    print "====celeryApp===="
    print celery
    return celery

# celeryApp = make_celery()

#https://docs.celeryproject.org/en/latest/userguide/configuration.html?highlight=TIMEZONE#timezone
# def make_celery(app):
#     #https://docs.celeryproject.org/en/latest/userguide/configuration.html?highlight=TIMEZONE#timezone
#     print "~~~app.config~~~~"
#     print app.config
#     # celery = Celery(app.import_name,
#     #     backend=app.config['CELERY_RESULT_BACKEND'],
#     #     broker=app.config['CELERY_BROKER_URL'])
#     celery = Celery(app.import_name)
#     celery.conf.update(app.config)
#     TaskBase = celery.Task
#     class ContextTask(TaskBase):
#         abstract = True
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return TaskBase.__call__(self, *args, **kwargs)
#     celery.Task = ContextTask
#     return celery
