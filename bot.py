from contextlib import redirect_stdout

from discord.ext import commands
import discord
import logging
import json
import sys
import websockets
import traceback, textwrap, io

_, shard_ids, shard_count, name = sys.argv
shard_ids = json.loads(shard_ids)

log = logging.getLogger(f"Cluster#{name}")
log.setLevel(logging.DEBUG)
log.handlers = [logging.FileHandler(f'cluster-{name}.log', encoding='utf-8', mode='a')]

log.info(f'[Cluster#{name}] {shard_ids}, {shard_count}')

bot = commands.AutoShardedBot(
    shard_count=int(shard_count),
    shard_ids=shard_ids,
    command_prefix="$$",
    status=discord.Status.offline
)
bot.cluster_name = name
bot.websocket = None
bot._last_result = None
# bot.load_extension("jishaku")


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')


@bot.command(hidden=True, name='eval')
async def _eval(ctx, *, body: str):
    """Evaluates a code"""

    env = {
        'bot': bot,
        'ctx': ctx,
        'channel': ctx.channel,
        'author': ctx.author,
        'guild': ctx.guild,
        'message': ctx.message,
        '_': bot._last_result
    }

    env.update(globals())

    body = cleanup_code(body)
    stdout = io.StringIO()

    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

    func = env['func']
    try:
        with redirect_stdout(stdout):
            ret = await func()
    except Exception as e:
        value = stdout.getvalue()
        await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
    else:
        value = stdout.getvalue()
        try:
            await ctx.message.add_reaction('\u2705')
        except:
            pass

        if ret is None:
            if value:
                await ctx.send(f'```py\n{value}\n```')
        else:
            bot._last_result = ret
            await ctx.send(f'```py\n{value}{ret}\n```')


async def ensure_ipc():
    bot.websocket = w = await websockets.connect('ws://localhost:42069')
    await w.send(bot.cluster_name.encode())
    try:
        await w.recv()
    except websockets.ConnectionClosed as exc:
        log.warning(f"! couldnt connect to ws: {exc.code} {exc.reason}")
        bot.websocket = None
        raise


bot.ensure_ipc = ensure_ipc


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
    bot.run("[token]")
