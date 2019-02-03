import time
import abc
import ujson
import uuid
from .session import SessionDict

class BaseSessionInterface(metaclass=abc.ABCMeta):
    # this flag show does this Interface need request/responce middleware hooks

    def __init__(self, expiry, prefix, cookie_name, domain, httponly, sessioncookie, samesite, session_name, secure, warn_lock):
        self.expiry = expiry
        self.prefix = prefix
        self.cookie_name = cookie_name
        self.domain = domain
        self.httponly = httponly
        self.sessioncookie = sessioncookie
        self.samesite = samesite
        self.session_name = session_name
        self.secure = secure
        self.warn_lock = warn_lock

    @staticmethod
    def _calculate_expires(expiry):
        expires = time.time() + expiry
        return time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(expires))

    def _del_cookie(self, request, response):
        response.cookies[self.cookie_name] = request[self.session_name].sid

        # We set expires/max-age even for session cookies to force expiration
        response.cookies[self.cookie_name]['expires'] = 0
        response.cookies[self.cookie_name]['max-age'] = 0

    def _set_cookie(self, request, response):
        response.cookies[self.cookie_name] = request[self.session_name].sid
        response.cookies[self.cookie_name]['httponly'] = self.httponly

        # Set expires and max-age unless we are using session cookies
        if not self.sessioncookie:
            response.cookies[self.cookie_name]['expires'] = self._calculate_expires(self.expiry)
            response.cookies[self.cookie_name]['max-age'] = self.expiry

        if self.domain:
            response.cookies[self.cookie_name]['domain'] = self.domain

        if self.samesite is not None:
            response.cookies[self.cookie_name]['samesite'] = self.samesite

        if self.secure is not None:
            response.cookies[self.cookie_name]['secure'] = self.secure

    @abc.abstractmethod
    async def _get_value(self, sid: str):
        '''
        Get value from datastore. Specific implementation for each datastore.

        Args:
            prefix:
                A prefix for the key, useful to namespace keys.
            sid:
                a uuid in hex string
        '''
        raise NotImplementedError

    @abc.abstractmethod
    async def _del_value(self, sid: str):
        '''Delete key from datastore'''
        raise NotImplementedError

    @abc.abstractmethod
    async def _set_value(self, sid: str, data: SessionDict):
        '''Set value for datastore'''
        raise NotImplementedError

    async def open(self, request) -> SessionDict:
        """
        Opens a session onto the request. Restores the client's session
        from the datastore if one exists.The session data will be available on
        `request.session`.


        Args:
            request (sanic.request.Request):
                The request, which a sessionwill be opened onto.

        Returns:
            SessionDict:
                the client's session data,
                attached as well to `request.session`.
        """
        sid = request.cookies.get(self.cookie_name)

        if not sid:
            sid = uuid.uuid4().hex
            session_dict = SessionDict(
                sid=sid,
                interface=self,
                warn_lock=self.warn_lock
            )
        else:
            val = await self._get_value(sid)

            if val is not None:
                data = ujson.loads(val)
                session_dict = SessionDict(
                    data,
                    sid=sid,
                    interface=self,
                    warn_lock=self.warn_lock
                )
            else:
                session_dict = SessionDict(
                    sid=sid,
                    interface=self,
                    warn_lock=self.warn_lock
                )

        # attach the session data to the request, return it for convenience
        request[self.session_name] = session_dict
        return session_dict

    async def save(self, request, response) -> None:
        """Saves the session to the datastore.

        Args:
            request (sanic.request.Request):
                The sanic request which has an attached session.
            response (sanic.response.Response):
                The Sanic response. Cookies with the appropriate expiration
                will be added onto this response.

        Returns:
            None
        """
        if 'session' not in request:
            return

        sid = request[self.session_name].sid
        if not request[self.session_name]:
            # Not going to check if session_dict.modified 
            # (Because it will be a real pain if you change a second layer dict,
            # e.g. request['session']['foo']['bar'] as opposed to request['session'['foo']
            # making the session_dict not update session_dict.modified to True and thus not 
            # reflecting that it was actually updated)
            await self._del_value(sid)

            if request[self.session_name].modified:
                self._del_cookie(request, response)
            return

        val = ujson.dumps(dict(request[self.session_name]))
        await self._set_value(sid, val)
        self._set_cookie(request, response)