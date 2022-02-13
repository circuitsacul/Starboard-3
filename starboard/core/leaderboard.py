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

from dataclasses import dataclass

from apgorm import raw as r
from apgorm import sql

from starboard.config import CONFIG
from starboard.database import Member


async def add_xp(user_id: int, guild_id: int, count: int) -> None:
    q = Member.update_query()
    q.where(user_id=user_id, guild_id=guild_id)
    q.set(xp=sql(Member.xp, r("+"), count))
    await q.execute()


async def get_leaderboard(guild_id: int) -> dict[int, MemberStats]:
    q = Member.fetch_query()
    q.where(guild_id=guild_id)
    q.where(Member.xp.gt(0))
    q.order_by(Member.xp, reverse=True)
    ret = await q.fetchmany(limit=CONFIG.leaderboard_length)

    return {m.user_id: MemberStats(m.xp, x + 1) for x, m in enumerate(ret)}


@dataclass
class MemberStats:
    xp: int
    rank: int