import sys
import asyncio
from async_timeout import timeout

import pytest
import ujson

from sanic_session.base import BaseSessionInterface
from sanic_session.session import SessionDict, lock_keeper, LockKeeper
from sanic_session import Session, InMemorySessionInterface


class MockInterface:
    store = {}

    async def _get_value(self, sid):
        return self.store.get(sid)

    async def _set_value(self, sid, data):
        self.store[sid] = data

mock_interface = MockInterface()
inmemory_session_interface = InMemorySessionInterface()

@pytest.mark.asyncio
@pytest.mark.parametrize('interface', [mock_interface, inmemory_session_interface])
async def test_session_dict_locked_by_sid(interface):
    SID = 'an_sid'

    session_dict = SessionDict(sid=SID, interface=interface)
    async with session_dict as sess:
        assert lock_keeper.acquired_locks[SID].locked() is True
        sess['foo'] = 'bar'
        assert sess['foo'] == 'bar'

    assert ujson.loads(
        await interface._get_value(SID)
    )['foo'] == 'bar'

    async with session_dict as sess:
        assert sess['foo'] == 'bar'
    assert lock_keeper.acquired_locks[SID].locked() is False

@pytest.mark.asyncio
@pytest.mark.parametrize('interface', [mock_interface, inmemory_session_interface])
async def test_warns_with_unlocked_access(interface):
    SID = 'another_sid'

    session_dict = SessionDict(sid=SID, interface=interface, warn_lock=True)
    with pytest.warns(RuntimeWarning):
        session_dict['foo'] = 'bar'

    with pytest.warns(RuntimeWarning):
        session_dict['foo']

@pytest.mark.asyncio
@pytest.mark.parametrize('interface', [mock_interface, inmemory_session_interface])
async def test_awaits_locked_session_dict(interface):
    SID = 'yet_another_sid'

    session_dict = SessionDict(sid=SID, interface=interface)

    lock = asyncio.Lock()
    await lock.acquire()

    lock_keeper.acquired_locks[SID] = lock

    assert lock_keeper.acquired_locks[SID].locked() is True

    assert len(lock_keeper.acquired_locks[SID]._waiters) == 0

    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.1):
            async with session_dict:
                session_dict['asd']
                assert len(lock_keeper.acquired_locks[SID]._waiters) == 1
