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

from starboard.config import CONFIG
from starboard.database import AutoStarChannel, Guild, goc_guild
from starboard.exceptions import ASCNotFound, StarboardErr
from starboard.undefined import UNDEF
from starboard.views import Confirm

from ._checks import has_guild_perms
from ._converters import any_emoji_list, any_emoji_str, disid
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

        guild = await goc_guild(ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_autostar if ip else CONFIG.np_max_autostar
        count = await AutoStarChannel.count(guild_id=ctx.guild_id)

        if count >= limit:
            raise StarboardErr(
                f"You can only have up to {limit} autostar channels."
                + (" Get premium to increase this limit." if not ip else "")
            )

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
        hikari.TextableGuildChannel,
        "The autostar channel to delete",
        default=None,
    )
    channel_id = crescent.option(
        str, "The autostar channel to delete, by ID", default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)

        chid = self.channel.id if self.channel else disid(self.channel_id)
        if not chid:
            raise StarboardErr(
                "Please specify either a channel or channel id."
            )

        confirm = Confirm(ctx.user.id, danger=True)
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
            .where(id=chid, guild_id=ctx.guild_id)
            .execute()
        )
        if not res:
            await msg.edit(ASCNotFound(chid).msg, components=[])
            return

        bot.database.asc.discard(chid)

        await msg.edit(f"Deleted autostar channel <#{chid}>", components=[])


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
            maxc = asc.max_chars if asc.max_chars is not None else "none"
            await ctx.respond(
                embed=bot.embed(
                    title=self.channel.name,
                    description=(
                        f"emojis: {es}\n"
                        f"min-chars: {asc.min_chars}\n"
                        f"max-chars: {maxc}\n"
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
        int,
        "The minimum length of messages",
        name="min-chars",
        max_value=CONFIG.max_minchars,
        min_value=0,
    )
    max_chars = optiond(
        int,
        "The maximum length of messages (use -1 to disable)",
        name="max-chars",
        max_value=CONFIG.max_maxchars,
        min_value=-1,
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

        if params.get("max_chars") == -1:
            params["max_chars"] = None

        for k, v in params.items():
            if v is UNDEF.UNDEF:
                continue
            setattr(asc, k, v)

        await asc.save()
        await ctx.respond(f"Updated settings for <#{asc.id}>.")


emojis = autostar.sub_group("emojis", "Modify emojis for an autostar channel")


@plugin.include
@emojis.child
@crescent.command(name="set", description="Set the emojis")
class SetEmoji:
    channel = crescent.option(
        hikari.TextableGuildChannel,
        "The autostar channel to set the emojis for",
    )
    emojis = crescent.option(str, "A list of emojis to use")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        asc = await AutoStarChannel.exists(id=self.channel.id)
        if not asc:
            raise ASCNotFound(self.channel.id)

        emojis = any_emoji_list(self.emojis)

        guild = await Guild.fetch(id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_asc_emojis if ip else CONFIG.np_max_asc_emojis

        if len(emojis) > limit:
            raise StarboardErr(
                f"You can only have up to {limit} emojis per autostar channel."
                + (" Get premium to increase this limit." if not ip else "")
            )

        asc.emojis = list(emojis)
        await asc.save()
        await ctx.respond("Done.")


@plugin.include
@emojis.child
@crescent.command(name="add", description="Add an emoji")
class AddEmoji:
    channel = crescent.option(
        hikari.TextableGuildChannel, "The autostar channel to add the emoji to"
    )
    emoji = crescent.option(str, "The emoji to add")

    async def callback(self, ctx: crescent.Context) -> None:
        asc = await AutoStarChannel.exists(id=self.channel.id)
        if not asc:
            raise ASCNotFound(self.channel.id)

        e = any_emoji_str(self.emoji)
        emojis = list(asc.emojis)
        if e in emojis:
            await ctx.respond(
                f"{e} is already an emoji for <#{asc.id}>.", ephemeral=True
            )
            return

        guild = await Guild.fetch(id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_asc_emojis if ip else CONFIG.np_max_asc_emojis

        if len(emojis) >= limit:
            raise StarboardErr(
                f"You can only have up to {limit} emojis per autostar channel."
                + (" Get premium to increase this limit." if not ip else "")
            )

        emojis.append(e)
        asc.emojis = emojis
        await asc.save()
        await ctx.respond("Done.")


@plugin.include
@emojis.child
@crescent.command(name="remove", description="Remove an emoji")
class RemoveEmoji:
    channel = crescent.option(
        hikari.TextableGuildChannel,
        "The autostar channel to remove the emoji from",
    )
    emoji = crescent.option(str, "The star emoji to remove")

    async def callback(self, ctx: crescent.Context) -> None:
        asc = await AutoStarChannel.exists(id=self.channel.id)
        if not asc:
            raise ASCNotFound(self.channel.id)

        e = any_emoji_str(self.emoji)
        emojis = list(asc.emojis)
        if e not in emojis:
            await ctx.respond(
                f"{e} is not an emoji on <#{asc.id}>", ephemeral=True
            )
            return

        emojis.remove(e)
        asc.emojis = emojis
        await asc.save()
        await ctx.respond("Done.")
