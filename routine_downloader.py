import asyncio
import aiohttp
import requests

from time import sleep
from collections import deque

RED = '\033[91m'
GREEN = '\033[32m'
RESET = '\033[0m'
BLUE = '\033[94m'

DEBUG = False
REQUEST_INTERVAL = 1

class Downloader:
    def __init__(self) -> None:
        self.tasks = deque()
        self.failds = []
        self.successs = []
        self.request_interval = REQUEST_INTERVAL

    def add_task(self, url, callback):
        self.tasks.append((url, callback, False))
    
    async def worker(self, worder_id):
        async with aiohttp.ClientSession() as session:
            while len(self.tasks):
                task = self.tasks.popleft()
                url = task[0]
                cb = task[1]
                try:
                    async with session.get(url) as resp:
                        if DEBUG:
                            print(f'{BLUE}downloaded [{url}]{RESET}')
                        resp.raise_for_status()
                        try:
                            await cb(resp)
                            self.successs.append(task)
                        except Exception as e:
                            print(f'{RED}[worker: {worder_id}]: error when call callback for url [{url}]: {e}{RESET}')
                            self.failds.append(task)
                except Exception as e:
                    print(f'{RED}[worker: {worder_id}]: error when download url [{url}]: {e}{RESET}')
                    self.failds.append(task)

    def download_async(self, worker_n=10):
        print(f'start downloading with corotines: {worker_n}')
        async def f():
            workers = []
            for i in range(worker_n):
                workers.append(asyncio.create_task(self.worker(i)))
            for worker in workers:
                await worker
        asyncio.run(f())
    
    def download(self):
        while len(self.tasks):
            task = self.tasks.popleft()
            url = task[0]
            cb = task[1]
            try:
                resp = requests.get(url)
                resp.raise_for_status()
                if DEBUG:
                    print(f'{BLUE}downloaded [{url}]{RESET}')
                try:
                    cb(resp)
                    self.successs.append(task)
                except Exception as e:
                    print(f'{RED}error when call callback for url [{url}]: {e}{RESET}')
                    self.failds.append(task)
            except Exception as e:
                print(f'{RED}error when download url [{url}]: {e}{RESET}')
                self.failds.append(task)
            sleep(self.request_interval)