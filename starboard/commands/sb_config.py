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

from typing import TYPE_CHECKING, Type, TypeVar, cast

import crescent
import hikari

from starboard.database import Starboard, goc_guild
from starboard.exceptions import StarboardNotFound
from starboard.undefined import UNDEF
from starboard.views import Confirm

from ._checks import has_guild_perms
from ._converters import any_emoji_str, hex_color, none_or, convert
from ._utils import pretty_emoji_str

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("starboard-config")


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

            channel = bot.cache.get_guild_channel(self.starboard.id)
            if channel is None:
                name = f"Deleted Channel {self.starboard.id}"
            else:
                assert channel.name is not None
                name = channel.name
            embed = bot.embed(title=name)

            de = pretty_emoji_str(starboard.display_emoji, bot=bot)
            wha = (
                f"[view]({starboard.webhook_avatar})"
                if starboard.webhook_avatar
                else "none"
            )
            embed.add_field(
                name="Appearance",
                value=(
                    f"color: {starboard.color}\n"
                    f"display-emoji: {de}\n"
                    f"ping-author: {starboard.ping_author}\n"
                    f"use-nicknames: {starboard.use_nicknames}\n"
                    f"use-webhook: {starboard.use_webhook}\n"
                    f"webhook-name: {starboard.webhook_name}\n"
                    f"webhook-avatar: {wha}\n"
                ),
                inline=True,
            )

            se = pretty_emoji_str(*starboard.star_emojis, bot=bot)
            embed.add_field(
                name="Requirements",
                value=(
                    f"required: {starboard.required}\n"
                    f"required-remove: {starboard.required_remove}\n"
                    f"star-emojis: {se}\n"
                    f"self-star: {starboard.self_star}\n"
                    f"allow-bots: {starboard.allow_bots}\n"
                    f"images-only: {starboard.images_only}\n"
                ),
                inline=True,
            )

            embed.add_field(
                name="Behaviour",
                value=(
                    f"autoreact: {starboard.autoreact}\n"
                    f"remove-invalid: {starboard.remove_invalid}\n"
                    f"link-deletes: {starboard.link_deletes}\n"
                    f"link-edits: {starboard.link_edits}\n"
                    f"disable-xp: {starboard.disable_xp}\n"
                    f"allow-explore: {starboard.allow_explore}\n"
                ),
                inline=True,
            )

            await ctx.respond(embed=embed)


@plugin.include
@starboards.child
@crescent.command(name="add", description="Add a starboard")
class AddStarboard:
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
            raise StarboardNotFound(self.starboard.id)

        await msg.edit(f"Deleted <#{self.starboard.id}>.", components=[])


_T = TypeVar("_T")


def optiond(type: Type[_T], *args, **kwargs) -> _T | UNDEF:
    return crescent.option(
        type, *args, **kwargs, default=UNDEF.UNDEF  # type: ignore
    )


@plugin.include
@starboards.child
@crescent.command(name="edit", description="Modify a starboard")
class EditStarboard:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to edit"
    )

    color = optiond(str, "The color of the starboard embeds")
    display_emoji = optiond(
        str, "The emoji next to the point count", name="display-emoji"
    )
    ping_author = optiond(
        bool,
        "Whether to ping users when their post is starboarded",
        name="ping-author",
    )
    use_nicknames = optiond(
        bool, "Whether to use nicknames", name="use-nicknames"
    )
    use_webhook = optiond(
        bool,
        "Whether to use webhooks for starboard messages",
        name="use-webhook",
    )
    webhook_name = optiond(
        str, "The name for webhooks, if enabled", name="webhook-name"
    )
    webhook_avatar = optiond(
        str, "The avatar for webhooks, if enabled", name="webhook-avatar"
    )
    required = optiond(
        int, "The number of reactions required for a message to be starboarded"
    )
    required_remove = optiond(
        int,
        "The fewest number of stars a message can have before it is removed",
        name="required-remove",
    )
    self_star = optiond(
        bool,
        "Whether to allow users to star their own messages",
        name="self-star",
    )
    allow_bots = optiond(
        bool,
        "Whether to allow messages from bots to be starboarded",
        name="allow-bots",
    )
    images_only = optiond(
        bool,
        "Whether to require messages to include an image",
        name="images-only",
    )
    autoreact = optiond(
        bool,
        "Whether to automatically react to messages sent to the starboard",
    )
    remove_invalid = optiond(
        bool, "Whether to remove invalid reactions", name="remove-invalid"
    )
    link_deletes = optiond(
        bool,
        "Whether to unstarboard messages if the original was deleted",
        name="link-deletes",
    )
    link_edits = optiond(
        bool,
        "Whether to update the starboard message if the original is edited",
        name="link-edits",
    )
    disable_xp = optiond(
        bool, "Whether to disable XP for a starboard", name="disable-xp"
    )
    allow_explore = optiond(
        bool,
        "Whether `random` and `moststarred` can pull from this starboard",
        name="allow-explore",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        params = self.__dict__.copy()
        del params["starboard"]

        # conversion
        convert("color", params, none_or(hex_color))
        convert("display_emoji", params, none_or(any_emoji_str))

        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        for k, v in params.items():
            if v is UNDEF.UNDEF:
                continue
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
