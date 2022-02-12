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

from starboard.core.config import StarboardConfig, validate_changes
from starboard.database import Starboard, goc_guild
from starboard.exceptions import StarboardNotFound
from starboard.views import Confirm

from ._checks import has_guild_perms
from ._converters import any_emoji_str
from ._sb_config import EditStarboardConfig
from ._utils import pretty_emoji_str, pretty_sb_config

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("starboards")


starboards = crescent.Group(
    "starboards",
    "Manage Starboards",
    hooks=[has_guild_perms(hikari.Permissions.MANAGE_GUILD)],
)


@plugin.include
@starboards.child
@crescent.command(name="view", description="View a starboard")
class ViewStarboard:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to view", default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        if self.starboard is None:
            all_starboards = (
                await Starboard.fetch_query()
                .where(guild_id=ctx.guild_id)
                .fetchmany()
            )
            if len(all_starboards) == 0:
                await ctx.respond(
                    "There are no starboards in this server.", ephemeral=True
                )
                return

            embed = bot.embed(
                title="Starboards",
                description=(
                    "This shows all starboards and their most important "
                    "settings. To view all settings, run this command for a "
                    "specific starboard instead."
                ),
            )

            for sb in all_starboards:
                channel = bot.cache.get_guild_channel(sb.id)
                if not channel:
                    name = f"Deleted Channel {sb.id}"
                else:
                    assert channel.name is not None
                    name = channel.name

                emoji_str = pretty_emoji_str(*sb.star_emojis, bot=bot)
                embed.add_field(
                    name=name,
                    value=(
                        f"required: {sb.required}\n"
                        f"self-star: {sb.self_star}\n"
                        f"emojis: {emoji_str}"
                    ),
                    inline=True,
                )
            await ctx.respond(embed=embed)

        else:
            starboard = await Starboard.exists(id=self.starboard.id)
            if not starboard:
                raise StarboardNotFound(self.starboard.id)

            config = pretty_sb_config(StarboardConfig(starboard, None), bot)
            embed = bot.embed(title=self.starboard.name)
            embed.add_field(
                name="Appearance", value=config.appearance, inline=True
            )
            embed.add_field(
                name="Requirements", value=config.requirements, inline=True
            )
            embed.add_field(
                name="Behaviour", value=config.behaviour, inline=True
            )

            await ctx.respond(embed=embed)


@plugin.include
@starboards.child
@crescent.command(name="create", description="Add a starboard")
class CreateStarboard:
    channel = crescent.option(
        hikari.TextableGuildChannel, "Channel to use as starboard"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        exists = await Starboard.exists(id=self.channel.id)
        if exists:
            await ctx.respond(
                f"<#{self.channel.id}> is already a starboard.", ephemeral=True
            )
            return

        assert ctx.guild_id
        await goc_guild(ctx.guild_id)

        await Starboard(id=self.channel.id, guild_id=ctx.guild_id).create()

        await ctx.respond(f"Created starboard <#{self.channel.id}>.")


@plugin.include
@starboards.child
@crescent.command(name="delete", description="Remove a starboard")
class DeleteStarboard:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "Starboard to delete."
    )

    async def callback(self, ctx: crescent.Context) -> None:
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
            await Starboard.delete_query()
            .where(id=self.starboard.id)
            .execute()
        )
        if len(res) == 0:
            await msg.edit(
                StarboardNotFound(self.starboard.id).msg, components=[]
            )
            return

        await msg.edit(
            f"Deleted starboard <#{self.starboard.id}>.", components=[]
        )


@plugin.include
@starboards.child
@crescent.command(name="edit", description="Modify a starboard")
class EditStarboard(EditStarboardConfig):
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to edit"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        params = self._options()
        await validate_changes(**params)

        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        for k, v in params.items():
            setattr(s, k, v)

        await s.save()
        await ctx.respond(f"Settings for <#{s.id}> updated.")


emojis = starboards.sub_group("emojis", "Modify emojis for a starboard.")


@plugin.include
@emojis.child
@crescent.command(name="add", description="Add a star emoji")
class AddStarEmoji:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to add the star emoji to"
    )
    emoji = crescent.option(str, "The star emoji to add")

    async def callback(self, ctx: crescent.Context) -> None:
        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        e = any_emoji_str(self.emoji)
        emojis = list(s.star_emojis)
        if e in emojis:
            await ctx.respond(
                f"{e} is already a star emoji for <#{s.id}>.", ephemeral=True
            )
            return

        emojis.append(e)
        s.star_emojis = emojis
        await s.save()
        await ctx.respond("Done.")


@plugin.include
@emojis.child
@crescent.command(name="remove", description="Remove a star emoji")
class RemoveStarEmoji:
    starboard = crescent.option(
        hikari.TextableGuildChannel,
        "The starboard to remove the star emoji from",
    )
    emoji = crescent.option(str, "The star emoji to remove")

    async def callback(self, ctx: crescent.Context) -> None:
        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        e = any_emoji_str(self.emoji)
        emojis = list(s.star_emojis)
        if e not in emojis:
            await ctx.respond(
                f"{e} is not a star emoji on <#{s.id}>", ephemeral=True
            )
            return

        emojis.remove(e)
        s.star_emojis = emojis
        await s.save()
        await ctx.respond("Done.")
