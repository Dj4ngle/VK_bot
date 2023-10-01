import asyncio, typing

from kts_backend.store import Store
from kts_backend.store.vk_api.dataclasses import UpdateObject


class Worker:
    def __init__(self, store: Store, queue: asyncio.Queue, n: int):
        self.store = store
        self.queue = queue
        self.is_running = False
        self.n = n
        self._tasks: typing.List[asyncio.Task] = []

    async def worker(self, worker_id):
        while self.is_running:
            u: UpdateObject = await self.queue.get()
            print(f"Worker {worker_id} is processing update: {u}")
            await self.store.bots_manager.handle_updates(u)
            self.queue.task_done()

    async def start(self):
        print("worker started")
        self.is_running = True
        for i in range(self.n):
            task = asyncio.create_task((self.worker(i)))
            self._tasks.append(task)

    async def stop(self):
        print("worker stoped")
        self.is_running = False
        await self.queue.join()
        for t in self._tasks:
            t.cancel()