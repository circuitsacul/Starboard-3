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

from enum import IntEnum
from typing import Iterable

import apgorm
from apgorm import types
from asyncpg import UniqueViolationError

from ._converters import DecimalC, NullDecimalC


async def goc_user(user_id: int, is_bot: bool) -> User:
    try:
        return await User(user_id=user_id, is_bot=is_bot).create()
    except UniqueViolationError:
        return await User.fetch(user_id=user_id)


async def goc_patron(patreon_id: str) -> Patron:
    try:
        return await Patron(patreon_id=patreon_id).create()
    except UniqueViolationError:
        return await Patron.fetch(patreon_id=patreon_id)


class PatreonStatus(IntEnum):
    NONE = 0
    ACTIVE = 1
    DECLINED = 2
    FORMER = 3


class User(apgorm.Model):
    __slots__: Iterable[str] = ()

    user_id = types.Numeric().field().with_converter(DecimalC)

    is_bot = types.Boolean().field()
    credits = types.Int().field(default=0)

    donated_cents = types.BigInt().field(default=0)
    """Total cents donated, excluding Patreon."""
    patreon_status = (
        types.SmallInt()
        .field(default=0)
        .with_converter(apgorm.IntEFConverter(PatreonStatus))
    )

    primary_key = (user_id,)


class Patron(apgorm.Model):
    __slots__: Iterable[str] = ()

    patreon_id = types.VarChar(64).field()
    discord_id = types.Numeric().nullablefield().with_converter(NullDecimalC)
    last_patreon_total_cents = types.BigInt().field(default=0)

    primary_key = (patreon_id,)
