import asyncio
import aiohttp

class RoutineDownloader:
    def __init__(self) -> None:
        tasks = []

    def add_task(self, url, callback):
        self.tasks.append((url, callback))

    async def _run(self):
        async with aiohttp.ClientSession() as session:
            for url, callback in self.tasks:
                async with session.get(url) as response:
                    await callback(response)
    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run())

