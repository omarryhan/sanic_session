from sanic_session.base import BaseSessionInterface

try:
    import aioredis
except ImportError:
    aioredis = None


class AIORedisSessionInterface(BaseSessionInterface):
    def __init__(
            self, redis,
            domain: str=None, expiry: int = 2592000,
            httponly: bool=True, cookie_name: str='session',
            prefix: str='session:',
            sessioncookie: bool=False, samesite: str=None,
            session_name: str='session', secure: bool=None,
            warn_lock: bool=True):
        """Initializes a session interface backed by Redis.

        Args:
            redis (Callable):
                aioredis connection or connection pool instance.
            domain (str, optional):
                Optional domain which will be attached to the cookie.
            expiry (int, optional):
                Seconds until the session should expire.
            httponly (bool, optional):
                Adds the `httponly` flag to the session cookie.
            cookie_name (str, optional):
                Name used for the client cookie.
            prefix (str, optional):
                Memcache keys will take the format of `prefix+session_id`;
                specify the prefix here.
            sessioncookie (bool, optional):
                Specifies if the sent cookie should be a 'session cookie', i.e
                no Expires or Max-age headers are included. Expiry is still
                fully tracked on the server side. Default setting is False.
            samesite (str, optional):
                Will prevent the cookie from being sent by the browser to the target
                site in all cross-site browsing context, even when following a regular link.
                One of ('lax', 'strict')
                Default: None
            session_name (str, optional):
                Name of the session that will be accessible through the request.
                e.g. If ``session_name`` is ``alt_session``, it should be accessed like that: ``request['alt_session']``
                e.g. And if ``session_name`` is left to default, it should be accessed like that: ``request['session']``
                Default: 'session'
            secure (bool, optional):
                Whether or not the cookie should be secure (HTTP(S) only)
            warn_lock (bool, optional):
                Set to False to turn off session_dict lock warning (Not recommended)
                Default: True
        """
        if aioredis is None:
            raise RuntimeError("Please install aioredis: pip install sanic_session[aioredis]")

        self.redis = redis

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

    async def _get_value(self, sid):
        return await self.redis.get(self.prefix + sid)

    async def _del_value(self, sid):
        await self.redis.delete(self.prefix + sid)

    async def _set_value(self, sid, data):
        await self.redis.setex(self.prefix + sid, self.expiry, data)

