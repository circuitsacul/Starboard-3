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
from typing import TYPE_CHECKING
from datetime import timedelta, datetime

from starboard.database import User, Guild
from starboard.config import CONFIG

if TYPE_CHECKING:
    from starboard.bot import Bot


async def redeem(bot: Bot, user_id: int, guild_id: int, months: int) -> bool:
    assert bot.database.pool
    async with bot.database.pool.acquire() as con:
        async with con.transaction():
            await con.execute("LOCK TABLE users IN EXCLUSIVE MODE")
            await con.execute("LOCK TABLE guilds IN EXCLUSIVE MODE")
            _g = await con.fetchrow(
                "SELECT * FROM guilds WHERE id=$1 FOR UPDATE", [guild_id]
            )
            _u = await con.fetchrow(
                "SELECT * FROM users WHERE id=$1 FOR UPDATE", [user_id]
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
