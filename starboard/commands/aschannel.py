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
from asyncpg import UniqueViolationError

from starboard.database import AutoStarChannel
from starboard.exceptions import ASCNotFound, StarboardErr
from starboard.undefined import UNDEF
from starboard.views import Confirm

from ._checks import has_guild_perms
from ._utils import optiond, pretty_emoji_str

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("aschannel")


autostar = crescent.Group(
    "autostar",
    "Manage autostar channels",
    hooks=[has_guild_perms(hikari.Permissions.MANAGE_GUILD)],
)


@plugin.include
@autostar.child
@crescent.command(name="create", description="Create an autostar channel")
class CreateAutoStar:
    channel = crescent.option(
        hikari.TextableGuildChannel, "The channel to make an autostar channel"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)

        assert ctx.guild_id
        try:
            await AutoStarChannel(
                id=self.channel.id, guild_id=ctx.guild_id
            ).create()
        except UniqueViolationError:
            raise StarboardErr(
                f"<#{self.channel.id}> is already an autostar channel."
            )

        bot.database.asc.add(self.channel.id)

        await ctx.respond(f"<#{self.channel.id}> is now an autostar channel.")


@plugin.include
@autostar.child
@crescent.command(name="delete", description="Delete an autostar channel")
class DeleteAutoStar:
    channel = crescent.option(
        hikari.TextableGuildChannel, "The autostar channel to delete"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)

        confirm = Confirm(ctx.user.id)
        msg = await ctx.respond(
            "Are you sure? All data will be lost **permanently**.",
            components=confirm.build(),
            ensure_message=True,
        )
        confirm.start(msg)
        await confirm.wait()

        if not confirm.result:
            await msg.edit("Cancelled.", components=[])
            return

        res = (
            await AutoStarChannel.delete_query()
            .where(id=self.channel.id)
            .execute()
        )
        if not res:
            await msg.edit(ASCNotFound(self.channel.id).msg, components=[])
            return

        bot.database.asc.discard(self.channel.id)

        await msg.edit(
            f"Deleted autostar channel <#{self.channel.id}>", components=[]
        )


@plugin.include
@autostar.child
@crescent.command(
    name="view", description="View the configuration for autostar channels"
)
class ViewAutoStar:
    channel = crescent.option(
        hikari.TextableGuildChannel,
        "The autostar channel to view settings for",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        if self.channel:
            asc = await AutoStarChannel.exists(id=self.channel.id)
            if not asc:
                raise ASCNotFound(self.channel.id)

            es = pretty_emoji_str(*asc.emojis, bot=bot)
            await ctx.respond(
                embed=bot.embed(
                    title=self.channel.name,
                    description=(
                        f"emojis: {es}\n"
                        f"min-chars: {asc.min_chars}\n"
                        f"max-chars: {asc.max_chars or 'none'}\n"
                        f"require-image: {asc.require_image}\n"
                        f"delete-invalid: {asc.delete_invalid}\n"
                    ),
                )
            )

        else:
            ascs = (
                await AutoStarChannel.fetch_query()
                .where(guild_id=ctx.guild_id)
                .fetchmany()
            )

            if not ascs:
                raise StarboardErr("This server has no autostar channels.")

            lines: list[str] = []
            for asc in ascs:
                channel = bot.cache.get_guild_channel(asc.id)
                if not channel:
                    name = f"Deleted Channel {asc.id}"
                else:
                    assert channel.name
                    name = channel.name

                es = pretty_emoji_str(*asc.emojis, bot=bot)
                lines.append(f"{name}: {es}")

            embed = bot.embed(
                title="Autostar Channels", description="\n".join(lines)
            )
            await ctx.respond(embed=embed)


@plugin.include
@autostar.child
@crescent.command(name="edit", description="Edit an autostar channel")
class EditAutoStar:
    channel = crescent.option(
        hikari.TextableGuildChannel, "The autostar channel to edit"
    )

    min_chars = optiond(
        int, "The minimum length of messages", name="min-chars"
    )
    max_chars = optiond(
        int, "The maximum length of messages", name="max-chars"
    )
    require_image = optiond(
        bool, "Whether images must include images", name="require-image"
    )
    delete_invalid = optiond(
        bool,
        "Whether to delete messages that don't meet requirements",
        name="delete-invalid",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        params = self.__dict__.copy()
        del params["channel"]

        asc = await AutoStarChannel.exists(id=self.channel.id)
        if not asc:
            raise ASCNotFound(self.channel.id)

        for k, v in params.items():
            if v is UNDEF.UNDEF:
                continue
            setattr(asc, k, v)

        await asc.save()
        await ctx.respond(f"Updated settings for <#{asc.id}>.")
