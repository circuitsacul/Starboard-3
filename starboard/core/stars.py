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
import hikari

from starboard.database import Message, Star, Starboard, User


async def is_star_valid_for(
    starboard: Starboard,
    orig_message: Message,
    author: User,
    star_adder: hikari.Member,
) -> bool:
    if starboard.locked:
        return False

    if (not starboard.self_star) and star_adder.id == orig_message.author_id:
        return False

    if author.is_bot and not starboard.allow_bots:
        return False

    if orig_message.trashed:
        return False

    if orig_message.frozen:
        return False

    return True


async def add_stars(
    orig_message_id: int,
    user_id: int,
    starboard_ids: list[int],
) -> None:
    for sbid in starboard_ids:
        if await Star.exists(
            message_id=orig_message_id,
            user_id=user_id,
            starboard_id=sbid,
        ):
            continue
        await Star(
            message_id=orig_message_id, user_id=user_id, starboard_id=sbid
        ).create()


async def remove_stars(
    orig_message_id: int,
    user_id: int,
    starboard_ids: list[int],
) -> None:
    await Star.delete_query().where(
        message_id=orig_message_id,
        user_id=user_id,
        starboard_id=apgorm.sql(starboard_ids).any,
    ).execute()
