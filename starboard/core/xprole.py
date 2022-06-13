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

from contextlib import suppress
from typing import TYPE_CHECKING

import hikari
from pycooldown import FixedCooldown

from starboard.config import CONFIG
from starboard.database import XPRole, goc_member

if TYPE_CHECKING:
    from starboard.bot import Bot


COOLDOWN: FixedCooldown[int] = FixedCooldown(*CONFIG.user_xpr_cooldown)


async def refresh_xpr(bot: Bot, guild_id: int, user_id: int) -> bool:
    if COOLDOWN.update_ratelimit(user_id):
        return False

    obj = await bot.cache.gof_member(guild_id, user_id)
    if not obj:
        return True
    member = await goc_member(guild_id, user_id, obj.is_bot)

    xpr = await XPRole.fetch_query().where(guild_id=guild_id).fetchmany()
    if not xpr:
        return True

    add = [
        r
        for r in xpr
        if member.xp >= r.required and r.role_id not in obj.role_ids
    ]
    remove = [
        r for r in xpr if member.xp < r.required and r.role_id in obj.role_ids
    ]

    with suppress(hikari.ForbiddenError):
        for r in remove:
            with suppress(hikari.NotFoundError):
                await obj.remove_role(r.role_id, reason="XPRoles")
        for r in add:
            with suppress(hikari.NotFoundError):
                await obj.add_role(r.role_id, reason="XPRoles")
    return True
