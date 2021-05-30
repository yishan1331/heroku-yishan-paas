#assign app from sessionMgr
from app import *
appSapido = appPaaS
import app.apiPortal

if __name__ == "__main__":
    print "-----spdpaas.py __main__-----"
    appSapido.run()