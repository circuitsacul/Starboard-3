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

import traceback
from contextlib import suppress
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import hikari
import pytz

from starboard.config import CONFIG
from starboard.database import (
    AutoStarChannel,
    Guild,
    Member,
    PatreonStatus,
    Starboard,
    User,
)

if TYPE_CHECKING:
    from starboard.bot import Bot


async def _add_role(member: hikari.Member, role_id: int | None) -> None:
    if role_id in member.role_ids or role_id is None:
        return
    with suppress(hikari.ForbiddenError, hikari.NotFoundError):
        await member.add_role(role_id)


async def _rm_role(member: hikari.Member, role_id: int | None) -> None:
    if role_id not in member.role_ids or role_id is None:
        return
    with suppress(hikari.ForbiddenError, hikari.NotFoundError):
        await member.remove_role(role_id)


async def _try_send(bot: Bot, channel: int, message: str) -> None:
    with suppress(hikari.ForbiddenError, hikari.NotFoundError):
        await bot.rest.create_message(channel, message)


async def update_prem_locks(bot: Bot, guild_id: int) -> None:
    guild = await Guild.exists(guild_id=guild_id)
    if not guild:
        return

    if guild.premium_end is not None:
        await Starboard.update_query().where(guild_id=guild_id).set(
            prem_locked=False
        ).execute()
        await AutoStarChannel.update_query().where(guild_id=guild_id).set(
            prem_locked=False
        ).execute()
        return

    # if we get here, the guild doesn't have premium
    # NOTE: kinda being lazy here. Should really lock the database while doing
    # this, but worst case they have an extra starboard or so.

    num_sb = await Starboard.count(guild_id=guild_id, prem_locked=False)
    if (to_lock := num_sb - CONFIG.np_max_starboards) > 0:
        sb_to_lock = (
            await Starboard.fetch_query()
            .where(guild_id=guild_id, prem_locked=False)
            .fetchmany(limit=to_lock)
        )
        for sb in sb_to_lock:
            sb.prem_locked = True
            await sb.save()
            await _try_send(
                bot,
                sb.channel_id,
                f"This starboard ({sb.name}) exceeds the non-premium limit "
                "and has been locked.",
            )
    elif to_lock < 0:
        sb_to_unlock = (
            await Starboard.fetch_query()
            .where(guild_id=guild_id, prem_locked=True)
            .fetchmany(limit=-to_lock)
        )
        for sb in sb_to_unlock:
            sb.prem_locked = False
            await sb.save()

    num_asc = await AutoStarChannel.count(guild_id=guild_id, prem_locked=False)
    if (to_lock := num_asc - CONFIG.np_max_autostar) > 0:
        asc_to_lock = (
            await AutoStarChannel.fetch_query()
            .where(guild_id=guild_id, prem_locked=False)
            .fetchmany(limit=to_lock)
        )
        for asc in asc_to_lock:
            asc.prem_locked = True
            await asc.save()
            await _try_send(
                bot,
                asc.channel_id,
                "This AutoStar channel exceeds the non-premium limit and has "
                "been locked.",
            )
    elif to_lock < 0:
        asc_to_unlock = (
            await AutoStarChannel.fetch_query()
            .where(guild_id=guild_id)
            .where(prem_locked=True)
            .fetchmany(limit=-to_lock)
        )
        for asc in asc_to_unlock:
            asc.prem_locked = False
            await asc.save()


async def update_supporter_roles(bot: Bot, user: User) -> None:
    if not CONFIG.main_guild:
        return
    member = await bot.cache.gof_member(CONFIG.main_guild, user.user_id)
    if not member:
        return
    if (
        user.patreon_status is PatreonStatus.ACTIVE
        or user.patreon_status is PatreonStatus.DECLINED
    ):
        await _add_role(member, CONFIG.patron_role)
        await _add_role(member, CONFIG.donor_role)
    elif user.patreon_status is PatreonStatus.FORMER:
        await _add_role(member, CONFIG.donor_role)
        await _rm_role(member, CONFIG.patron_role)
    else:
        await _rm_role(member, CONFIG.patron_role)
        await _rm_role(member, CONFIG.donor_role)


async def try_autoredeem(bot: Bot, guild: Guild) -> hikari.Member | None:
    q = Member.fetch_query()
    q.where(guild_id=guild.guild_id, autoredeem_enabled=True)
    ar = await q.fetchmany()

    for a in ar:
        member = await bot.cache.gof_member(guild.guild_id, a.user_id)
        if member is None:
            a.autoredeem_enabled = False
            await a.save()
            continue

        try:
            worked = await redeem(bot, a.user_id, guild.guild_id, 1)
        except Exception:
            traceback.print_exc()
            continue

        if worked:
            return member

        # if we reach this point, the user didn't have enough credits.
        # we disable autoredeem to prevent load on the bot later on.
        a.autoredeem_enabled = False
        await a.save()

    return None


async def redeem(bot: Bot, user_id: int, guild_id: int, months: int) -> bool:
    assert bot.database.pool
    async with bot.database.pool.acquire() as con:
        async with con.transaction():
            await con.execute("LOCK TABLE users IN EXCLUSIVE MODE")
            await con.execute("LOCK TABLE guilds IN EXCLUSIVE MODE")
            _g = await con.fetchrow(
                "SELECT * FROM guilds WHERE guild_id=$1 FOR UPDATE", [guild_id]
            )
            _u = await con.fetchrow(
                "SELECT * FROM users WHERE user_id=$1 FOR UPDATE", [user_id]
            )
            assert _u and _g
            guild = Guild._from_raw(**_g)
            user = User._from_raw(**_u)

            # update user
            credits = months * CONFIG.credits_per_month
            if user.credits < credits:
                return False

            user.credits = user.credits - credits
            await user.save(con=con)

            # update guild
            delta = timedelta(days=CONFIG.days_per_month * months)
            from_now = datetime.now(pytz.UTC) + delta
            if guild.premium_end:
                from_curr = guild.premium_end + delta
                new = max(from_curr, from_now)
            else:
                new = from_now

            guild.premium_end = new
            await guild.save(con=con)

    return True
