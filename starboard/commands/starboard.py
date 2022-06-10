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

import asyncpg
import crescent
import hikari

from starboard.commands._converters import any_emoji_list
from starboard.config import CONFIG
from starboard.core.config import StarboardConfig
from starboard.database import (
    Guild,
    Override,
    Starboard,
    goc_guild,
    validate_sb_changes,
)
from starboard.exceptions import StarboardError
from starboard.undefined import UNDEF
from starboard.views import Confirm

from ._autocomplete import starboard_autocomplete
from ._checks import has_guild_perms
from ._sb_config import (
    BaseEditStarboardBehavior,
    BaseEditStarboardEmbedStyle,
    BaseEditStarboardRequirements,
    BaseEditStarboardStyle,
)
from ._utils import optiond, pretty_emoji_str, pretty_sb_config

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
        str,
        "The starboard to view",
        default=None,
        autocomplete=starboard_autocomplete,
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
            if not all_starboards:
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
                if sb.prem_locked:
                    name = f"{sb.name} (Locked)"
                else:
                    name = sb.name

                emoji_str = pretty_emoji_str(*sb.upvote_emojis, bot=bot)
                embed.add_field(
                    name=name,
                    value=(
                        f"channel: <#{sb.channel_id}>\n"
                        f"required: {sb.required}\n"
                        f"self-vote: {sb.self_vote}\n"
                        f"upvote-emojis: {emoji_str}"
                    ),
                    inline=True,
                )
            await ctx.respond(embed=embed)

        else:
            starboard = await Starboard.from_user_input(
                ctx.guild_id, self.starboard
            )
            overrides = await Override.count(starboard_id=starboard.id)

            config = pretty_sb_config(StarboardConfig(starboard, None), bot)
            embed = bot.embed(title=starboard.name)
            notes: list[str] = []
            if overrides:
                notes.append(
                    f"This starboard also has {overrides} channel-specific "
                    "overrides."
                )
            if starboard.prem_locked:
                notes.append(
                    "This starboard exceeds the non-premium limit and is "
                    "locked. If you believe this is a mistake, run `/premium "
                    "locks refresh`."
                )
            notes.append(f"This starboard is in <#{starboard.channel_id}>.")
            if notes:
                embed.description = "\n\n".join(notes)
            embed.add_field(
                name="General Style", value=config.general_style, inline=True
            )
            embed.add_field(
                name="Embed Style", value=config.embed_style, inline=True
            )
            embed.add_field(
                name="Requirements", value=config.requirements, inline=True
            )
            embed.add_field(
                name="Behavior", value=config.behavior, inline=True
            )

            await ctx.respond(embed=embed)


@plugin.include
@starboards.child
@crescent.command(name="create", description="Add a starboard")
class CreateStarboard:
    channel = crescent.option(
        hikari.TextableGuildChannel, "Channel to use as starboard"
    )
    name = crescent.option(str, "The name of the starboard")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        guild = await goc_guild(ctx.guild_id)
        ip = guild.premium_end is not None

        limit = CONFIG.max_starboards if ip else CONFIG.np_max_starboards
        count = await Starboard.count(guild_id=ctx.guild_id)
        if count >= limit:
            raise StarboardError(
                f"You can only have up to {limit} starboards."
                + (
                    " You can increase this limit with premium."
                    if not ip
                    else ""
                )
            )

        try:
            sb = await Starboard(
                channel_id=self.channel.id,
                guild_id=ctx.guild_id,
                name=self.name,
            ).create()
        except asyncpg.UniqueViolationError:
            raise StarboardError(
                f"A starboard with the name '{self.name}' already exists."
            )

        bot.cache.invalidate_vote_emojis(ctx.guild_id)
        await ctx.respond(
            f"Created starboard '{sb.name}' in <#{self.channel.id}>."
        )


@plugin.include
@starboards.child
@crescent.command(name="delete", description="Remove a starboard")
class DeleteStarboard:
    starboard = crescent.option(
        str, "The starboard to delete", autocomplete=starboard_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        starboard = await Starboard.from_user_input(
            ctx.guild_id, self.starboard
        )

        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
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

        await starboard.delete()
        bot.cache.invalidate_vote_emojis(ctx.guild_id)
        await msg.edit(f"Deleted starboard '{starboard.name}'.", components=[])


@plugin.include
@starboards.child
@crescent.command(name="rename", description="Rename a starboard")
class RenameStarboard:
    starboard = crescent.option(
        str, "The starboard to rename", autocomplete=starboard_autocomplete
    )
    name = crescent.option(str, "The new name of the starboard")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        starboard = await Starboard.from_user_input(
            ctx.guild_id, self.starboard
        )
        old_name = starboard.name
        starboard.name = self.name
        try:
            await starboard.save()
        except asyncpg.UniqueViolationError:
            raise StarboardError(
                f"A starboard with the name '{self.name}' already exists."
            )

        await ctx.respond(
            f"Renamed starboard '{old_name}' to '{self.name}'."
        )


async def _update_starboard(
    guild: int, starboard: str, params: dict[str, Any]
) -> Starboard:
    validate_sb_changes(**params)
    s = await Starboard.from_user_input(guild, starboard)
    for k, v in params.items():
        setattr(s, k, v)
    await s.save()
    return s


edit = starboards.sub_group("edit", description="Edit a starboard")


@plugin.include
@edit.child
@crescent.command(name="behavior", description="Edit a starboard's behavior")
class EditStarboardBehavior(BaseEditStarboardBehavior):
    starboard = crescent.option(
        str, "The starboard to edit", autocomplete=starboard_autocomplete
    )

    # these options cannot be implemented for overrides, so we put it on the
    # starboard edit command instead of the superclass
    private = optiond(
        bool,
        "Whether to prevent `random` and `moststarred` from using this "
        "starboard",
    )
    xp_multiplier = optiond(
        float, "The XP multiplier for this starboard", name="xp-multiplier"
    )

    def _options(self) -> dict[str, Any]:
        d = super()._options()
        if self.private is not UNDEF.UNDEF:
            d["private"] = self.private
        if self.xp_multiplier is not UNDEF.UNDEF:
            d["xp_multiplier"] = self.xp_multiplier
        return d

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        s = await _update_starboard(
            ctx.guild_id, self.starboard, self._options()
        )
        await ctx.respond(f"Settings for '{s.name}' updated.")


@plugin.include
@edit.child
@crescent.command(name="embed", description="Edit a starboard's embed style")
class EditStarboardEmbedStyle(BaseEditStarboardEmbedStyle):
    starboard = crescent.option(
        str, "The starboard to edit", autocomplete=starboard_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        s = await _update_starboard(
            ctx.guild_id, self.starboard, self._options()
        )
        await ctx.respond(f"Settings for '{s.name}' updated.")


@plugin.include
@edit.child
@crescent.command(
    name="requirements", description="Edit a starboard's requirements"
)
class EditStarboardRequirements(BaseEditStarboardRequirements):
    starboard = crescent.option(
        str, "The starboard to edit", autocomplete=starboard_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        s = await _update_starboard(
            ctx.guild_id, self.starboard, self._options()
        )
        await ctx.respond(f"Settings for '{s.name}' updated.")


@plugin.include
@edit.child
@crescent.command(name="style", description="Edit a starboard's style")
class EditStarboardStyle(BaseEditStarboardStyle):
    starboard = crescent.option(
        str, "The starboard to edit", autocomplete=starboard_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        s = await _update_starboard(
            ctx.guild_id, self.starboard, self._options()
        )
        await ctx.respond(f"Settings for '{s.name}' updated.")


upvote_emojis = starboards.sub_group(
    "emojis", "Modify upvote/downvote emojis for a starboard"
)


@plugin.include
@upvote_emojis.child
@crescent.command(name="set-upvote", description="Set the upvote emojis")
class SetUpvoteEmojis:
    starboard = crescent.option(
        str,
        "The starboard to set the upvote emojis for",
        autocomplete=starboard_autocomplete,
    )
    emojis = crescent.option(str, "A list of emojis to use")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        s = await Starboard.from_user_input(ctx.guild_id, self.starboard)

        guild = await Guild.fetch(guild_id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_vote_emojis if ip else CONFIG.np_max_vote_emojis

        upvote_emojis = any_emoji_list(self.emojis)
        downvote_emojis = set(s.downvote_emojis)
        downvote_emojis.difference_update(upvote_emojis)
        if len(upvote_emojis) + len(downvote_emojis) > limit:
            raise StarboardError(
                f"You an only have up to {limit} emojis per starboard."
                + (" Get premium to increase this." if not ip else "")
            )
        s.upvote_emojis = list(upvote_emojis)
        s.downvote_emojis = list(downvote_emojis)
        await s.save()
        bot.cache.invalidate_vote_emojis(ctx.guild_id)
        await ctx.respond("Done.")


@plugin.include
@upvote_emojis.child
@crescent.command(name="set-downvote", description="Set the downvote emojis")
class SetDownvoteEmojis:
    starboard = crescent.option(
        str,
        "The starboard to set the downvote emojis for",
        autocomplete=starboard_autocomplete,
    )
    emojis = crescent.option(str, "A list of emojis to use")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        s = await Starboard.from_user_input(ctx.guild_id, self.starboard)

        guild = await Guild.fetch(guild_id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_vote_emojis if ip else CONFIG.np_max_vote_emojis

        downvote_emojis = any_emoji_list(self.emojis)
        upvote_emojis = set(s.upvote_emojis)
        upvote_emojis.difference_update(downvote_emojis)
        if len(upvote_emojis) + len(downvote_emojis) > limit:
            raise StarboardError(
                f"You an only have up to {limit} emojis per starboard."
                + (" Get premium to increase this." if not ip else "")
            )
        s.upvote_emojis = list(upvote_emojis)
        s.downvote_emojis = list(downvote_emojis)
        await s.save()
        bot.cache.invalidate_vote_emojis(ctx.guild_id)
        await ctx.respond("Done.")
