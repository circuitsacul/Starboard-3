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

from typing import TYPE_CHECKING

from starboard.config import CONFIG
from starboard.cooldown import Cooldown
from starboard.database import Member, XPRole

if TYPE_CHECKING:
    from starboard.bot import Bot


COOLDOWN: Cooldown[int] = Cooldown()


async def refresh_xpr(bot: Bot, guild_id: int, user_id: int) -> bool:
    if not COOLDOWN.trigger(
        user_id, CONFIG.xpr_cooldown_cap, CONFIG.xpr_cooldown_period
    ):
        return False

    obj = await bot.cache.gof_member(guild_id, user_id)
    if not obj:
        return True
    member = await Member.fetch(user_id=user_id, guild_id=guild_id)

    xpr = await XPRole.fetch_query().where(guild_id=guild_id).fetchmany()
    if not xpr:
        return True

    add = [
        r for r in xpr if member.xp >= r.required and r.id not in obj.role_ids
    ]
    remove = [
        r for r in xpr if member.xp < r.required and r.id in obj.role_ids
    ]

    for r in remove:
        await obj.remove_role(r.id, reason="XPRoles")

    for r in add:
        await obj.add_role(r.id, reason="XPRoles")

    return True
