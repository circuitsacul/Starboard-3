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

from starboard.core.gifs import get_gif_url
from starboard.utils import truncate, trunc_list
from starboard.constants import EMBED_DESC_LEN, EMBED_FIELD_LEN, ZWS

if TYPE_CHECKING:
    from starboard.bot import Bot


def get_raw_message_text(
    channel_id: int,
    author_id: int,
    display_emoji: hikari.UnicodeEmoji | hikari.CustomEmoji | None,
    ping_author: bool,
    point_count: int,
    frozen: bool,
    forced: bool,
) -> str:
    text = ""
    if display_emoji:
        text += display_emoji.mention + " "

    text += f"**{point_count} |** <#{channel_id}>"

    if ping_author:
        text += f" **(**<@{author_id}>**)**"

    if frozen:
        text += " ❄️"
    if forced:
        text += " 🔒"

    return text


async def embed_message(
    bot: Bot,
    message: hikari.Message,
    guild_id: int,
    color: int,
    display_emoji: hikari.CustomEmoji | hikari.UnicodeEmoji | None,
    server_profile: bool,
    ping_author: bool,
    point_count: int,
    frozen: bool,
    forced: bool,
) -> tuple[str, hikari.Embed, list[hikari.Embed]]:
    channel = await bot.cache.gof_guild_channel_wnsfw(message.channel_id)
    assert channel is not None
    nsfw = channel.is_nsfw
    assert nsfw is not None

    name, avatar = await _get_name_and_avatar(
        bot, guild_id, message.author, server_profile
    )

    embed = hikari.Embed(
        description=_extract_main_content(message),
        color=color,
        timestamp=message.created_at,
    ).set_author(name=name, icon=avatar)

    filestr = _extract_file_str(message)
    if filestr:
        embed.add_field(name=ZWS, value=filestr)

    embed.add_field(
        name=ZWS, value=f"[Go to Message]({message.make_link(guild_id)})"
    )

    image_urls = await _extract_images(bot, message)
    if image_urls and len(image_urls):
        embed.set_image(image_urls[0])

    await _extract_reply(bot, message, guild_id, server_profile, embed)

    return (
        get_raw_message_text(
            message.channel_id,
            message.author.id,
            display_emoji,
            ping_author,
            point_count,
            frozen,
            forced,
        ),
        embed,
        _extract_extra_embeds(message),
    )


async def _get_name_and_avatar(
    bot: Bot,
    guild: hikari.SnowflakeishOr[hikari.PartialGuild],
    user: hikari.User,
    server_profile: bool,
) -> tuple[str, hikari.URL]:
    if not server_profile:
        return (user.username, user.avatar_url or user.default_avatar_url)

    member = await bot.cache.gof_member(guild, user)
    if not member:
        return (user.username, user.avatar_url or user.default_avatar_url)

    return (
        member.nickname or member.username,
        member.guild_avatar_url
        or member.avatar_url
        or member.default_avatar_url,
    )


async def _extract_reply(
    bot: Bot,
    message: hikari.Message,
    guild_id: int,
    server_profile: bool,
    embed: hikari.Embed,
) -> None:
    if (ref := message.referenced_message) is not None:
        name, _ = await _get_name_and_avatar(
            bot, guild_id, ref.author, server_profile
        )
        embed.add_field(
            name=f"Replying To {name}",
            value=_extract_main_content(ref) or "*file only*",
        )


def _is_rich(embed: hikari.Embed) -> bool:
    if embed.title:
        return True
    if embed.description:
        return True
    if embed.fields:
        return True
    return False


async def _get_gifv(bot: Bot, embed: hikari.Embed) -> str | None:
    if _is_rich(embed) or embed.url is None:
        return None

    gif_url = await get_gif_url(bot, embed.url)
    if not gif_url:
        return None

    return gif_url


def _extract_main_content(message: hikari.Message) -> str | None:
    if message.content:
        return truncate(message.content, EMBED_DESC_LEN)
    return None


def _extract_extra_embeds(message: hikari.Message) -> list[hikari.Embed]:
    embeds: list[hikari.Embed] = []
    for e in message.embeds:
        if not _is_rich(e):
            continue
        new_em = hikari.Embed(
            title=e.title,
            description=e.description,
            url=e.url,
            color=e.color,
            timestamp=e.timestamp,
        )
        for f in e.fields:
            new_em.add_field(
                name=f.name,
                value=f.value,
                inline=f.is_inline,
            )
        if e.author:
            new_em.set_author(
                name=e.author.name,
                url=e.author.url,
                icon=e.author.icon,
            )
        if e.footer:
            new_em.set_footer(
                text=e.footer.text,
                icon=e.footer.icon
            )
        if e.image:
            new_em.set_image(e.image)
        if e.thumbnail:
            new_em.set_thumbnail(e.thumbnail)
        embeds.append(new_em)

    return embeds


def _extract_file_str(message: hikari.Message) -> str | None:
    files = [f"[{a.filename}]({a.url})\n" for a in message.attachments]
    files = trunc_list(files, EMBED_FIELD_LEN)

    return "".join(files) or None


async def _extract_images(bot: Bot, message: hikari.Message) -> list[str]:
    urls = [
        a.url
        for a in message.attachments
        if a.media_type is not None
        and a.media_type.lower().startswith("image")
    ]

    for embed in message.embeds:
        gif_url = await _get_gifv(bot, embed)
        if gif_url is not None:
            urls.append(gif_url)
        elif not _is_rich(embed):
            if embed.image:
                urls.append(embed.image.url)
            if embed.thumbnail:
                urls.append(embed.thumbnail.url)

    return urls
