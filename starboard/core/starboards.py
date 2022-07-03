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

import asyncio
import traceback
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

import hikari
from apgorm import sql
from pycooldown import FixedCooldown

from starboard.config import CONFIG
from starboard.database import Guild, Message, SBMessage, Starboard, Vote

from .config import StarboardConfig, get_config
from .has_image import has_image
from .messages import get_sbmsg_content

if TYPE_CHECKING:
    from starboard.bot import Bot


LOCK: set[int] = set()


async def refresh_message(
    bot: Bot,
    orig_message: Message,
    sbids: Iterable[int] | None = None,
    force: bool = False,
    premium: bool | None = None,
) -> None:
    if orig_message.message_id in LOCK:
        return

    LOCK.add(orig_message.message_id)
    try:
        if premium is None:
            premium = (
                await Guild.fetch(guild_id=orig_message.guild_id)
            ).premium_end is not None

        await orig_message.refetch()
        if orig_message.trashed:
            await _handle_trashed_message(bot, orig_message)
        else:
            await _refresh_message(bot, orig_message, sbids, force, premium)
    finally:
        LOCK.remove(orig_message.message_id)


async def _handle_trashed_message(bot: Bot, orig_message: Message) -> None:
    starboards = {
        sb.id: sb
        for sb in await Starboard.fetch_query()
        .where(guild_id=orig_message.guild_id)
        .fetchmany()
    }
    for sid, sb in starboards.items():
        config = await get_config(sb, orig_message.channel_id)
        sbmsg = await SBMessage.exists(
            message_id=orig_message.message_id, starboard_id=sid
        )
        if not (sbmsg and sbmsg.sb_message_id):
            continue

        sbmsg_obj = await bot.cache.gof_message(
            sbmsg.starboard_id, sbmsg.sb_message_id
        )
        if not sbmsg_obj:
            continue

        await _edit(
            bot,
            config,
            sbmsg_obj,
            content=None,
            embeds=[
                hikari.Embed(
                    title="Trashed Message",
                    description="This message was trashed by a moderator.",
                )
            ],
            author_id=orig_message.author_id,
        )

    await asyncio.sleep(10)


async def _refresh_message(
    bot: Bot,
    orig_message: Message,
    sbids: Iterable[int] | None,
    force: bool,
    premium: bool,
) -> None:
    if sbids:
        _s = (
            await Starboard.fetch_query()
            .where(Starboard.id.eq(sql(sbids).any))
            .where(prem_locked=False)
            .fetchmany()
        )
    else:
        _s = (
            await Starboard.fetch_query()
            .where(guild_id=orig_message.guild_id)
            .where(prem_locked=False)
            .fetchmany()
        )
    configs = [await get_config(s, orig_message.channel_id) for s in _s]

    for c in configs:
        if not c.enabled and c.starboard.id not in orig_message.forced_to:
            continue
        try:
            await _refresh_message_for_starboard(
                bot, orig_message, c, force, premium
            )
        except Exception:
            traceback.print_exc()


async def _refresh_message_for_starboard(
    bot: Bot,
    orig_msg: Message,
    config: StarboardConfig,
    force: bool,
    premium: bool,
) -> None:
    if orig_msg.is_nsfw and config.starboard.id not in orig_msg.forced_to:
        sbchannel = await bot.cache.gof_guild_channel_wnsfw(
            config.starboard.channel_id
        )
        if sbchannel is None or sbchannel.is_nsfw is False:
            return

    orig_msg_obj = await bot.cache.gof_message(
        orig_msg.channel_id, orig_msg.message_id
    )

    points = await _get_points(orig_msg.message_id, config.starboard.id)
    action = _get_action(
        orig_msg, orig_msg_obj, config, points, orig_msg_obj is None
    )

    sbmsg = await SBMessage.exists(
        message_id=orig_msg.message_id, starboard_id=config.starboard.id
    )
    if (
        sbmsg is not None
        and sbmsg.last_known_point_count == points
        and not action.remove
        and not force
    ):
        return
    if not sbmsg:
        sbmsg = await SBMessage(
            message_id=orig_msg.message_id, starboard_id=config.starboard.id
        ).create()
    if sbmsg.sb_message_id is not None:
        sbmsg_obj = await bot.cache.gof_message(
            config.starboard.channel_id, sbmsg.sb_message_id
        )
    else:
        sbmsg_obj = None

    if action.add and sbmsg_obj is None:
        if orig_msg_obj:
            content, embed, embeds = await get_sbmsg_content(
                bot, config, orig_msg_obj, orig_msg, points, premium
            )
            assert embed
            sbmsg_obj = await _send(
                bot, config, content, [embed, *embeds], orig_msg.author_id
            )
            if sbmsg_obj:
                sbmsg.sb_message_id = sbmsg_obj.id
                await sbmsg.save()
                if config.autoreact_upvote:
                    await _add_reactions(bot, config.upvote_emojis, sbmsg_obj)
                if config.autoreact_downvote:
                    await _add_reactions(
                        bot, config.downvote_emojis, sbmsg_obj
                    )

    elif action.remove:
        if sbmsg_obj is not None:
            sbmsg.sb_message_id = None
            await _delete(bot, config, sbmsg_obj)

    elif sbmsg_obj is not None:
        # edit the message

        if orig_msg_obj:
            content, embed, embeds = await get_sbmsg_content(
                bot, config, orig_msg_obj, orig_msg, points, premium
            )
            assert embed
            if config.link_edits:
                await _edit(
                    bot,
                    config,
                    sbmsg_obj,
                    content,
                    [embed, *embeds],
                    orig_msg.author_id,
                )
            else:
                await _edit(
                    bot, config, sbmsg_obj, content, None, orig_msg.author_id
                )
        else:
            content, *_ = await get_sbmsg_content(
                bot, config, None, orig_msg, points, premium
            )
            await _edit(
                bot, config, sbmsg_obj, content, None, orig_msg.author_id
            )

    else:
        sbmsg.sb_message_id = None

    sbmsg.last_known_point_count = points
    await sbmsg.save()


async def _add_reactions(
    bot: Bot, emojis: list[str], sbmsg_obj: hikari.Message
) -> None:
    for emoji in emojis:
        _emoji: hikari.UnicodeEmoji | hikari.CustomEmoji
        try:
            __emoji = bot.cache.get_emoji(int(emoji))
            if __emoji is None:
                continue
            _emoji = __emoji
        except ValueError:
            _emoji = hikari.UnicodeEmoji.parse(emoji)
        with suppress(
            hikari.ForbiddenError, hikari.BadRequestError, hikari.NotFoundError
        ):
            await sbmsg_obj.add_reaction(_emoji)


EDIT_COOLDOWN: FixedCooldown[int] = FixedCooldown(
    *CONFIG.guild_message_edit_cooldown
)


async def _edit(
    bot: Bot,
    config: StarboardConfig,
    message: hikari.Message,
    content: str | None,
    embeds: list[hikari.Embed] | None,
    author_id: int,
) -> None:
    if EDIT_COOLDOWN.update_ratelimit(config.starboard.guild_id):
        return

    if message.author.id != bot.me.id:
        wh = await _webhook(bot, config, False)
        if not wh or wh.webhook_id != message.author.id:
            return

        await wh.edit_message(
            message,
            content=content or hikari.UNDEFINED,
            embeds=embeds or hikari.UNDEFINED,
            user_mentions=(author_id,),
        )

    else:
        await message.edit(
            content=content or hikari.UNDEFINED,
            embeds=embeds or hikari.UNDEFINED,
            user_mentions=(author_id,),
        )


DELETE_COOLDOWN: FixedCooldown[int] = FixedCooldown(
    *CONFIG.guild_message_delete_cooldown
)


async def _delete(
    bot: Bot, config: StarboardConfig, message: hikari.Message
) -> None:
    if DELETE_COOLDOWN.update_ratelimit(config.starboard.guild_id):
        return

    if message.author.id == bot.me.id:
        return await message.delete()

    wh = await _webhook(bot, config, False)
    if wh is None:
        # try anyways. will work if bot has manage_messages
        with suppress(hikari.ForbiddenError):
            await message.delete()
    else:
        await wh.delete_message(message)


SEND_COOLDOWN: FixedCooldown[int] = FixedCooldown(
    *CONFIG.guild_message_send_cooldown
)


async def _send(
    bot: Bot,
    config: StarboardConfig,
    content: str,
    embeds: list[hikari.Embed] | None,
    author_id: int,
) -> hikari.Message | None:
    if SEND_COOLDOWN.update_ratelimit(config.starboard.guild_id):
        return None

    webhook = await _webhook(bot, config)

    if webhook and config.use_webhook:
        with suppress(hikari.NotFoundError):
            botuser = bot.get_me()
            assert botuser
            return await webhook.execute(
                content,
                embeds=embeds or hikari.UNDEFINED,
                user_mentions=(author_id,),
            )

    with suppress(hikari.ForbiddenError, hikari.NotFoundError):
        return await bot.rest.create_message(
            config.starboard.channel_id,
            content,
            embeds=embeds or hikari.UNDEFINED,
            user_mentions=(author_id,),
        )
    return None


async def _webhook(
    bot: Bot, config: StarboardConfig, allow_create: bool = True
) -> hikari.ExecutableWebhook | None:
    create = allow_create and config.use_webhook
    wh = None
    if config.starboard.webhook_id is not None:
        wh = await bot.cache.gof_webhook(config.starboard.webhook_id)
        if not wh:
            config.starboard.webhook_id = None
            await config.starboard.save()

    if wh is not None:
        assert isinstance(wh, hikari.ExecutableWebhook)
        return wh

    if not create:
        return None

    try:
        wh = await bot.rest.create_webhook(
            config.starboard.channel_id,
            name=f"Starboard {config.starboard.name}",
            avatar=bot.me.avatar_url or hikari.UNDEFINED,
            reason="This starboard has use_webhook set to True.",
        )
    except (hikari.ForbiddenError, hikari.NotFoundError):
        return None

    config.starboard.webhook_id = wh.id
    await config.starboard.save()

    return wh


async def _get_points(orig_msg_id: int, starboard_id: int) -> int:
    upvotes = (
        await Vote.fetch_query()
        .where(
            message_id=orig_msg_id,
            starboard_id=starboard_id,
            is_downvote=False,
        )
        .count()
    )
    downvotes = (
        await Vote.fetch_query()
        .where(
            message_id=orig_msg_id, starboard_id=starboard_id, is_downvote=True
        )
        .count()
    )
    return upvotes - downvotes


@dataclass(order=True)
class _Actions:
    add: bool
    remove: bool


def _get_action(
    orig_msg: Message,
    orig_msg_obj: hikari.Message | None,
    config: StarboardConfig,
    points: int,
    deleted: bool,
) -> _Actions:
    add_trib: bool | None = None

    # check points
    if points >= config.required:
        add_trib = True
    elif points <= config.required_remove:
        add_trib = False

    # check deletion
    if deleted and config.link_deletes:
        add_trib = False

    # check image
    if orig_msg_obj and config.require_image and not has_image(orig_msg_obj):
        add_trib = False

    # check if frozen
    if orig_msg.frozen:
        add_trib = None

    # check if forced
    if config.starboard.id in orig_msg.forced_to:
        add_trib = True

    # return
    if add_trib is True:
        return _Actions(True, False)
    elif add_trib is None:
        return _Actions(False, False)
    else:
        return _Actions(False, True)
