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

from typing import TYPE_CHECKING

import hikari

from starboard.database import Message, SBMessage, Starboard

from .embed_message import embed_message, get_raw_message_text
from .emojis import stored_to_emoji

if TYPE_CHECKING:
    from starboard.bot import Bot


async def get_orig_message(message_id: int) -> Message | None:
    if sbm := await SBMessage.exists(sb_message_id=message_id):
        return await Message.fetch(id=sbm.message_id)

    if m := await Message.exists(id=message_id):
        return m

    return None


async def get_sbmsg_content(
    bot: Bot,
    starboard: Starboard,
    dis_orig_msg: hikari.Message | None,
    sql_orig_msg: Message,
    starcount: int,
) -> tuple[str, hikari.Embed | None]:
    def _display_emoji() -> hikari.UnicodeEmoji | hikari.CustomEmoji | None:
        return (
            stored_to_emoji(starboard.display_emoji, bot)
            if starboard.display_emoji is not None
            else None
        )

    if dis_orig_msg is not None:
        return await embed_message(
            bot,
            dis_orig_msg,
            starboard.guild_id,
            starboard.color or bot.config.color,
            _display_emoji(),
            starboard.use_nicknames,
            starboard.ping_author,
            starcount,
        )

    return (
        get_raw_message_text(
            sql_orig_msg.channel_id,
            sql_orig_msg.author_id,
            _display_emoji(),
            starboard.ping_author,
            starcount,
        ),
        None,
    )
