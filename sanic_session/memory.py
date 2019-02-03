from sanic_session.base import BaseSessionInterface
from typing import Union, Any
import time


class ExpiringDict(dict):
    def __init__(self, prefix=''):
        self.prefix = prefix
        super().__init__()
        self.expiry_times = {}

    def set(self, key: Union[str, int], val: Any, expiry: int):
        self[key] = val
        self.expiry_times[key] = time.time() + expiry

    def get_by_sid(self, key: str):
        key = self.prefix + key
        return self.get(key)

    def get(self, key: Union[str, int]):
        data = dict(self).get(key)

        if not data:
            return None

        if time.time() > self.expiry_times[key]:
            del self[key]
            del self.expiry_times[key]
            return None

        return data

    def delete(self, key: Union[str, int]):
        del self[key]
        del self.expiry_times[key]

class InMemorySessionInterface(BaseSessionInterface):
    def __init__(
            self, domain: str=None, expiry: int = 2592000,
            httponly: bool=True, cookie_name: str = 'session',
            prefix: str='session:',
            sessioncookie: bool=False, samesite: str=None,
            session_name='session', secure: bool=None,
            warn_lock: bool=True):

        super().__init__(
            expiry=expiry,
            prefix=prefix,
            cookie_name=cookie_name,
            domain=domain,
            httponly=httponly,
            sessioncookie=sessioncookie,
            samesite=samesite,
            session_name=session_name,
            secure=secure,
            warn_lock=warn_lock
        )
        self.session_store = ExpiringDict()

    async def _get_value(self, sid):
        return self.session_store.get(self.prefix + sid)

    async def _del_value(self, sid):
        key = self.prefix + sid
        if key in self.session_store:
            self.session_store.delete(key)

    async def _set_value(self, sid, data):
        key = self.prefix + sid
        self.session_store.set(
            key, data,
            self.expiry
        )
