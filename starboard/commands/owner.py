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
import subprocess
from typing import TYPE_CHECKING, cast

import crescent

from starboard.constants import MESSAGE_LEN
from starboard.utils import truncate

from ._checks import owner_only

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("owner")
owner = crescent.Group("owner", "Owner only commands", hooks=[owner_only])


@plugin.include
@owner.child
@crescent.command(name="eval", description="Evaluate code")
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
@crescent.command(name="shell", description="Run a shell command")
class ShellCommand:
    command = crescent.option(str, "The command to run")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.defer(True)
        p = subprocess.Popen(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = p.communicate()
        await ctx.respond(
            "```\n" + truncate((out or err).decode(), MESSAGE_LEN - 8) + "```"
        )


@plugin.include
@owner.child
@crescent.command(name="reconnect", description="Reconnect all clusters")
async def reconnect_clusters(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    await ctx.respond("Reconnecting all clusters...", ephemeral=True)
    await asyncio.sleep(1)
    await bot.cluster.ipc.send_event(
        bot.cluster.ipc.cluster_uids, "cluster_stop"
    )


@plugin.include
@owner.child
@crescent.command(name="restart", description="Restart the bot")
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

    pass


@plugin.include
@owner.child
@crescent.command(name="sql", description="Execute raw SQL")
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
                    ret = await con.fetchmany(self.sql, [])
                    result = " - " + "\n - ".join([repr(d) for d in ret[0:50]])
                    if self.rollback:
                        raise Rollback
        except Rollback:
            pass
        except Exception as e:
            result = str(e)

        await ctx.respond(result, ephemeral=True)
