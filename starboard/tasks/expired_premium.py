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
import traceback
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from starboard.config import CONFIG
from starboard.core.notifications import notify
from starboard.core.premium import try_autoredeem, update_prem_locks
from starboard.database import Guild

if TYPE_CHECKING:
    from starboard.bot import Bot


async def check_expired_premium(bot: Bot) -> None:
    if bot.cluster.cluster_id != 0:
        return

    while True:
        try:
            await _check_expired_premium(bot)
        except Exception:
            traceback.print_exc()

        await asyncio.sleep(CONFIG.check_expired_premium_delay)


async def _check_expired_premium(bot) -> None:
    now = datetime.now(timezone.utc)

    q = Guild.fetch_query()
    q.where(Guild.premium_end.is_null.not_)
    q.where(Guild.premium_end.lt(now))
    expired = await q.fetchmany()

    tasks = [
        asyncio.create_task(_check_for_server(bot, g, now)) for g in expired
    ]
    await asyncio.gather(*tasks, return_exceptions=True)


async def _check_for_server(bot: Bot, g: Guild, now: datetime) -> None:
    guild = bot.cache.get_guild(g.guild_id)
    if not guild:
        return

    member = await try_autoredeem(bot, g)
    if not member:
        # NOTE: we do this to prevent the possibility that someone
        # redeemed premium between the original query (that fetched
        # expired guilds) and this query. We don't want any added
        # premium to disappear.
        await Guild.update_query().where(
            Guild.premium_end.lt(now), guild_id=g.guild_id
        ).set(premium_end=None).execute()
        await update_prem_locks(bot, g.guild_id)
        return

    await notify(
        bot,
        member.user.id,
        f"You have autoredeem enabled in {guild.name}, so "
        f"{CONFIG.credits_per_month} credits were taken from your account to "
        "redeem premium. You can disable autoredeem by running `/premium "
        "autoredeem disable` in that server, or `/premium autoredeem clear` "
        "to disable in all servers.",
    )
