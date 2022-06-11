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

from starboard.database import Message, SBMessage

from .embed_message import embed_message, get_raw_message_text
from .emojis import stored_to_emoji

if TYPE_CHECKING:
    from starboard.bot import Bot
    from starboard.core.config import StarboardConfig


async def get_orig_message(message_id: int) -> Message | None:
    if sbm := await SBMessage.exists(sb_message_id=message_id):
        return await Message.fetch(message_id=sbm.message_id)

    if m := await Message.exists(message_id=message_id):
        return m

    return None


async def get_sbmsg_content(
    bot: Bot,
    config: StarboardConfig,
    dis_orig_msg: hikari.Message | None,
    sql_orig_msg: Message,
    points: int,
    premium: bool,
) -> tuple[str, hikari.Embed | None, list[hikari.Embed]]:
    def _display_emoji() -> hikari.UnicodeEmoji | hikari.CustomEmoji | None:
        return (
            stored_to_emoji(config.display_emoji, bot)
            if config.display_emoji is not None
            else None
        )

    frozen = sql_orig_msg.frozen
    forced = config.starboard.id in sql_orig_msg.forced_to

    if dis_orig_msg is not None:
        c, e, es = await embed_message(
            bot=bot,
            message=dis_orig_msg,
            guild_id=config.starboard.guild_id,
            color=config.color,
            display_emoji=_display_emoji(),
            server_profile=config.use_server_profile,
            ping_author=config.ping_author,
            point_count=points,
            frozen=frozen,
            forced=forced,
            gifs=premium,
            attachments_list=config.attachments_list,
            jump_to_message=config.jump_to_message,
            replied_to=config.replied_to,
        )
        if config.extra_embeds:
            return c, e, es
        return c, e, []

    return (
        get_raw_message_text(
            sql_orig_msg.channel_id,
            sql_orig_msg.author_id,
            _display_emoji(),
            config.ping_author,
            points,
            frozen,
            forced,
        ),
        None,
        [],
    )
