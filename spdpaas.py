#assign app from sessionMgr
print "-----into spdpaas.py-----"
# from app import *
# appSapido = appPaaS
# import app.apiPortal

from flask import Flask, request, jsonify, Blueprint
appPaaS = Flask('YishanPaaS')

@appPaaS.route("/")
def homePage():
    dicRet = {}
    mesg = "<h1 style='color:blue'>sapido-PaaS!</h1>"
    dicRet["message"] = mesg    
    dicRet["APIS"] = "{} {}".format(request.method,request.path) 
    dicRet["Response"] = "ok" 
    return jsonify( **dicRet)

# if __name__ == "__main__":
#     print "-----spdpaas.py __main__-----"
#     appSapido.run()