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

from starboard.constants import EMBED_DESC_LEN, EMBED_FIELD_LEN, ZWS
from starboard.core.gifs import get_gif_url
from starboard.utils import rendered_content, trunc_list, truncate

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
        text += f"{display_emoji.mention} "

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
    gifs: bool,
    attachments_list: bool,
    jump_to_message: bool,
    replied_to: bool,
) -> tuple[str, hikari.Embed, list[hikari.Embed]]:
    name, avatar = await _get_name_and_avatar(
        bot, guild_id, message.author, server_profile
    )

    embed = hikari.Embed(
        description=_extract_main_content(message),
        color=color,
        timestamp=message.created_at,
    ).set_author(name=name, icon=avatar)

    if attachments_list and (filestr := _extract_file_str(message)):
        embed.add_field(name=ZWS, value=filestr)

    if jump_to_message:
        embed.add_field(
            name=ZWS, value=f"[Go to Message]({message.make_link(guild_id)})"
        )

    image_urls = await _extract_images(bot, message, gifs)
    if image_urls:
        embed.set_image(image_urls[0])

    if replied_to:
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
        if not isinstance(ref, hikari.Message):
            ref = await bot.cache.gof_message(ref.channel_id, ref.id)
            if ref is None:
                return None
        name, _ = await _get_name_and_avatar(
            bot, guild_id, ref.author, server_profile
        )
        embed.add_field(
            name=f"Replying To {name}",
            value=_extract_main_content(ref) or "*file only*",
        )


def _is_rich(embed: hikari.Embed) -> bool:
    return bool(embed.title or embed.description or embed.fields)


async def _get_gifv(bot: Bot, embed: hikari.Embed) -> str | None:
    if _is_rich(embed) or embed.url is None:
        return None

    gif_url = await get_gif_url(bot, embed.url)
    if not gif_url:
        return None

    return gif_url


def _extract_main_content(message: hikari.Message) -> str | None:
    if content := rendered_content(message):
        return truncate(content, EMBED_DESC_LEN)
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
            new_em.add_field(name=f.name, value=f.value, inline=f.is_inline)
        if e.author:
            new_em.set_author(
                name=e.author.name, url=e.author.url, icon=e.author.icon
            )
        if e.footer:
            new_em.set_footer(text=e.footer.text, icon=e.footer.icon)
        if e.image:
            new_em.set_image(e.image)
        if e.thumbnail:
            new_em.set_thumbnail(e.thumbnail)
        embeds.append(new_em)

    return embeds


def _extract_file_str(message: hikari.Message) -> str | None:
    files: list[str] = []
    for a in message.attachments:
        if _is_spoiler(a.filename):
            files.append(f"||[{a.filename}]({a.url})||\n")
        else:
            files.append(f"[{a.filename}]({a.url})\n")
    files = trunc_list(files, EMBED_FIELD_LEN)

    return "".join(files) or None


async def _extract_images(
    bot: Bot, message: hikari.Message, gifs: bool
) -> list[str]:
    urls = [
        a.url
        for a in message.attachments
        if a.media_type is not None
        and a.media_type.lower().startswith("image")
        and not _is_spoiler(a.filename)
    ]

    for embed in message.embeds:
        gif_url = await _get_gifv(bot, embed) if gifs else None
        if gif_url is not None:
            urls.append(gif_url)
        elif not _is_rich(embed):
            if embed.image and not _is_spoiler(embed.image.filename):
                urls.append(embed.image.url)
            if embed.thumbnail and not _is_spoiler(embed.thumbnail.filename):
                urls.append(embed.thumbnail.url)

    return urls


def _is_spoiler(name: str) -> bool:
    return name.startswith("SPOILER_")
