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

from typing import Iterable

import apgorm
from apgorm import types
from asyncpg import UniqueViolationError

from starboard.config import CONFIG

from ._converters import DecimalC
from ._validators import num_range
from .guild import Guild
from .user import User


class Member(apgorm.Model):
    __slots__: Iterable[str] = ()

    user_id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)

    xp = types.Real().field(default=0)

    autoredeem_enabled = types.Boolean().field(default=False)

    userid_fk = apgorm.ForeignKey(user_id, User.user_id)
    guildid_fk = apgorm.ForeignKey(guild_id, Guild.guild_id)

    primary_key = (user_id, guild_id)

    xp.add_validator(num_range("XP", CONFIG.min_xp, CONFIG.max_xp))

    # methods
    @staticmethod
    async def get_or_create(
        guild_id: int, user_id: int, is_bot: bool
    ) -> Member:
        if (
            m := await Member.exists(guild_id=guild_id, user_id=user_id)
        ) is not None:
            return m

        await Guild.get_or_create(guild_id)
        await User.get_or_create(user_id, is_bot)

        try:
            return await Member(guild_id=guild_id, user_id=user_id).create()
        except UniqueViolationError:
            return await Member.fetch(guild_id=guild_id, user_id=user_id)
