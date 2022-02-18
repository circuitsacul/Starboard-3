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

from typing import TYPE_CHECKING, Any, cast

import crescent
import hikari

from starboard.config import CONFIG
from starboard.core.config import StarboardConfig
from starboard.database import Guild, Starboard, goc_guild, validate_sb_changes
from starboard.exceptions import StarboardErr, StarboardNotFound
from starboard.views import Confirm
from starboard.undefined import UNDEF

from ._checks import has_guild_perms
from ._converters import any_emoji_list, any_emoji_str, disid
from ._sb_config import EditStarboardConfig
from ._utils import pretty_emoji_str, pretty_sb_config, optiond

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
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        exists = await Starboard.exists(id=self.channel.id)
        if exists:
            await ctx.respond(
                f"<#{self.channel.id}> is already a starboard.", ephemeral=True
            )
            return

        guild = await goc_guild(ctx.guild_id)
        ip = guild.premium_end is not None

        limit = CONFIG.max_starboards if ip else CONFIG.np_max_starboards
        count = await Starboard.count(guild_id=ctx.guild_id)
        if count >= limit:
            raise StarboardErr(
                f"You can only have up to {limit} starboards."
                + (
                    " You can increase this limit with premium."
                    if not ip
                    else ""
                )
            )

        await Starboard(id=self.channel.id, guild_id=ctx.guild_id).create()
        bot.cache.invalidate_star_emojis(ctx.guild_id)

        await ctx.respond(f"Created starboard <#{self.channel.id}>.")


@plugin.include
@starboards.child
@crescent.command(name="delete", description="Remove a starboard")
class DeleteStarboard:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "Starboard to delete.", default=None
    )
    starboard_id = crescent.option(
        str, "Starboard to delete, by ID", default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        chid = (
            self.starboard.id if self.starboard else disid(self.starboard_id)
        )
        if not chid:
            raise StarboardErr(
                "Please specify either a channel or channel ID."
            )

        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
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
            .where(id=chid, guild_id=ctx.guild_id)
            .execute()
        )
        bot.cache.invalidate_star_emojis(ctx.guild_id)
        if len(res) == 0:
            await msg.edit(StarboardNotFound(chid).msg, components=[])
            return

        await msg.edit(f"Deleted starboard <#{chid}>.", components=[])


@plugin.include
@starboards.child
@crescent.command(name="edit", description="Modify a starboard")
class EditStarboard(EditStarboardConfig):
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to edit"
    )

    # this option cannot be implemented for overrides, so we put it on the
    # starboard edit command instead of the superclass
    private = optiond(
        bool,
        "Whether to prevent `random` and `moststarred` from using this "
        "starboard",
    )

    def _options(self) -> dict[str, Any]:
        d = super()._options()
        if self.private is not UNDEF.UNDEF:
            d["private"] = self.private
        return d

    async def callback(self, ctx: crescent.Context) -> None:
        params = self._options()
        validate_sb_changes(**params)

        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        for k, v in params.items():
            setattr(s, k, v)

        await s.save()
        await ctx.respond(f"Settings for <#{s.id}> updated.")


emojis = starboards.sub_group("emojis", "Modify emojis for a starboard")


@plugin.include
@emojis.child
@crescent.command(name="set", description="Set the star emojis")
class SetStarEmoji:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to set the star emojis for"
    )
    emojis = crescent.option(str, "A list of emojis to use")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        guild = await Guild.fetch(id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_star_emojis if ip else CONFIG.np_max_star_emojis

        emojis = any_emoji_list(self.emojis)
        if len(emojis) > limit:
            raise StarboardErr(
                f"You an only have up to {limit} emojis per starboard."
                + (" Get premium to increase this." if not ip else "")
            )
        s.star_emojis = list(emojis)
        await s.save()
        bot.cache.invalidate_star_emojis(ctx.guild_id)
        await ctx.respond("Done.")


@plugin.include
@emojis.child
@crescent.command(name="add", description="Add a star emoji")
class AddStarEmoji:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to add the star emoji to"
    )
    emoji = crescent.option(str, "The star emoji to add")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)
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

        guild = await Guild.fetch(id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_star_emojis if ip else CONFIG.np_max_star_emojis

        if len(emojis) >= limit:
            raise StarboardErr(
                f"You an only have up to {limit} emojis per starboard."
                + (" Get premium to increase this." if not ip else "")
            )

        emojis.append(e)
        s.star_emojis = emojis
        await s.save()
        bot.cache.invalidate_star_emojis(ctx.guild_id)
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
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id

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
        bot.cache.invalidate_star_emojis(ctx.guild_id)
        await ctx.respond("Done.")
