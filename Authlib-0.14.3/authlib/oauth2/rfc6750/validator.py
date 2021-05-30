"""
    authlib.oauth2.rfc6750.validator
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Validate Bearer Token for in request, scope and token.
"""

import time
from ..rfc6749.util import scope_to_list
from .errors import (
    InvalidRequestError,
    InvalidTokenError,
    InsufficientScopeError
)


class BearerTokenValidator(object):
    TOKEN_TYPE = 'bearer'

    def __init__(self, realm=None):
        self.realm = realm

    def authenticate_token(self, token_string):
        """A method to query token from database with the given token string.
        Developers MUST re-implement this method. For instance::

            def authenticate_token(self, token_string):
                return get_token_from_database(token_string)

        :param token_string: A string to represent the access_token.
        :return: token
        """
        raise NotImplementedError()

    def request_invalid(self, request):
        """Check if the HTTP request is valid or not.  Developers MUST
        re-implement this method.  For instance, your server requires a
        "X-Device-Version" in the header::

            def request_invalid(self, request):
                return 'X-Device-Version' in request.headers

        Usually, you don't have to detect if the request is valid or not,
        you can just return a ``False``.

        :param request: instance of HttpRequest
        :return: Boolean
        """
        raise NotImplementedError()

    def token_revoked(self, token):
        """Check if this token is revoked. Developers MUST re-implement this
        method. If there is a column called ``revoked`` on the token table::

            def token_revoked(self, token):
                return token.revoked

        :param token: token instance
        :return: Boolean
        """
        raise NotImplementedError()

    def token_expired(self, token):
        #print "$$$$$token$$$$$$"
        #print token
        # #print token.__dict__
        # #print token.get_expires_at()
        # expires_at = token.get_expires_at()
        # if not expires_at:
        #     return False
        # #print expires_at < time.time()
        # return expires_at < time.time()

        #Yishan add
        if token:
            #print "False"
            return False
        #print "True"
        return True

    def scope_insufficient(self, token, scope, operator='AND'):
        #print "#####token######"
        #print token
        if not scope:
            return False
        #Yishan add
        token_scopes = scope_to_list(token.get("scope"))
        #print token_scopes
        # token_scopes = scope_to_list(token.get_scope())
        if not token_scopes:
            return True

        token_scopes = set(token_scopes)
        resource_scopes = set(scope_to_list(scope))
        if operator == 'AND':
            return not token_scopes.issuperset(resource_scopes)
        if operator == 'OR':
            return not token_scopes & resource_scopes
        if callable(operator):
            return not operator(token_scopes, resource_scopes)
        raise ValueError('Invalid operator value')

    def __call__(self, token_string, scope, request, scope_operator='AND'):
        if self.request_invalid(request):
            raise InvalidRequestError()
        #print "#####self.authenticate_token#####"
        token = self.authenticate_token(token_string)
        #print "#####self.authenticate_token#####"
        #print token
        #print "#####scope#####"
        #print scope
        if not token:
            raise InvalidTokenError(realm=self.realm)
        
        #Yishan del : already check expired or not
        # if self.token_expired(token):
        #     raise InvalidTokenError(realm=self.realm)

        if self.token_revoked(token):
            raise InvalidTokenError(realm=self.realm)
        if self.scope_insufficient(token, scope, scope_operator):
            raise InsufficientScopeError()
        return token
