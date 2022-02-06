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

from typing import cast, TYPE_CHECKING

from hikari import Permissions
import crescent
import hikari

from starboard.exceptions import CommandErr
from starboard.core.starboards import refresh_message
from starboard.core.messages import get_orig_message

from ._checks import has_guild_perms
from ._converters import db_orig_message

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
@crescent.message_command(name="Freeze Message")
async def freeze_message(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    msg = await get_orig_message(message.id)
    if not msg:
        raise CommandErr("Message does not exist in database.")

    if msg.frozen:
        raise CommandErr("That message is already frozen.")

    msg.frozen = True
    await msg.save()
    await ctx.respond("Message frozen.", ephemeral=True)
    await refresh_message(cast("Bot", ctx.app), msg, force=True)


@plugin.include
@manage_messages
@crescent.message_command(name="Unfreeze Message")
async def unfreeze_message(
    ctx: crescent.Context, message: hikari.Message
) -> None:
    msg = await get_orig_message(message.id)
    if not msg or not msg.frozen:
        raise CommandErr("That message is not frozen.")

    msg.frozen = False
    await msg.save()
    await ctx.respond("Message unfrozen.", ephemeral=True)
    await refresh_message(cast("Bot", ctx.app), msg, force=True)


# TRASHING
@plugin.include
@utils.child
@crescent.command(
    name="trash",
    description="Trash a message so it won't appear on starboards.",
)
class TrashMessage:
    message_link = crescent.option(
        str, "Link to the message to trash", name="message-link"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        pass
