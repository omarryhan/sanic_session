from asyncio import Lock
import warnings

import ujson

__all__ = []


UNLOCKED_WARNING_MSG = '''
    Updating or reading from session store without acquiring a lock for session ID.
    To avoid race conditions, please use the session dict as follows:

        async with request['session']:
            value_to_read = request['session']['a_key']
            request['session']['a_key'] = 'value_to_write'

    instead of:

        request['session']['a_key']
''', RuntimeWarning

class _Missing(object):
    """
    Copyright (c) 2015 by Armin Ronacher and contributors.  See AUTHORS
    in FLASK_LICENSE for more details.
    """
    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()


class UpdateDictMixin(object):
    """
    Copyright (c) 2015 by Armin Ronacher and contributors.  See AUTHORS
    in FLASK_LICENSE for more details.
    """

    def calls_update(name):
        def oncall(self, *args, **kw):
            if self.is_locked() is not True and self.warn_lock is True:
                warnings.warn(*UNLOCKED_WARNING_MSG)
            rv = getattr(super(UpdateDictMixin, self), name)(*args, **kw)
            if self.on_update is not None:
                self.on_update()
            return rv
        oncall.__name__ = name
        return oncall

    def __getitem__(self, *args, **kwargs):
        if self.is_locked() is not True and self.warn_lock is True:
            warnings.warn(*UNLOCKED_WARNING_MSG)
        return super().__getitem__(*args, **kwargs)

    def setdefault(self, key, default=None):
        modified = key not in self
        rv = super(UpdateDictMixin, self).setdefault(key, default)
        if modified and self.on_update is not None:
            self.on_update()
        return rv

    def pop(self, key, default=_missing):
        modified = key in self
        if default is _missing:
            rv = super(UpdateDictMixin, self).pop(key)
        else:
            rv = super(UpdateDictMixin, self).pop(key, default)
        if modified and self.on_update is not None:
            self.on_update()
        return rv

    __setitem__ = calls_update('__setitem__')
    __delitem__ = calls_update('__delitem__')
    clear = calls_update('clear')
    popitem = calls_update('popitem')
    update = calls_update('update')
    del calls_update


class LockKeeper:
    acquired_locks = {}

    async def acquire(self, sid):
        existing_lock = self.acquired_locks.get(sid)
        if existing_lock:
            await existing_lock.acquire()
        else:
            new_lock = Lock()
            await new_lock.acquire()
            self.acquired_locks[sid] = new_lock

    def release(self, sid):
        existing_lock = self.acquired_locks.get(sid)
        if existing_lock:
            existing_lock.release()
            #del self.acquired_locks[sid]

lock_keeper = LockKeeper()


class SessionDict(UpdateDictMixin, dict):
    def __init__(self, initial=None, sid=None, interface=None, warn_lock=True):
        dict.__init__(self, initial or ())

        self.sid = sid
        self.modified = False

        self.warn_lock = warn_lock
        self.interface = interface

    def is_locked(self):
        if self.sid in lock_keeper.acquired_locks:
            return lock_keeper.acquired_locks[self.sid].locked()
        else:
            return False

    def on_update(self):
        self.modified = True

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            dict.__repr__(self)
        )

    async def __aenter__(self):
        await lock_keeper.acquire(self.sid)
        assert self.is_locked() is True
        initial = await self.interface._get_value(sid=self.sid)
        initial = ujson.loads(initial) if initial is not None else initial
        dict.__init__(self, initial or ())
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        # Save value to store
        val = ujson.dumps(dict(self))
        await self.interface._set_value(sid=self.sid, data=val)
        lock_keeper.release(self.sid)
        assert self.is_locked() is False