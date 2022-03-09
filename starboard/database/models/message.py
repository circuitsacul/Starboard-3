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

from ._converters import DecimalArrayC, DecimalC
from .guild import Guild
from .member import goc_member
from .user import User


async def goc_message(
    guild_id: int,
    channel_id: int,
    message_id: int,
    is_nsfw: bool,
    author_id: int,
    is_author_bot: bool,
) -> Message:
    if (m := await Message.exists(id=message_id)) is not None:
        return m

    await goc_member(guild_id, author_id, is_author_bot)

    try:
        return await Message(
            guild_id=guild_id,
            author_id=author_id,
            channel_id=channel_id,
            id=message_id,
            is_nsfw=is_nsfw,
        ).create()
    except UniqueViolationError:
        return await Message.fetch(id=message_id)


class Message(apgorm.Model):
    __slots__: Iterable[str] = tuple()

    id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)
    channel_id = types.Numeric().field().with_converter(DecimalC)
    author_id = types.Numeric().field().with_converter(DecimalC)

    is_nsfw = types.Boolean().field()

    forced_to = (
        types.Array(types.Numeric())
        .field(default=[])
        .with_converter(DecimalArrayC)
    )
    trashed = types.Boolean().field(default=False)
    trash_reason = types.VarChar(32).nullablefield()
    frozen = types.Boolean().field(default=False)

    guild_id_fk = apgorm.ForeignKey(guild_id, Guild.id)
    author_id_fk = apgorm.ForeignKey(author_id, User.id)

    primary_key = (id,)
