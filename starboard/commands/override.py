from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import asyncpg
import crescent
import hikari

from starboard.config import CONFIG
from starboard.core.config import StarboardConfig
from starboard.database import Override, Starboard, validate_sb_changes
from starboard.exceptions import (
    OverrideNotFound,
    StarboardError,
    StarboardNotFound,
)

from ._checks import has_guild_perms
from ._converters import channel_list
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
    name = crescent.option(str, "The override to view", default=None)

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        if self.name:
            ov = await Override.exists(guild_id=ctx.guild_id, name=self.name)
            if not ov:
                raise OverrideNotFound(self.name)

            sb = await Starboard.fetch(id=ov.starboard_id)

            config = StarboardConfig(sb, [ov])
            options = pretty_sb_config(config, bot, ov.overrides.keys())

            cs = pretty_channel_str(bot, ov.channel_ids)
            embed = bot.embed(
                title=f"Override {self.name}",
                description=(
                    f"These are the settings for <#{sb.id}> in the channels "
                    f"{cs}."
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

            await ctx.respond(embed=embed)
        else:
            q = Override.fetch_query()
            q.where(guild_id=ctx.guild_id)
            ovs = await q.fetchmany()

            if not ovs:
                await ctx.respond(
                    "This server has no overrides.", ephemeral=True
                )
                return

            embed = bot.embed(
                title="Setting Overrides",
                description="\n".join(
                    f"{o.name}: **{len(o.overrides)}** overwritten settings "
                    f"for <#{o.starboard_id}> in **{len(o.channel_ids)}** "
                    "channels."
                    for o in ovs
                ),
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
        hikari.TextableGuildChannel, "The starboard this override applies to"
    )
    copy_from = crescent.option(
        str,
        "An existing override to copy options from",
        default=None,
        name="copy-from",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        if self.copy_from is not None:
            ov = await Override.exists(
                guild_id=ctx.guild_id, name=self.copy_from
            )
            if not ov:
                raise OverrideNotFound(self.copy_from)

        else:
            ov = None

        count = await Override.count(
            guild_id=ctx.guild_id, starboard_id=self.starboard.id
        )
        if count >= CONFIG.max_ov_per_starboard:
            raise StarboardError(
                f"You can only have up to {CONFIG.max_ov_per_starboard} "
                "overrides per starboard."
            )

        o = Override(
            guild_id=ctx.guild_id,
            name=self.name,
            starboard_id=self.starboard.id,
            channel_ids=channel_list(self.channels, bot).valid,
            _overrides=ov._overrides if ov else "{}",
        )
        try:
            await o.create()
        except asyncpg.UniqueViolationError:
            raise StarboardError(
                f"There is already an override with the name '{self.name}'."
            )
        except asyncpg.ForeignKeyViolationError:
            raise StarboardNotFound(self.starboard.id)

        await ctx.respond(f"Created override with name '{self.name}'.")


@plugin.include
@overrides.child
@crescent.command(name="delete", description="Delete a setting override")
class DeleteOverride:
    name = crescent.option(str, "The name of the override")

    async def callback(self, ctx: crescent.Context) -> None:
        q = Override.delete_query()
        q.where(guild_id=ctx.guild_id)
        q.where(name=self.name)
        ret = await q.execute()

        if ret:
            await ctx.respond(f"Deleted setting override '{self.name}'.")
        else:
            raise OverrideNotFound(self.name)


async def _update_override(
    name: str, guild_id: int, params: dict[str, Any]
) -> None:
    ov = await Override.exists(guild_id=guild_id, name=name)
    if not ov:
        raise OverrideNotFound(name)

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
    name = crescent.option(str, "The override to edit")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await _update_override(self.name, ctx.guild_id, self._options())
        await ctx.respond(f"Settings for override '{self.name}' updated.")


@plugin.include
@edit.child
@crescent.command(name="embed", description="Edit a starboard's embed style")
class EditStarboardEmbedStyle(BaseEditStarboardEmbedStyle):
    name = crescent.option(str, "The override to edit")

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
    name = crescent.option(str, "The override to edit")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await _update_override(self.name, ctx.guild_id, self._options())
        await ctx.respond(f"Settings for override '{self.name}' updated.")


@plugin.include
@edit.child
@crescent.command(name="style", description="Edit a starboard's style")
class EditStarboardStyle(BaseEditStarboardStyle):
    name = crescent.option(str, "The override to edit")

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
    name = crescent.option(str, "The name of the override")
    options = crescent.option(str, "A list of settings to reset")

    async def callback(self, ctx: crescent.Context) -> None:
        ov = await Override.exists(guild_id=ctx.guild_id, name=self.name)
        if not ov:
            raise OverrideNotFound(self.name)

        options = set(
            o.strip().strip(",").replace("-", "_")
            for o in self.options.split()
        )
        ovd = ov.overrides
        c = 0
        for o in options:
            c += 1
            if o == "cooldown":  # special edge case, sadly
                del ovd["cooldown_count"]
                del ovd["cooldown_period"]
            elif o in ovd:
                del ovd[o]
        ov.overrides = ovd
        await ov.save()
        await ctx.respond(f"Reset {c} settings for override '{ov.name}'.")


@plugin.include
@overrides.child
@crescent.command(name="rename", description="Rename an override")
class RenameOverride:
    orig = crescent.option(
        str, "The original name of the override", name="original-name"
    )
    new = crescent.option(str, "The new name of the override", name="new-name")

    async def callback(self, ctx: crescent.Context) -> None:
        ov = await Override.exists(guild_id=ctx.guild_id, name=self.orig)
        if not ov:
            raise OverrideNotFound(self.orig)

        ov.name = self.new
        try:
            await ov.save()
        except asyncpg.UniqueViolationError:
            raise StarboardError(
                f"There is already an override with the name '{self.new}'."
            )
        await ctx.respond(
            f"Renamed the override '{self.orig}' to '{self.new}'."
        )


@plugin.include
@overrides.child
@crescent.command(
    name="set-channels", description="Set the channels for an override"
)
class SetOverrideChannels:
    name = crescent.option(str, "The name of the override")
    channels = crescent.option(str, "The channels to use for the override")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        ov = await Override.exists(guild_id=ctx.guild_id, name=self.name)
        if not ov:
            raise OverrideNotFound(self.name)

        ov.channel_ids = list(channel_list(self.channels, bot).valid)
        await ov.save()
        await ctx.respond(f"Updated the channels for override '{self.name}'.")


@plugin.include
@overrides.child
@crescent.command(
    name="remove-channels", description="Removes channels from an override"
)
class RemoveOverrideChannels:
    name = crescent.option(str, "The name of the override")
    channels = crescent.option(str, "The channels to remove from the override")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        ov = await Override.exists(guild_id=ctx.guild_id, name=self.name)
        if not ov:
            raise OverrideNotFound(self.name)

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
    name = crescent.option(str, "The name of the override")
    channels = crescent.option(str, "The channels to use for the override")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        ov = await Override.exists(guild_id=ctx.guild_id, name=self.name)
        if not ov:
            raise OverrideNotFound(self.name)

        ov.channel_ids = list(
            set(ov.channel_ids).union(channel_list(self.channels, bot).valid)
        )
        await ov.save()
        await ctx.respond(f"Updated the channels for override '{self.name}'.")
