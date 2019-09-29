import asyncio
import io
import json
import logging
import sys
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
import websockets
from discord.ext import commands

_, shard_ids, shard_count, name = sys.argv
shard_ids = json.loads(shard_ids)

log = logging.getLogger(f"Cluster#{name}")
log.setLevel(logging.DEBUG)
log.handlers = [logging.FileHandler(f'cluster-{name}.log', encoding='utf-8', mode='a')]

log.info(f'[Cluster#{name}] {shard_ids}, {shard_count}')


class ClusterBot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        self.cluster_name = kwargs.pop('cluster_name')
        super().__init__(**kwargs)
        self.websocket = None
        self._last_result = None
        self.ws_task = None
        self.responses = asyncio.Queue()
        self.eval_wait = False
        self.load_extension("eval")

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    async def close(self, *args, **kwargs):
        await self.websocket.close()
        await super().close()

    async def exec(self, code):
        env = {
            'bot': self,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(code)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return f'{e.__class__.__name__}: {e}'

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            f'{value}{traceback.format_exc()}'
        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    return str(value)
                else:
                    return 'None'
            else:
                self._last_result = ret
                return f'{value}{ret}'

    async def websocket_loop(self):
        while True:
            msg = await self.websocket.recv()
            data = json.loads(msg, encoding='utf-8')
            if self.eval_wait and data.get('response'):
                await self.responses.put(data)
            cmd = data.get('command')
            if not cmd:
                continue
            if cmd == 'ping':
                ret = {'response': 'pong'}
                log.info("received command [ping]")
            elif cmd == 'eval':
                log.info(f"received command [eval] ({data['content']})")
                content = data['content']
                data = await self.exec(content)
                ret = {'response': str(data)}
            else:
                ret = {'response': 'unknown command'}
            ret['author'] = self.cluster_name
            log.info(f"responding: {ret}")
            await self.websocket.send(json.dumps(ret).encode('utf-8'))

    async def ensure_ipc(self):
        self.websocket = w = await websockets.connect('ws://localhost:42069')
        await w.send(self.cluster_name.encode('utf-8'))
        try:
            await w.recv()
            self.ws_task = self.loop.create_task(self.websocket_loop())
        except websockets.ConnectionClosed as exc:
            log.warning(f"! couldnt connect to ws: {exc.code} {exc.reason}")
            self.websocket = None
            raise


bot = ClusterBot(
    command_prefix='$$',
    shard_ids=shard_ids,
    shard_count=int(shard_count),
    cluster_name=name
)


@bot.event
async def on_ready():
    log.info(f'[Cluster#{bot.cluster_name}] Ready called.')


@bot.event
async def on_shard_ready(shard):
    log.info(f'[Cluster#{bot.cluster_name}] Shard {shard} ready')


@bot.event
async def on_command_error(ctx, exc):
    log.error(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    await ctx.send("check logs")


@bot.event
async def on_error(*args):
    log.error(traceback.format_exc())


if __name__ == '__main__':
    bot.loop.create_task(bot.ensure_ipc())
    bot.run("bot token here")

