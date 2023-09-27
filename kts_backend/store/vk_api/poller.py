import asyncio
from asyncio import Task

from kts_backend.store import Store

class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Task | None = None

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        self.is_running = False
        await self.poll_task
        #self.poll_task.cancel()

    async def poll(self):
        while self.is_running:
            await self.store.vk_api.poll()