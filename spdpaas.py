#assign app from sessionMgr
print "-----into spdpaas.py-----"
from app import *
import app.apiPortal

socketio.run(appPaaS,debug=True)

# if __name__ == "__main__":
#     print "-----spdpaas.py __main__-----"
#     appSapido.run()