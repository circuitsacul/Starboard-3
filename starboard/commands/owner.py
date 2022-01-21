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

import tanjun

if TYPE_CHECKING:
    from starboard.bot import Bot


C = tanjun.Component()


owner = tanjun.slash_command_group(
    "owner", "Owner Only Commands", default_to_ephemeral=True
)
owner = tanjun.with_owner_check(owner)
C.add_slash_command(owner)


@owner.with_command
@tanjun.with_str_slash_option("code", "Code to evaluate.")
@tanjun.as_slash_command("eval", "Evaluate code.")
async def evaluate(ctx: tanjun.abc.SlashContext, code: str):
    bot = cast("Bot", ctx.interaction.app)
    await ctx.defer()

    stdout, obj = await bot.exec_code(code, {"_bot": bot, "_ctx": ctx})
    await ctx.respond(
        embed=bot.embed(title="Output", description=stdout,).add_field(
            name="Return",
            value=repr(obj),
        )
    )


@owner.with_command
@tanjun.as_slash_command("restart", "Restart All Clusters")
async def restart_bot(ctx: tanjun.abc.SlashContext):
    bot = cast("Bot", ctx.interaction.app)
    await ctx.respond("Restarting all clusters...")
    await asyncio.sleep(1)
    await bot.ipc.send_command(bot.ipc.cluster_uids, "cluster_stop")


class Rollback(Exception):
    """Rollback the transaction."""

    pass


@owner.with_command
@tanjun.with_str_slash_option("sql", "The SQL to execute.")
@tanjun.with_bool_slash_option(
    "rollback", "Whether to rollback.", default=True
)
@tanjun.as_slash_command("sql", "Execute SQL, optionally rolling back.")
async def run_sql(
    ctx: tanjun.abc.SlashContext,
    sql: str,
    rollback: bool,
):
    bot = cast("Bot", ctx.interaction.app)
    assert bot.database.pool
    try:
        async with bot.database.pool.acquire() as con:
            async with con.transaction():
                ret = await con.fetchmany(sql, [])
                result = " - " + "\n".join([repr(d) for d in ret[0:50]])
                if rollback:
                    raise Rollback
    except Rollback:
        pass
    except Exception as e:
        result = str(e)

    await ctx.respond(result)


load = C.make_loader()
