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

if TYPE_CHECKING:
    from starboard.bot import Bot


ZWS = "​"


def get_raw_message_text(
    channel_id: int,
    display_emoji: hikari.UnicodeEmoji | hikari.CustomEmoji | None,
    point_count: int,
) -> str:
    text = ""
    if display_emoji:
        text += display_emoji.mention + " "

    text += f"**{point_count} |** <#{channel_id}>"

    return text


async def embed_message(
    bot: Bot,
    message: hikari.Message,
    guild_id: int,
    color: int,
    display_emoji: hikari.CustomEmoji | hikari.UnicodeEmoji | None,
    point_count: int,
) -> tuple[str, hikari.Embed]:
    channel = await bot.cache.gof_guild_channel_wnsfw(message.channel_id)
    assert channel is not None
    nsfw = channel.is_nsfw
    assert nsfw is not None

    embed = (
        hikari.Embed(
            description=_get_main_content(message),
            color=color,
            timestamp=message.created_at,
        )
        .set_author(
            name=message.author.username,
            icon=message.author.avatar_url
            or message.author.default_avatar_url,
        )
        .add_field(
            name=ZWS,
            value=f"[Go to Message]({message.make_link(guild_id)})",
        )
    )

    if (ref := message.referenced_message) is not None:
        embed.add_field(
            name=f"Replying To {ref.author.username}",
            value=(
                (ref.content + "\n\n" if ref.content else "")
                + f"[Go to Message]({ref.make_link(guild_id)})"
            ),
        )

    return (
        get_raw_message_text(message.channel_id, display_emoji, point_count),
        embed,
    )


def _get_main_content(message: hikari.Message) -> str:
    return message.content or "<nothing>"
