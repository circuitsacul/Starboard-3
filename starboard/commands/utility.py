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

from typing import TYPE_CHECKING, cast

import crescent
import hikari
from hikari import Permissions

from starboard.core.messages import get_orig_message
from starboard.core.starboards import refresh_message
from starboard.database import Starboard, goc_message
from starboard.exceptions import CommandErr, StarboardNotFound

from ._checks import has_guild_perms
from ._converters import db_orig_message, msg_ch_id

if TYPE_CHECKING:
    from starboard.bot import Bot


manage_messages = crescent.hook(has_guild_perms(Permissions.MANAGE_MESSAGES))
plugin = crescent.Plugin("utility-commands")
utils = crescent.Group(
    "utils",
    "Utility Commands",
    hooks=[has_guild_perms(Permissions.MANAGE_MESSAGES)],
)


# FREEZING
@plugin.include
@utils.child
@crescent.command(name="freeze", description="Freeze a message")
class FreezeMessage:
    message_link = crescent.option(
        str, "A link to the message to freeze", name="message-link"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        msg = await db_orig_message(self.message_link)

        if msg.frozen:
            raise CommandErr("That message is already frozen.")

        msg.frozen = True
        await msg.save()
        await ctx.respond("Message frozen.", ephemeral=True)
        await refresh_message(cast("Bot", ctx.app), msg, force=True)


@plugin.include
@utils.child
@crescent.command(name="unfreeze", description="Unfreeze a message")
class UnfreezeMessage:
    message_link = crescent.option(
        str, "A link to the message to unfreeze", name="message-link"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        msg = await db_orig_message(self.message_link)

        if not msg.frozen:
            raise CommandErr("That message is not frozen.")

        msg.frozen = False
        await msg.save()
        await ctx.respond("Message unfrozen.", ephemeral=True)
        await refresh_message(cast("Bot", ctx.app), msg, force=True)


@plugin.include
@manage_messages
@crescent.message_command(name="Toggle Freeze")
async def toggle_freeze(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    msg = await get_orig_message(message.id)
    if not msg:
        raise CommandErr("That message does not exist in my database.")

    msg.frozen = not msg.frozen
    await msg.save()
    if msg.frozen:
        await ctx.respond("Message frozen.", ephemeral=True)
    else:
        await ctx.respond("Message unfrozen.", ephemeral=True)
    await refresh_message(cast("Bot", ctx.app), msg, force=True)


# TRASHING
@plugin.include
@utils.child
@crescent.command(
    name="trash",
    description="Trash a message so it won't appear on starboards",
)
class TrashMessage:
    message_link = crescent.option(
        str, "Link to the message to trash", name="message-link"
    )
    reason = crescent.option(
        str, "Reason for trashing the message", default="No reason"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        msg = await db_orig_message(self.message_link)

        if msg.trashed:
            raise CommandErr("That message is already trashed.")

        msg.trashed = True
        msg.trash_reason = self.reason
        await msg.save()
        await ctx.respond("Message trashed.", ephemeral=True)
        await refresh_message(cast("Bot", ctx.app), msg, force=True)


@plugin.include
@utils.child
@crescent.command(
    name="untrash",
    description="Untrash a message so it can appear on starboards",
)
class UntrashMessage:
    message_link = crescent.option(
        str, "Link to the message to untrash", name="message-link"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        msg = await db_orig_message(self.message_link)

        if not msg.trashed:
            raise CommandErr("That message is not trashed.")

        msg.trashed = False
        msg.trash_reason = None
        await msg.save()
        await ctx.respond("Message untrashed.", ephemeral=True)
        await refresh_message(cast("Bot", ctx.app), msg, force=True)


@plugin.include
@manage_messages
@crescent.message_command(name="Toggle Trash")
async def toggle_trashed(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    bot = cast("Bot", ctx.app)
    msg = await get_orig_message(message.id)

    if msg is None:
        assert ctx.guild_id
        channel = await bot.cache.gof_guild_channel_wnsfw(message.channel_id)
        assert channel
        assert channel.is_nsfw is not None
        msg = await goc_message(
            ctx.guild_id,
            channel.id,
            message.id,
            channel.is_nsfw,
            message.author.id,
            message.author.is_bot,
        )

    msg.trashed = not msg.trashed
    msg.trash_reason = "Trashed using message command" if msg.trashed else None
    await msg.save()
    await ctx.respond(
        "Message trashed." if msg.trashed else "Message untrashed.",
        ephemeral=True,
    )
    await refresh_message(bot, msg, force=True)


# FORCING
@plugin.include
@utils.child
@crescent.command(
    name="force", description="Force a message to one or more starboards"
)
class ForceMessage:
    message_link = crescent.option(
        str, "The message to force", name="message-link"
    )
    starboard = crescent.option(
        hikari.TextableGuildChannel,
        "The starboard to force the message to",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        msgid, chid = msg_ch_id(self.message_link)
        msg = await get_orig_message(msgid)

        if not msg:
            obj = await bot.cache.gof_message(chid, msgid)
            if not obj:
                raise CommandErr("I couldn't find that message.")

            channel = await bot.cache.gof_guild_channel_wnsfw(obj.channel_id)
            assert channel
            assert channel.is_nsfw is not None
            assert ctx.guild_id
            msg = await goc_message(
                ctx.guild_id,
                channel.id,
                obj.id,
                channel.is_nsfw,
                obj.author.id,
                obj.author.is_bot,
            )

        if self.starboard:
            sb = await Starboard.exists(id=self.starboard.id)
            if not sb:
                raise StarboardNotFound(self.starboard.id)
            sbids = [sb.id]
        else:
            assert ctx.guild_id
            sbids = [
                sb.id
                for sb in await Starboard.fetch_query()
                .where(guild_id=ctx.guild_id)
                .fetchmany()
            ]
            if not sbids:
                raise CommandErr(
                    "This server has no starboards, so you can't force this "
                    "message."
                )

        orig_force = set(msg.forced_to)
        orig_force.update(sbids)
        msg.forced_to = list(orig_force)
        await msg.save()
        await ctx.respond("Message forced.", ephemeral=True)
        await refresh_message(bot, msg, sbids, force=True)


@plugin.include
@utils.child
@crescent.command(
    name="unforce",
    description="Unforces a message from one or more starboards",
)
class UnforceMessage:
    message_link = crescent.option(
        str, "The message to unforce", name="message-link"
    )
    starboard = crescent.option(
        hikari.TextableGuildChannel,
        "The starboard to unforce from",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        msg = await db_orig_message(self.message_link)
        if not msg.forced_to:
            raise CommandErr("That message is not forced to any starboards.")

        if self.starboard:
            ft = set(msg.forced_to)
            if self.starboard.id not in ft:
                raise CommandErr(
                    "That message is not forced to that starboard."
                )

            ft.remove(self.starboard.id)
            msg.forced_to = list(ft)
            await msg.save()

            sbids = [self.starboard.id]

        else:
            msg.forced_to = []
            await msg.save()

            sbids = None

        await ctx.respond("Message unforced.", ephemeral=True)
        await refresh_message(cast("Bot", ctx.app), msg, sbids, force=True)


@plugin.include
@manage_messages
@crescent.message_command(name="Force Message")
async def force_message(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    bot = cast("Bot", ctx.app)

    sbids = [
        sb.id
        for sb in await Starboard.fetch_query()
        .where(guild_id=ctx.guild_id)
        .fetchmany()
    ]
    if not sbids:
        raise CommandErr(
            "There are no starboards in this server, so you can't force this "
            "message."
        )

    msg = await get_orig_message(message.id)
    if not msg:
        assert ctx.guild_id
        obj = await bot.cache.gof_message(message.channel_id, message.id)
        assert obj
        channel = await bot.cache.gof_guild_channel_wnsfw(obj.channel_id)
        assert channel
        assert channel.is_nsfw is not None

        msg = await goc_message(
            ctx.guild_id,
            channel.id,
            obj.id,
            channel.is_nsfw,
            obj.author.id,
            obj.author.is_bot,
        )

    msg.forced_to = sbids
    await msg.save()
    await ctx.respond("Message forced to all starboards.", ephemeral=True)
    await refresh_message(bot, msg, sbids, force=True)


@plugin.include
@manage_messages
@crescent.message_command(name="Unforce Message")
async def unforce_message(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    bot = cast("Bot", ctx.app)

    msg = await get_orig_message(message.id)
    if msg is None or not msg.forced_to:
        raise CommandErr("That message is not forced to any starboards.")

    msg.forced_to = list()
    await msg.save()
    await ctx.respond("Message unforced from all starboards.", ephemeral=True)
    await refresh_message(bot, msg, force=True)


# REFRESHING
@plugin.include
@utils.child
@crescent.command(name="refresh", description="Refresh a message")
class RefreshMessage:
    message_link = crescent.option(str, "The message to refresh")

    async def callback(self, ctx: crescent.Context) -> None:
        msg = await db_orig_message(self.message_link)
        await ctx.respond(
            "Message should update momentarily...", ephemeral=True
        )
        if msg:
            await refresh_message(cast("Bot", ctx.app), msg, force=True)


@plugin.include
@manage_messages
@crescent.message_command(name="Refresh Message")
async def refresh_message_cmd(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    bot = cast("Bot", ctx.app)
    msg = await get_orig_message(message.id)

    await ctx.respond("Message should update momentarily...", ephemeral=True)

    if msg:
        await refresh_message(bot, msg, force=True)
