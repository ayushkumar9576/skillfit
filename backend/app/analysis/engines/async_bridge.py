"""Run synchronous engine entry points on one reusable worker event loop.

Async callers should normally await analyze_async(). The sync API also works
from notebooks and async callers, without nesting asyncio.run() in their loop.
"""

import asyncio
import atexit
from threading import Event, Lock, Thread
from typing import Callable, Coroutine, Any, TypeVar

T = TypeVar("T")
_lock = Lock()
_loop = None
_thread = None


def _worker_loop():
    global _loop, _thread
    with _lock:
        if _loop is None:
            ready = Event()
            def start():
                global _loop
                _loop = asyncio.new_event_loop()
                asyncio.set_event_loop(_loop)
                ready.set()
                _loop.run_forever()
                _loop.close()
            _thread = Thread(target=start, name="resume-analysis", daemon=True)
            _thread.start()
            ready.wait()
        return _loop


def run_sync(factory: Callable[[], Coroutine[Any, Any, T]]) -> T:
    loop = _worker_loop()
    try:
        current = asyncio.get_running_loop()
    except RuntimeError:
        current = None
    if current is loop:
        raise RuntimeError("Inside the engine worker, await analyze_async() instead.")
    return asyncio.run_coroutine_threadsafe(factory(), loop).result()


@atexit.register
def _shutdown():
    if _loop is None or _loop.is_closed():
        return
    async def cancel_pending():
        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await _loop.shutdown_asyncgens()
    try:
        asyncio.run_coroutine_threadsafe(cancel_pending(), _loop).result(timeout=5)
    finally:
        _loop.call_soon_threadsafe(_loop.stop)
        _thread.join(timeout=5)
