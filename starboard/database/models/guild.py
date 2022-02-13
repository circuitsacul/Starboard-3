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
from datetime import datetime

import apgorm
from apgorm import types

from ._converters import DecimalC, NullDecimalC


async def goc_guild(guild_id: int) -> Guild:
    if (g := await Guild.exists(id=guild_id)) is not None:
        return g
    return await Guild(id=guild_id).create()


class Guild(apgorm.Model):
    id = types.Numeric().field().with_converter(DecimalC)

    # config options
    log_channel_id = (
        types.Numeric().nullablefield().with_converter(NullDecimalC)
    )
    _premium_end = types.TimestampTZ().nullablefield()

    stack_posroles = types.Boolean().field(default=False)
    stack_xproles = types.Boolean().field(default=False)

    # primary key
    primary_key = (id,)

    async def premium_end(self, allow_update: bool = False) -> datetime | None:
        if not self._premium_end:
            return None

        now = datetime.now(pytz.UTC)

        if self._premium_end < now:
            if allow_update:
                self._premium_end = None
                await self.save()

            return None

        return self._premium_end
