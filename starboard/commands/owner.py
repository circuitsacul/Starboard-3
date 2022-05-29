# MIT License
#
# Copyright (c) 2022 TrigonDev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import crescent
import hikari
from hikari_clusters import callbacks, payload

from starboard.config import CONFIG
from starboard.constants import MESSAGE_LEN
from starboard.database import goc_user
from starboard.exceptions import StarboardError
from starboard.stats import post_stats
from starboard.tasks.patreon import _get_all_patrons
from starboard.utils import paginate, trunc_list, truncate
from starboard.views import Paginator

from ._checks import owner_only

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("owner")
owner = crescent.Group("owner", "Owner only commands", hooks=[owner_only])


def _parse_response(
    rid: int, pl: payload.RESPONSE | callbacks.NoResponse, block: bool = False
) -> str:
    if isinstance(pl, callbacks.NoResponse):
        return f"Client {rid} failed to respond."
    elif isinstance(pl.data, payload.ResponseNotFound):
        return f"Client {pl.author} could not find the command."

    if isinstance(pl.data, payload.ResponseTraceback):
        res = pl.data.traceback
    else:
        assert pl.data.data is not None
        res = pl.data.data["result"]

    if not block:
        res = f"Client {pl.author} responded with:\n\n{res}"
        res = truncate(res, MESSAGE_LEN)
    else:
        res = f"Client {pl.author} responded with:\n```\n{res}"
        res = truncate(res, MESSAGE_LEN - 4)
        res += "\n```"
    return res


@plugin.include
@owner.child
@crescent.command(
    name="patrons", description="List patrons", guild=CONFIG.main_guild
)
class ListPatrons:
    async def callback(self, ctx: crescent.Context) -> None:
        p = await _get_all_patrons()
        paginator = Paginator(ctx.user.id, list(paginate(repr(p), 2000)))
        await paginator.send(ctx.interaction)


@plugin.include
@owner.child
@crescent.command(
    name="post-stats",
    description="Manually post guild count",
    guild=CONFIG.main_guild,
)
class PostGuildCount:
    guilds = crescent.option(int, "The guild count to post")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        await ctx.defer(True)
        work, fail = await post_stats(bot, self.guilds)
        await ctx.respond(
            "Worked:\n - "
            + "\n - ".join(work)
            + "\nFailed:\n - "
            + "\n - ".join(fail),
            ephemeral=True,
        )


@plugin.include
@owner.child
@crescent.command(
    name="give-credits",
    description="Gives a user credits",
    guild=CONFIG.main_guild,
)
class GiveCredits:
    user = crescent.option(str, "The id of the user")
    credits = crescent.option(int, "The number of credits to give")

    async def callback(self, ctx: crescent.Context) -> None:
        try:
            uid = int(self.user)
        except ValueError:
            raise StarboardError(f"{self.user} is not a valid id.")

        bot = cast("Bot", ctx.app)
        try:
            obj = await bot.rest.fetch_user(uid)
        except hikari.NotFoundError:
            raise StarboardError(f"No user with id {uid} was found.")

        u = await goc_user(uid, obj.is_bot)
        u.credits = u.credits + self.credits
        await u.save()
        await ctx.respond(
            f"Gave {obj} {self.credits} credits. They now have {u.credits} "
            "credits.",
            ephemeral=True,
        )


@plugin.include
@owner.child
@crescent.command(
    name="clear-cache",
    description="Clears the cache entirely",
    guild=CONFIG.main_guild,
)
async def clear_cache(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    bot.cache.clear_safe()
    await ctx.respond("Cleared the cache.", ephemeral=True)


@plugin.include
@owner.child
@crescent.command(
    name="eval", description="Evaluate code", guild=CONFIG.main_guild
)
class Eval:
    code = crescent.option(str, "Code to evaluate")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        await ctx.defer(True)

        stdout, obj = await bot.exec_code(
            self.code, {"_bot": bot, "_ctx": ctx}
        )
        await ctx.respond(
            embed=bot.embed(title="Output", description=stdout).add_field(
                name="Return", value=repr(obj)
            )
        )


@plugin.include
@owner.child
@crescent.command(
    name="evall",
    description="Broadcast eval to all clusters",
    guild=CONFIG.main_guild,
)
class EvalBroadcast:
    code = crescent.option(str, "Code to evaluate")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)

        ret = await bot.cluster.ipc.send_command(
            bot.cluster.ipc.cluster_uids, "eval", {"code": self.code}
        )
        pages: list[str] = []
        for rid, pl in ret.items():
            pages.append(_parse_response(rid, pl))

        if not pages:
            raise StarboardError("No responses were received.")
        paginator = Paginator(ctx.user.id, pages)
        await paginator.send(ctx.interaction, ephemeral=True)


@plugin.include
@owner.child
@crescent.command(
    name="shell", description="Run a shell command", guild=CONFIG.main_guild
)
class ShellCommand:
    command = crescent.option(str, "The command to run")
    broadcast = crescent.option(
        bool, "Whether or not to broadcast to all servers", default=False
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)

        if self.broadcast:
            send_to = bot.cluster.ipc.server_uids
        else:
            send_to = {bot.cluster.server_uid}

        ret = await bot.cluster.ipc.send_command(
            send_to, "run_shell", {"command": self.command}
        )

        pages: list[str] = []
        for rid, pl in ret.items():
            pages.append(_parse_response(rid, pl, block=True))

        if not pages:
            raise StarboardError("No responses were received.")
        paginator = Paginator(ctx.user.id, pages)
        await paginator.send(ctx.interaction, ephemeral=True)


@plugin.include
@owner.child
@crescent.command(
    name="reconnect",
    description="Reconnect all clusters",
    guild=CONFIG.main_guild,
)
async def reconnect_clusters(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    await ctx.respond("Reconnecting all clusters...", ephemeral=True)
    await asyncio.sleep(1)
    await bot.cluster.ipc.send_event(
        bot.cluster.ipc.cluster_uids, "cluster_stop"
    )


@plugin.include
@owner.child
@crescent.command(
    name="restart", description="Restart the bot", guild=CONFIG.main_guild
)
async def restart_bot(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    if not bot.cluster.ipc.brain_uid:
        await ctx.respond("Brain UID is undefined...", ephemeral=True)
        return
    await ctx.respond("Restarting bot...", ephemeral=True)
    await asyncio.sleep(1)
    await bot.cluster.ipc.send_event([bot.cluster.ipc.brain_uid], "shutdown")


class Rollback(Exception):
    """Rollback the transaction."""


@plugin.include
@owner.child
@crescent.command(
    name="sql", description="Execute raw SQL", guild=CONFIG.main_guild
)
class RunSQL:
    sql = crescent.option(str, "The SQL to run")
    rollback = crescent.option(
        bool, "Whether to rollback any changes", default=True
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert bot.database.pool
        try:
            async with bot.database.pool.acquire() as con:
                async with con.transaction():
                    ret: list[str] = []
                    async for r in con.cursor(self.sql, []):
                        ret.append(f"\n - {repr(r)}")

                        if len(ret) >= 50:
                            break

                    ret = trunc_list(
                        ret, MESSAGE_LEN - 8, lambda x: f"\n - And {x} others."
                    )
                    result = "```\n" + "".join(ret) + "\n```"
                    if self.rollback:
                        raise Rollback
        except Rollback:
            pass
        except Exception as e:
            result = str(e)

        await ctx.respond(result, ephemeral=True)
