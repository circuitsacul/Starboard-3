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

import apgorm
from apgorm import types

from ._converters import DecimalC
from .guild import Guild
from .user import User


class Member(apgorm.Model):
    user_id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)

    stars_given = types.Int().field(default=0)
    stars_received = types.Int().field(default=0)
    xp = types.Int().field(default=0)
    level = types.SmallInt().field(default=0)

    autoredeem_enabled = types.Boolean().field(default=False)

    userid_fk = apgorm.ForeignKey(user_id, User.id)
    guildid_fk = apgorm.ForeignKey(guild_id, Guild.id)

    primary_key = (
        user_id,
        guild_id,
    )
