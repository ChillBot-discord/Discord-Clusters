import asyncio
from asyncio.subprocess import DEVNULL, PIPE
from datetime import datetime
import aiohttp
import sys
import signal

if sys.platform == 'win32':  # asyncio subprocesses only support this
    asyncio.set_event_loop(asyncio.ProactorEventLoop())
    
    
TOKEN = "insert bot token here"


async def get_shard_count():
    """async with aiohttp.ClientSession() as s, s.get(
        "https://discordapp.com/api/v7/gateway/bot", headers={
                "Authorization": f'Bot {TOKEN}',
                'User-Agent': 'DiscordBot (https://github.com/Rapptz/discord.py 1.3.0a) Python/3.7 aiohttp/3.5.4'
            }
    ) as g:
        data = await g.json()
    return data.get('shards')"""
    return 16  # temp


NAMES = iter([
    'Alpha', 'Beta', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf', 'Hotel',
    'India', 'Juliett', 'Kilo', 'Mike', 'November', 'Oscar', 'Papa', 'Quebec',
    'Romeo', 'Sierra', 'Tango', 'Uniform', 'Victor', 'Whisky', 'X-ray', 'Yankee', 'Zulu'
])


def get_cluster_name():
    return next(NAMES)


def get_cluster_shards(max_shard_count):
    for i in range(0, max_shard_count, 4):
        yield [x+i for x in range(4)]


class Cluster:
    def __init__(self, launcher, *shard_ids, shard_count, name, loop=None):
        self.shards = shard_ids
        self.process = None
        self.cmd = f"{sys.executable} bot.py \"{list(shard_ids)}\" {shard_count} \"{name}\""
        self.loop = loop or asyncio.get_event_loop()
        self.name = name
        self.launcher = launcher
        self.start_count = 0
        self.is_alive = False
        self.loop.create_task(self.start())

    async def run_until_complete(self):
        stdout, stderr = await self.process.communicate()
        self.is_alive = False
        return self, stderr

    async def start(self):
        if self.is_alive:
            print(f"[Cluster#{self.name}] Cannot start() since already alive.")
            return
        self.process = await asyncio.create_subprocess_shell(
            self.cmd,
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=PIPE,
            loop=self.loop
        )
        t = self.loop.create_task(self.run_until_complete())
        print(f"[Cluster#{self.name}] Process Started with PID {self.process.pid}")
        t.add_done_callback(self.launcher.process_dead)
        self.start_count += 1
        self.is_alive = True

    async def stop(self):
        print(f'[Cluster#{self.name}] Stopping')
        self.process.send_signal(signal.SIGTERM)
        await asyncio.sleep(20)
        if self.is_alive:
            print(f'[Cluster#{self.name}] Forcefully closing.')
            self.process.send_signal(signal.SIGKILL)
            print(f"[Cluster#{self.name}] Closed forcefully.")
            return
        print(f"[Cluster#{self.name}] Closed gracefully.")


class Launcher:
    def __init__(self, loop):
        self.loop = loop
        self.clusters = []
        self.ipc = None

    async def start(self, loop):
        shard_count = await get_shard_count()
        for cluster_shards in get_cluster_shards(shard_count):
            c = Cluster(self, *cluster_shards, name=get_cluster_name(), loop=self.loop, shard_count=shard_count)
            self.clusters.append(c)
            print(f"[Launcher] Initialized cluster {c.name}")
            await asyncio.sleep(20)
        print(f'[Launcher] Initialized {len(self.clusters)} clusters.')

    def process_dead(self, result):
        exit_time = datetime.utcnow().strftime('%m-%d-%y_%H-%M-%S')
        cluster, stderr = result.result()
        print(f'[Cluster#{cluster.name}] Process stopped: {cluster.process.returncode}')
        if cluster.process.returncode != 0 and cluster.process.returncode != -15:
            with open(f"cluster-{cluster.name}-err-{exit_time}.txt", "wb") as f:
                f.write(stderr)
            print(f'[Cluster#{cluster.name}] wrote stderr to `cluster-{cluster.name}-err-{exit_time}.txt')
            # cluster.loop.create_task(cluster.start())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    launcher = Launcher(loop)
    loop.create_task(launcher.start(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print(f'[Launcher] Shutting down')

        def shutdown_handler(_loop, ctx):
            if 'exception' not in ctx or not isinstance(ctx['exception'], asyncio.CancelledError):
                _loop.default_excecption_handler(ctx)

        loop.run_until_complete(asyncio.gather(*[cluster.stop() for cluster in launcher.clusters]))

        loop.set_exception_handler(shutdown_handler)
        tasks = asyncio.gather(*asyncio.all_tasks(loop=loop), loop=loop, return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()
        while not tasks.done() and not loop.is_closed():
            loop.run_forever()
    finally:
        if hasattr(loop, 'shutdown_asyncgens'):
            loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        print("press ctrl c again")
        loop.close()

