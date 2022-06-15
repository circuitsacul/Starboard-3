from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import asyncpg
import crescent
import hikari

from starboard.commands._converters import channel_list
from starboard.config import CONFIG
from starboard.core.config import StarboardConfig
from starboard.database import Guild, Override, Starboard, validate_sb_changes
from starboard.exceptions import OverrideNotFound, StarboardError

from ._autocomplete import override_autocomplete, starboard_autocomplete
from ._checks import has_guild_perms
from ._converters import any_emoji_list, clean_name
from ._sb_config import (
    BaseEditStarboardBehavior,
    BaseEditStarboardEmbedStyle,
    BaseEditStarboardRequirements,
    BaseEditStarboardStyle,
)
from ._utils import pretty_channel_str, pretty_sb_config

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("overrides")
overrides = crescent.Group(
    "overrides",
    "Manage setting overrides",
    hooks=[has_guild_perms(hikari.Permissions.MANAGE_GUILD)],
)


@plugin.include
@overrides.child
@crescent.command(name="view", description="View setting overrides")
class ViewSettingOverrides:
    name = crescent.option(
        str,
        "The override to view",
        default=None,
        autocomplete=override_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        if self.name:
            ov = await Override.from_name(ctx.guild_id, self.name)
            sb = await Starboard.fetch(id=ov.starboard_id)

            config = StarboardConfig(sb, [ov])
            options = pretty_sb_config(config, bot, ov.overrides.keys())

            cs = pretty_channel_str(bot, ov.channel_ids)
            embed = bot.embed(
                title=f"Override {self.name}",
                description=(
                    f"These are the settings for {sb.name} in the "
                    f"channels {cs}."
                ),
            )

            embed.add_field(
                name="General Style", value=options.general_style, inline=True
            )
            embed.add_field(
                name="Embed Style", value=options.embed_style, inline=True
            )
            embed.add_field(
                name="Requirements", value=options.requirements, inline=True
            )
            embed.add_field(
                name="Behavior", value=options.behavior, inline=True
            )

        else:
            q = Override.fetch_query()
            q.where(guild_id=ctx.guild_id)
            ovs = await q.fetchmany()

            if not ovs:
                await ctx.respond(
                    "This server has no overrides.", ephemeral=True
                )
                return

            ret: list[str] = []
            for ov in ovs:
                sb = await Starboard.fetch(id=ov.starboard_id)
                ret.append(
                    f"{ov.name}: **{len(ov.overrides)}** overwritten settings "
                    f"for {sb.name} in {len(ov.channel_ids)} channels"
                )

            embed = bot.embed(
                title="Setting Overrides", description="\n".join(ret)
            )

        await ctx.respond(embed=embed)


@plugin.include
@overrides.child
@crescent.command(name="create", description="Create a setting override")
class CreateOverride:
    name = crescent.option(str, "The name of the override")
    channels = crescent.option(
        str, "A list of channels that this override applies to"
    )
    starboard = crescent.option(
        str,
        "The starboard this override applies to",
        autocomplete=starboard_autocomplete,
    )
    copy_from = crescent.option(
        str,
        "An existing override to copy options from",
        default=None,
        name="copy-from",
        autocomplete=override_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        starboard = await Starboard.from_name(ctx.guild_id, self.starboard)

        if self.copy_from is not None:
            ov = await Override.exists(
                guild_id=ctx.guild_id, name=self.copy_from
            )
            if not ov:
                raise OverrideNotFound(self.copy_from)

        else:
            ov = None

        count = await Override.count(
            guild_id=ctx.guild_id, starboard_id=starboard.id
        )
        if count >= CONFIG.max_ov_per_starboard:
            raise StarboardError(
                f"You can only have up to {CONFIG.max_ov_per_starboard} "
                "overrides per starboard."
            )

        name = clean_name(self.name)
        o = Override(
            guild_id=ctx.guild_id,
            name=name,
            starboard_id=starboard.id,
            channel_ids=channel_list(self.channels, bot).valid,
            _overrides=ov._overrides if ov else "{}",
        )
        try:
            await o.create()
        except asyncpg.UniqueViolationError:
            raise StarboardError(
                f"There is already an override with the name '{name}'."
            ) from None

        await ctx.respond(f"Created override with name '{name}'.")


@plugin.include
@overrides.child
@crescent.command(name="delete", description="Delete a setting override")
class DeleteOverride:
    name = crescent.option(
        str, "The name of the override", autocomplete=override_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        ov = await Override.from_name(ctx.guild_id, self.name)
        await ov.delete()
        await ctx.respond(f"Deleted setting override '{self.name}'.")


async def _update_override(
    name: str, guild_id: int, params: dict[str, Any]
) -> None:
    ov = await Override.from_name(guild_id, name)

    validate_sb_changes(**params)

    opt = ov.overrides
    for k, v in params.items():
        opt[k] = v
    ov.overrides = opt

    await ov.save()


edit = overrides.sub_group("edit", description="Edit a starboard")


@plugin.include
@edit.child
@crescent.command(name="behavior", description="Edit a starboard's behavior")
class EditStarboardBehavior(BaseEditStarboardBehavior):
    name = crescent.option(
        str, "The override to edit", autocomplete=override_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await _update_override(self.name, ctx.guild_id, self._options())
        await ctx.respond(f"Settings for override '{self.name}' updated.")


@plugin.include
@edit.child
@crescent.command(name="embed", description="Edit a starboard's embed style")
class EditStarboardEmbedStyle(BaseEditStarboardEmbedStyle):
    name = crescent.option(
        str, "The override to edit", autocomplete=override_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await _update_override(self.name, ctx.guild_id, self._options())
        await ctx.respond(f"Settings for override '{self.name}' updated.")


@plugin.include
@edit.child
@crescent.command(
    name="requirements", description="Edit a starboard's requirements"
)
class EditStarboardRequirements(BaseEditStarboardRequirements):
    name = crescent.option(
        str, "The override to edit", autocomplete=override_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await _update_override(self.name, ctx.guild_id, self._options())
        await ctx.respond(f"Settings for override '{self.name}' updated.")


@plugin.include
@edit.child
@crescent.command(name="style", description="Edit a starboard's style")
class EditStarboardStyle(BaseEditStarboardStyle):
    name = crescent.option(
        str, "The override to edit", autocomplete=override_autocomplete
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await _update_override(self.name, ctx.guild_id, self._options())
        await ctx.respond(f"Settings for override '{self.name}' updated.")


@plugin.include
@overrides.child
@crescent.command(
    name="reset", description="Reset specific settings to their defaults"
)
class ResetOverrideSettings:
    name = crescent.option(
        str, "The name of the override", autocomplete=override_autocomplete
    )
    options = crescent.option(str, "A list of settings to reset")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        ov = await Override.from_name(ctx.guild_id, self.name)

        options = {
            o.strip().strip(",").replace("-", "_")
            for o in self.options.split()
        }

        ovd = ov.overrides
        c = 0
        for o in options:
            if o == "cooldown":  # special edge case, sadly
                del ovd["cooldown_count"]
                del ovd["cooldown_period"]
                c += 1
            elif o in ovd:
                del ovd[o]
                c += 1
        ov.overrides = ovd
        await ov.save()
        await ctx.respond(f"Reset {c} settings for override '{ov.name}'.")


@plugin.include
@overrides.child
@crescent.command(name="rename", description="Rename an override")
class RenameOverride:
    orig = crescent.option(
        str,
        "The original name of the override",
        name="original-name",
        autocomplete=override_autocomplete,
    )
    new = crescent.option(str, "The new name of the override", name="new-name")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        ov = await Override.from_name(ctx.guild_id, self.orig)
        name = clean_name(self.new)
        ov.name = name
        try:
            await ov.save()
        except asyncpg.UniqueViolationError:
            raise StarboardError(
                f"There is already an override with the name '{name}'."
            ) from None
        await ctx.respond(f"Renamed the override '{self.orig}' to '{name}'.")


@plugin.include
@overrides.child
@crescent.command(
    name="set-channels", description="Set the channels for an override"
)
class SetOverrideChannels:
    name = crescent.option(
        str, "The name of the override", autocomplete=override_autocomplete
    )
    channels = crescent.option(str, "The channels to use for the override")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        ov = await Override.from_name(ctx.guild_id, self.name)
        ov.channel_ids = list(channel_list(self.channels, bot).valid)
        await ov.save()
        await ctx.respond(f"Updated the channels for override '{self.name}'.")


@plugin.include
@overrides.child
@crescent.command(
    name="remove-channels", description="Removes channels from an override"
)
class RemoveOverrideChannels:
    name = crescent.option(
        str, "The name of the override", autocomplete=override_autocomplete
    )
    channels = crescent.option(str, "The channels to remove from the override")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        ov = await Override.from_name(ctx.guild_id, self.name)
        chlist = channel_list(self.channels, bot)
        ov.channel_ids = list(
            set(ov.channel_ids)
            .difference(chlist.valid)
            .difference(chlist.invalid)
        )
        await ov.save()
        await ctx.respond(f"Updated the channels for override '{self.name}'.")


@plugin.include
@overrides.child
@crescent.command(
    name="add-channels", description="Adds channel to an override"
)
class AddOverrideChannels:
    name = crescent.option(
        str, "The name of the override", autocomplete=override_autocomplete
    )
    channels = crescent.option(str, "The channels to use for the override")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        ov = await Override.from_name(ctx.guild_id, self.name)
        ov.channel_ids = list(
            set(ov.channel_ids).union(channel_list(self.channels, bot).valid)
        )
        await ov.save()
        await ctx.respond(f"Updated the channels for override '{self.name}'.")


vote_emojis = overrides.sub_group(
    "emojis", "Modify the upvote/downvote emojis for an override"
)


@plugin.include
@vote_emojis.child
@crescent.command(name="set-upvote", description="Set the upvote emojis")
class SetUpvoteEmojis:
    override = crescent.option(
        str,
        "The override to set the upvote emojis for",
        autocomplete=override_autocomplete,
    )
    emojis = crescent.option(str, "A list of emojis to use")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        ov = await Override.from_name(ctx.guild_id, self.override)
        guild = await Guild.fetch(guild_id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_vote_emojis if ip else CONFIG.np_max_vote_emojis

        ov_data = ov.overrides

        upvote_emojis = any_emoji_list(self.emojis)
        downvote_emojis = set(ov_data.get("downvote_emojis", []))
        downvote_emojis.difference_update(upvote_emojis)
        if len(upvote_emojis) + len(downvote_emojis) > limit:
            raise StarboardError(
                f"You an only have up to {limit} emojis per starboard."
                + ("" if ip else " Get premium to increase this.")
            )

        ov_data["upvote_emojis"] = list(upvote_emojis)
        ov_data["downvote_emojis"] = list(downvote_emojis)
        ov.overrides = ov_data
        await ov.save()
        bot.cache.invalidate_vote_emojis(ctx.guild_id)
        await ctx.respond("Done.")


@plugin.include
@vote_emojis.child
@crescent.command(name="set-downvote", description="Set the downvote emojis")
class SetDownvoteEmojis:
    override = crescent.option(
        str,
        "The override to set the downvote emojis for",
        autocomplete=override_autocomplete,
    )
    emojis = crescent.option(str, "A list of emojis to use")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id
        ov = await Override.from_name(ctx.guild_id, self.override)
        guild = await Guild.fetch(guild_id=ctx.guild_id)
        ip = guild.premium_end is not None
        limit = CONFIG.max_vote_emojis if ip else CONFIG.np_max_vote_emojis

        ov_data = ov.overrides

        downvote_emojis = any_emoji_list(self.emojis)
        upvote_emojis = set(ov_data.get("upvote_emojis", []))
        upvote_emojis.difference_update(downvote_emojis)
        if len(downvote_emojis) + len(upvote_emojis) > limit:
            raise StarboardError(
                f"You an only have up to {limit} emojis per starboard."
                + ("" if ip else " Get premium to increase this.")
            )

        ov_data["downvote_emojis"] = list(downvote_emojis)
        ov_data["upvote_emojis"] = list(upvote_emojis)
        ov.overrides = ov_data
        await ov.save()
        bot.cache.invalidate_vote_emojis(ctx.guild_id)
        await ctx.respond("Done.")
