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


owner = tanjun.slash_command_group("owner", "Owner Only Commands")
owner = tanjun.with_owner_check(owner)
C.add_slash_command(owner)


@owner.with_command
@tanjun.with_str_slash_option("code", "Code to evaluate.")
@tanjun.as_slash_command("eval", "Evaluate code.")
async def evaluate(ctx: tanjun.abc.SlashContext, code: str):
    await ctx.defer()
    await ctx.respond(eval(code))


@owner.with_command
@tanjun.as_slash_command("restart", "Restart All Clusters")
async def restart_bot(ctx: tanjun.abc.SlashContext):
    bot = cast("Bot", ctx.interaction.app)
    await ctx.respond("Restarting all clusters...")
    await asyncio.sleep(1)
    await bot.ipc.send_command(bot.ipc.cluster_uids, "cluster_stop")


load = C.make_loader()
