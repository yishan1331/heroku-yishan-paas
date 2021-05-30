from authlib.oauth2.rfc6750 import BearerToken
from authlib.oauth2.rfc6749.errors import InvalidClientError
import json

def create_query_client_func(session, client_model):
    """Create an ``query_client`` function that can be used in authorization
    server.

    :param session: SQLAlchemy session
    :param client_model: Client model class
    """
    def query_client(client_id):
        #print "............"
        q = session.query(client_model)
        return q.filter_by(client_id=client_id).first()
    return query_client

def create_save_token_func(session, token_model, client_model, Yishan_dbRedis):
    """Create an ``save_token`` function that can be used in authorization
    server.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    def save_token(token, request):
        # if request.user:
        #     system_id = request.user.get_system_id()
        # else:
        #     system_id = None
        #print "~~~~~~~~~save_token~~~~~~~~~~~"
        #print token
        #print request.__dict__
        client = request.client
        item = token_model(
            client_id=client.client_id,
            system_id=client.system_id,
            **token
        )
        #print token
        #print "******save_tokensave_tokensave_tokensave_token******"
        session.add(item)
        #Yishan add update sub_account_counts +1
        q = session.query(client_model).filter(client_model.client_id == client.client_id,client_model.client_secret == client.client_secret)
        q.update({client_model.sub_account_counts : client_model.sub_account_counts + 1})
        #print item.__dict__
        #print item._sa_instance_state.__dict__
        session.commit()
        #print "99999999999save_tokensave_tokensave_tokensave_token99999999"

        thisscope = ""
        if request.data.get("scope"):
            thisscope = request.data.get("scope")
        #print "~~~~thisscope~~~~"
        #print thisscope
        redis_value = {
            "client_id":client.client_id,
            "system_id":client.system_id,
            "scope":thisscope,
            "client_id_issued_at":client.client_id_issued_at,
            "client_secret_expires_at":client.client_secret_expires_at,
            "revoked":0
        }
        redis_value.update(token)
        #print "redis_value------>",redis_value
        #Yishan set token in Redis 
        import json
        Yishan_dbRedis.setex(token["access_token"], BearerToken.GRANT_TYPES_EXPIRES_IN.get("client_credentials"), json.dumps(redis_value))

    return save_token


def create_query_token_func(session, token_model):
    """Create an ``query_token`` function for revocation, introspection
    token endpoints.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    def query_token(token, token_type_hint, client):
        q = session.query(token_model)
        q = q.filter_by(client_id=client.client_id, revoked=False)
        if token_type_hint == 'access_token':
            return q.filter_by(access_token=token).first()
        elif token_type_hint == 'refresh_token':
            return q.filter_by(refresh_token=token).first()
        # without token_type_hint
        item = q.filter_by(access_token=token).first()
        if item:
            return item
        return q.filter_by(refresh_token=token).first()
    return query_token


def create_revocation_endpoint(session, token_model, Yishan_dbRedis):
    """Create a revocation endpoint class with SQLAlchemy session
    and token model.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    from authlib.oauth2.rfc7009 import RevocationEndpoint
    query_token = create_query_token_func(session, token_model)

    class _RevocationEndpoint(RevocationEndpoint):
        def query_token(self, token, token_type_hint, client):
            return query_token(token, token_type_hint, client)

        def revoke_token(self, token):
            #mysql
            token.revoked = True
            session.add(token)
            session.commit()
            #redis
            #Yishan add to update redis token key's value:revoked
            if Yishan_dbRedis.exists(token.access_token):
                redis_value = json.loads(Yishan_dbRedis.get(token.access_token))
                redis_value["revoked"] = 1
                Yishan_dbRedis.setex(token.access_token, Yishan_dbRedis.ttl(token.access_token), json.dumps(redis_value))

    return _RevocationEndpoint

def create_bearer_token_validator(session, token_model, client_model, Yishan_dbRedis):
    """Create an bearer token validator class with SQLAlchemy session
    and token model.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    from authlib.oauth2.rfc6750 import BearerTokenValidator

    class _BearerTokenValidator(BearerTokenValidator):
        def authenticate_token(self, token_string):
            isExisted = False
            #is Expired
            if Yishan_dbRedis.exists(token_string):
                isExisted = True
            
            if isExisted:
                this_token = json.loads(Yishan_dbRedis.get(token_string))
                #Yishan add token existed need to check client secret is legal
                import time
                if this_token["client_id_issued_at"]+this_token["client_secret_expires_at"] < time.time():
                    self._client_token_expired(this_token["system_id"],token_string)
                    raise InvalidClientError(state=None, status_code=400)
                
                return json.loads(Yishan_dbRedis.get(token_string))
            else:
                #Yishan add update sub_account_counts -1
                system_id = session.query(token_model.system_id).filter_by(access_token=token_string).first()
                if system_id: self._client_token_expired(system_id[0],token_string)

        def request_invalid(self, request):
            return False

        def token_revoked(self, token):
            #Yishan add
            return token["revoked"]
            # return token.revoked
        
        def _client_token_expired(self,system_id,token_string):
            session.query(client_model).filter(client_model.system_id == system_id).update({client_model.sub_account_counts : client_model.sub_account_counts - 1})
            session.query(token_model).filter_by(access_token=token_string).delete()
            session.commit()
            if Yishan_dbRedis.exists(token_string): Yishan_dbRedis.delete(token_string)
            #print "<><><><><>_client_token_expired<><><><><>"

    return _BearerTokenValidator

def update_client_secret_func(session, client_model):

    def update_client_secret(request):
        # if request.user:
        #     system_id = request.user.get_system_id()
        # else:
        #     system_id = None
        import time
        #print "~~~~~~~~~update_secret~~~~~~~~~~~"
        #print request.__dict__
        #print "~~~~client_model~~~~~"
        #print client_model
        client = request.client
        q = session.query(client_model).filter(client_model.client_id == client.client_id,client_model.client_secret == client.client_secret)
        #print "~~~~~Q~~~~~~"
        #print q
        q.update({client_model.client_id_issued_at : int(time.time()),client_model.client_secret_update_times : client_model.client_secret_update_times + 1})
        session.commit()
        #print "~~~~~commit~~~~~"
    return update_client_secret