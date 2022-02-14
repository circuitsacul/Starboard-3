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

import pytz
from datetime import datetime, timedelta

import crescent

from starboard.database import Guild, goc_guild, User
from starboard.views import Confirm
from starboard.config import CONFIG
from starboard.exceptions import StarboardErr

from ._checks import guild_only


plugin = crescent.Plugin("premium-commands")
prem = crescent.Group("premium", "Premium-related commands")


@plugin.include
@prem.child
@crescent.hook(guild_only)
@crescent.command(
    name="server", description="Shows the premium status for a server"
)
async def guild_premium(ctx: crescent.Context) -> None:
    assert ctx.guild_id is not None
    g = await Guild.exists(id=ctx.guild_id)

    prem_end = g.premium_end if g else None

    if prem_end is None:
        await ctx.respond("This server does not have premium.")
    else:
        await ctx.respond(
            f"This server has premium until <t:{int(prem_end.timestamp())}>"
        )


@plugin.include
@prem.child
@crescent.hook(guild_only)
@crescent.command(name="redeem", description="Redeems premium for a server")
class Redeem:
    months = crescent.option(
        int,
        "The number of months to redeem (each costing "
        f"{CONFIG.credits_per_month} credits)",
        min_value=1,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None

        if self.months < 1:
            raise StarboardErr("You must redeem at least one month.")

        cost = self.months * CONFIG.credits_per_month

        conf = Confirm(ctx.user.id)
        m = await ctx.respond(
            f"Are you sure? This will cost you {cost} credits and will give "
            f"this server {self.months} months of premium.",
            components=conf.build(),
            ensure_message=True,
        )
        conf.start(m)
        await conf.wait()

        if not conf.result:
            await m.edit("Cancelled.", components=[])
            return

        u = await User.exists(id=ctx.user.id)
        if not u or u.credits < cost:
            await m.edit("You don't have enough credits.", components=[])
            return

        u.credits = u.credits - cost
        await u.save()
        if u.credits < 0:  # they tried running the command twice to trick us
            u.credits = u.credits + cost  # revert the change
            await u.save()
            await m.edit("Nice try.", components=[])
            return

        g = await goc_guild(ctx.guild_id)

        delta = timedelta(days=CONFIG.days_per_month * self.months)
        from_now = datetime.now(pytz.UTC) + delta
        if g.premium_end:
            from_curr = g.premium_end + delta
            new = max(from_curr, from_now)
        else:
            new = from_now

        g.premium_end = new
        await g.save()
        await m.edit("Done.", components=[])


@plugin.include
@prem.child
@crescent.hook(guild_only)
@crescent.command(
    name="credits", description="Tells you how many credits you have"
)
async def credits(ctx: crescent.Context) -> None:
    u = await User.exists(id=ctx.user.id)
    credits = u.credits if u else 0
    await ctx.respond(f"You have {credits} credits.", ephemeral=True)
