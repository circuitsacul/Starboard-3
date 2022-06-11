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

from typing import TYPE_CHECKING, cast

import crescent
import hikari

from starboard.config import CONFIG
from starboard.core.premium import redeem, update_prem_locks
from starboard.database import (
    AutoStarChannel,
    Guild,
    Member,
    Starboard,
    User,
    goc_guild,
    goc_member,
)
from starboard.exceptions import StarboardError
from starboard.views import Confirm

from ._autocomplete import asc_autocomplete, starboard_autocomplete
from ._checks import guild_only, has_guild_perms

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("premium-commands")
prem = crescent.Group("premium", "Premium-related commands")
locks = prem.sub_group(
    "locks",
    "Manage premium locks",
    hooks=[has_guild_perms(hikari.Permissions.MANAGE_GUILD)],
)


@plugin.include
@locks.child
@crescent.hook(guild_only)
@crescent.command(
    name="refresh", description="Refresh the premium locks for the server"
)
async def refresh_prem_lock(ctx: crescent.Context) -> None:
    assert ctx.guild_id

    conf = Confirm(ctx.user.id)
    msg = await ctx.respond(
        "Are you sure you want to refresh the premium locks for this server? "
        "If anything is over the limit, it may be disabled.",
        components=conf.build(),
        ephemeral=True,
        ensure_message=True,
    )
    conf.start(msg)
    await conf.wait()

    if not conf.result:
        await ctx.edit("Cancelled.", components=None)
        return

    await update_prem_locks(cast("Bot", ctx.app), ctx.guild_id)
    await ctx.edit("Refreshed premium locks.", components=None)


@plugin.include
@locks.child
@crescent.hook(guild_only)
@crescent.command(
    name="move-autostar",
    description="Move a lock from one autostar channel to another",
)
class MoveAscPremLock:
    asc_from = crescent.option(
        str,
        "The starboard to move the lock from",
        autocomplete=asc_autocomplete,
        name="from",
    )
    asc_to = crescent.option(
        str,
        "The starboard to move the lock to",
        autocomplete=asc_autocomplete,
        name="to",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        asc_from = await AutoStarChannel.from_name(ctx.guild_id, self.asc_from)
        asc_to = await AutoStarChannel.from_name(ctx.guild_id, self.asc_to)

        if not asc_from.prem_locked:
            raise StarboardError(f"'{asc_from.name}' is not locked.")
        if asc_to.prem_locked:
            raise StarboardError(f"'{asc_to.name}' is already locked.")

        asc_from.prem_locked = False
        asc_to.prem_locked = True
        await asc_from.save()
        await asc_to.save()

        await ctx.respond(
            f"Lock moved from '{asc_from.name}' to '{asc_to.name}'."
        )


@plugin.include
@locks.child
@crescent.hook(guild_only)
@crescent.command(
    name="move-starboard",
    description="Move a lock from one starboard to another",
)
class MoveSbPremLock:
    sb_from = crescent.option(
        str,
        "The starboard to move the lock from",
        autocomplete=starboard_autocomplete,
        name="from",
    )
    sb_to = crescent.option(
        str,
        "The starboard to move the lock to",
        autocomplete=starboard_autocomplete,
        name="to",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        sb_from = await Starboard.from_name(ctx.guild_id, self.sb_from)
        sb_to = await Starboard.from_name(ctx.guild_id, self.sb_to)

        if not sb_from.prem_locked:
            raise StarboardError(f"'{sb_from.name}' is not locked.")
        if sb_to.prem_locked:
            raise StarboardError(f"'{sb_to.name}' is already locked.")

        sb_from.prem_locked = False
        sb_to.prem_locked = True
        await sb_from.save()
        await sb_to.save()

        await ctx.respond(
            f"Lock moved from '{sb_from.name}' to '{sb_to.name}'."
        )


@plugin.include
@prem.child
@crescent.hook(guild_only)
@crescent.command(
    name="server", description="Shows the premium status for a server"
)
async def guild_premium(ctx: crescent.Context) -> None:
    assert ctx.guild_id is not None
    g = await Guild.exists(guild_id=ctx.guild_id)

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
        bot = cast("Bot", ctx.app)

        if self.months < 1:
            raise StarboardError("You must redeem at least one month.")

        cost = self.months * CONFIG.credits_per_month

        conf = Confirm(ctx.user.id)
        m = await ctx.respond(
            f"Are you sure? This will cost you {cost} credits and will give "
            f"this server {self.months} months of premium.",
            components=conf.build(),
            ensure_message=True,
            ephemeral=True,
        )
        conf.start(m)
        await conf.wait()

        if not conf.result:
            await ctx.edit("Cancelled.", components=[])
            return

        g = await goc_guild(ctx.guild_id)
        u = await User.exists(user_id=ctx.user.id)
        if not u:
            await ctx.edit("You don't have enough credits.", components=[])
            return

        success = await redeem(bot, u.user_id, g.guild_id, self.months)
        if not success:
            await ctx.edit("You don't have enough credits.", components=[])
            return

        await ctx.edit("Done.", components=[])
        await update_prem_locks(bot, ctx.guild_id)


@plugin.include
@prem.child
@crescent.hook(guild_only)
@crescent.command(
    name="credits", description="Tells you how many credits you have"
)
async def credits(ctx: crescent.Context) -> None:
    u = await User.exists(user_id=ctx.user.id)
    credits = u.credits if u else 0
    await ctx.respond(f"You have {credits} credits.", ephemeral=True)


ar = prem.sub_group("autoredeem", "Manage autoredeem")


@plugin.include
@ar.child
@crescent.hook(guild_only)
@crescent.command(name="enable", description="Enables autoredeem for a server")
async def enable_autoredeem(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    m = await goc_member(ctx.guild_id, ctx.user.id, ctx.user.is_bot)
    if m.autoredeem_enabled:
        raise StarboardError("Autoredeem is already enabled in this server.")
    m.autoredeem_enabled = True
    await m.save()
    await ctx.respond("Enabled autoredeem for this server.", ephemeral=True)


@plugin.include
@ar.child
@crescent.hook(guild_only)
@crescent.command(
    name="disable", description="Disables autoredeem for a server"
)
async def disable_autoredeem(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    m = await Member.exists(user_id=ctx.user.id, guild_id=ctx.guild_id)
    if not (m and m.autoredeem_enabled):
        raise StarboardError("Autoredeem is not enabled in this server.")

    m.autoredeem_enabled = False
    await m.save()
    await ctx.respond("Disabled autoredeem for this server.", ephemeral=True)


@plugin.include
@ar.child
@crescent.command(name="view", description="View autoreeem info")
async def view_autoredeem(ctx: crescent.Context) -> None:
    count = await Member.count(
        user_id=ctx.user.id, guild_id=ctx.guild_id, autoredeem_enabled=True
    )
    if ctx.guild_id is not None:
        m = await Member.exists(user_id=ctx.user.id, guild_id=ctx.guild_id)
        ar_enabled = m.autoredeem_enabled if m else False
        await ctx.respond(
            f"Autoredeem is {'' if ar_enabled else 'not '}enabled for this "
            f"server. It is enabled in {count} servers total.",
            ephemeral=True,
        )
    else:
        await ctx.respond(
            f"Autoredeem is enabled in {count} servers.", ephemeral=True
        )


@plugin.include
@ar.child
@crescent.command(
    name="clear", description="Disables autoredeem in all servers"
)
async def clear_autoredeem(ctx: crescent.Context) -> None:
    conf = Confirm(ctx.user.id, danger=True)
    m = await ctx.respond(
        "Are you sure? This will disable autoredeem for any servers you've "
        "enabled it in.",
        components=conf.build(),
        ensure_message=True,
    )
    conf.start(m)
    await conf.wait()

    if not conf.result:
        await m.edit("Cancelled.", components=[])
        return

    await Member.update_query().where(
        user_id=ctx.user.id, autoredeem_enabled=True
    ).set(autoredeem_enabled=False).execute()
    await m.edit("Done.", components=[])
