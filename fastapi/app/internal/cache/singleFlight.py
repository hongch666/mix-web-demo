import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class SingleFlight:
    """按键合并并发的回源任务，同一 key 同时只执行一个 loader

    语义与 go-zero 的 syncx.SingleFlight 对齐：
    1. 第一个调用者创建并执行 loader，其余同 key 调用者等待同一个结果
    2. loader 抛出的异常原样传播给所有等待者，不吞异常也不重试
    3. 等待方被取消只影响自己，不中断正在执行的回源任务（shield）
    4. 任务结束后立即释放 key，后续请求重新竞争，不缓存结果
    """

    def __init__(self) -> None:
        """初始化进行中的回源任务表，进程内单实例共享"""
        self._in_flight: dict[str, asyncio.Future[Any]] = {}

    async def do(self, key: str, loader: Callable[[], Awaitable[Any]]) -> Any:
        """按键执行回源：已有同 key 任务时等待其结果，否则创建并执行 loader"""
        pending: asyncio.Future[Any] | None = self._in_flight.get(key)
        if pending is not None:
            return await asyncio.shield(pending)

        future: asyncio.Future[Any] = asyncio.ensure_future(loader())
        self._in_flight[key] = future
        future.add_done_callback(lambda _: self._release(key, future))
        return await asyncio.shield(future)

    def _release(self, key: str, future: asyncio.Future[Any]) -> None:
        """任务结束后清理任务表并取走异常，避免等待方全部取消时 asyncio 告警"""
        if self._in_flight.get(key) is future:
            self._in_flight.pop(key, None)
        if not future.cancelled():
            future.exception()

    @property
    def in_flight(self) -> int:
        """当前进行中的回源任务数，供观测与测试断言使用"""
        return len(self._in_flight)
