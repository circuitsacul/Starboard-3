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

from ._converters import DecimalC
from .guild import Guild
from .user import User


class Message(apgorm.Model):
    message_id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)
    channel_id = types.Numeric().field().with_converter(DecimalC)
    author_id = types.Numeric().field().with_converter(DecimalC)

    is_nsfw = types.Boolean().field()

    forced_to = types.Array(types.Numeric()).field(default=[])
    trashed = types.Boolean().field(default=False)
    trash_reason = types.VarChar(512).nullablefield()
    frozen = types.Boolean().field(default=False)

    guild_id_fk = apgorm.ForeignKey(guild_id, Guild.guild_id)
    author_id_fk = apgorm.ForeignKey(author_id, User.user_id)

    primary_key = (message_id,)
