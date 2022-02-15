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

import apgorm
from apgorm import types

from ._converters import DecimalC


async def goc_user(user_id: int, is_bot: bool) -> User:
    if (u := await User.exists(id=user_id)) is not None:
        return u
    return await User(id=user_id, is_bot=is_bot).create()


class PatreonStatus(IntEnum):
    NONE = 0
    ACTIVE = 1
    DECLINED = 2
    FORMER = 3


class User(apgorm.Model):
    id = types.Numeric().field().with_converter(DecimalC)

    is_bot = types.Boolean().field()
    votes = types.Int().field(default=0)
    credits = types.Int().field(default=0)
    credits_recv = types.Int().field(default=0)

    last_patreon_total_cents = types.BigInt().field(default=0)
    patreon_status = (
        types.SmallInt()
        .field(default=0)
        .with_converter(apgorm.IntEFConverter(PatreonStatus))
    )

    primary_key = (id,)
