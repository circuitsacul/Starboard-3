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

from enum import IntEnum

import apgorm
from apgorm import types


class PatreonStatus(IntEnum):
    NO = 0
    PATRON = 1
    DECLINED = 2


class User(apgorm.Model):
    user_id = types.Numeric().field()

    is_bot = types.Boolean()
    locale = types.VarChar(16).field(default="en_US")
    public = types.Boolean().field(default=True)
    votes = types.Int().field(default=0)
    credits = types.Int().field(default=0)
    total_donated = types.Money().field(default="$0")
    last_patreon_total = types.Money().field(default="$0")
    patreon_status = (
        types.SmallInt()
        .field(default=0)
        .with_converter(apgorm.IntEFConverter(PatreonStatus))
    )

    primary_key = (user_id,)