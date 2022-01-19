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

import apgorm
from apgorm import types

from ._converters import DecimalC, NullDecimalC


class Guild(apgorm.Model):
    id = types.Numeric().field().with_converter(DecimalC)

    # config options
    locale = types.VarChar(8).field(default="en_US")

    log_channel_id = (
        types.Numeric().nullablefield().with_converter(NullDecimalC)
    )
    lvl_channel_id = (
        types.Numeric().nullablefield().with_converter(NullDecimalC)
    )
    ping_on_lvlup = types.Boolean().field(default=False)

    premium_end = types.Timestamp().nullablefield()

    enable_xp_cooldown = types.Boolean().field(default=True)
    xp_cooldown_count = types.SmallInt().field(default=3)
    xp_cooldown_bucket = types.SmallInt().field(default=60)  # seconds/user

    stack_posroles = types.Boolean().field(default=False)
    stack_xproles = types.Boolean().field(default=False)

    # primary key
    primary_key = (id,)
