import asyncio

import pytest

from app.internal.cache import SingleFlight


# 同 key 并发调用只执行一次 loader，所有调用方拿到同一结果
@pytest.mark.anyio
async def test_do_merges_concurrent_calls_for_same_key() -> None:
    flight = SingleFlight()
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def loader() -> str:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return "value"

    first = asyncio.create_task(flight.do("k", loader))
    await started.wait()
    second = asyncio.create_task(flight.do("k", loader))
    await asyncio.sleep(0)
    release.set()

    assert await asyncio.gather(first, second) == ["value", "value"]
    assert calls == 1
    assert flight.in_flight == 0


# 不同 key 互不合并，各自执行自己的 loader
@pytest.mark.anyio
async def test_do_keeps_different_keys_independent() -> None:
    flight = SingleFlight()
    started = asyncio.Event()
    release = asyncio.Event()
    calls: list[str] = []

    async def loader(name: str) -> str:
        calls.append(name)
        started.set()
        await release.wait()
        return name

    first = asyncio.create_task(flight.do("a", lambda: loader("a")))
    second = asyncio.create_task(flight.do("b", lambda: loader("b")))
    await started.wait()
    await asyncio.sleep(0)
    release.set()

    assert await asyncio.gather(first, second) == ["a", "b"]
    assert calls == ["a", "b"]


# 任务结束后释放 key，后续调用重新执行 loader，不复用历史结果
@pytest.mark.anyio
async def test_do_releases_key_after_completion() -> None:
    flight = SingleFlight()
    calls = 0

    async def loader() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert await flight.do("k", loader) == 1
    assert await flight.do("k", loader) == 2
    assert calls == 2
    assert flight.in_flight == 0


# loader 异常原样传播给所有等待者，并在结束后释放 key
@pytest.mark.anyio
async def test_do_propagates_loader_error_to_all_waiters() -> None:
    flight = SingleFlight()
    started = asyncio.Event()
    release = asyncio.Event()

    async def loader() -> str:
        started.set()
        await release.wait()
        raise RuntimeError("db down")

    first = asyncio.create_task(flight.do("k", loader))
    await started.wait()
    second = asyncio.create_task(flight.do("k", loader))
    await asyncio.sleep(0)
    release.set()

    results = await asyncio.gather(first, second, return_exceptions=True)

    assert all(isinstance(item, RuntimeError) for item in results)
    assert flight.in_flight == 0


# 等待方被取消不会中断正在执行的回源任务，首个调用方仍能拿到结果
@pytest.mark.anyio
async def test_do_keeps_loader_running_when_waiter_cancelled() -> None:
    flight = SingleFlight()
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def loader() -> str:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return "done"

    owner = asyncio.create_task(flight.do("k", loader))
    await started.wait()
    waiter = asyncio.create_task(flight.do("k", loader))
    await asyncio.sleep(0)

    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter

    release.set()

    assert await owner == "done"
    assert calls == 1
    assert flight.in_flight == 0
