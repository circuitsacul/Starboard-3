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
from ._converters import any_emoji_str

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
                description="\n".join(f"<#{s.id}>" for s in all_starboards),
            )
            await ctx.respond(embed=embed)

        else:
            s = await Starboard.exists(id=self.starboard.id)
            if not s:
                raise StarboardNotFound(self.starboard.id)

            await ctx.respond(repr(s))


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

        await ctx.respond(f"<#{self.channel.id}> is not a starboard.")


@plugin.include
@starboards.child
@crescent.command(name="delete", description="Remove a starboard")
class DeleteStarboard:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "Starboard to delete."
    )

    async def callback(self, ctx: crescent.Context) -> None:
        confirm = Confirm(ctx.user.id)
        await ctx.respond(
            "Are you sure? All data will be lost **permanently**.",
            components=confirm.build(),
        )
        msg = await ctx.app.rest.fetch_interaction_response(
            ctx.application_id, ctx.token
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
    display_emoji = optiond(str, "The emoji next to the point count")
    ping_author = optiond(
        bool, "Whether to ping users when their post is starboarded"
    )
    use_nicknames = optiond(bool, "Whether to use nicknames")
    use_webhook = optiond(
        bool, "Whether to use webhooks for starboard messages"
    )
    webhook_name = optiond(str, "The name for webhooks, if enabled")
    webhook_avatar = optiond(str, "The avatar for webhooks, if enabled")
    required = optiond(
        int, "The number of reactions required for a message to be starboarded"
    )
    required_remove = optiond(
        int,
        "The fewest number of stars a message can have before it is removed",
    )
    self_star = optiond(
        bool, "Whether to allow users to star their own messages"
    )
    allow_bots = optiond(
        bool, "Whether to allow messages from bots to be starboarded"
    )
    images_only = optiond(
        bool, "Whether to require messages to include an image"
    )
    autoreact = optiond(
        bool,
        "Whether to automatically react to messages sent to the starboard",
    )
    remove_invalid = optiond(bool, "Whether to remove invalid reactions")
    link_deletes = optiond(
        bool, "Whether to unstarboard messages if the original was deleted"
    )
    link_edits = optiond(
        bool,
        "Whether to update the starboard message if the original is edited",
    )
    disable_xp = optiond(bool, "Whether to disable XP for a starboard")
    allow_explore = optiond(
        bool, "Whether `random` and `moststarred` can pull from this starboard"
    )

    async def callback(self, ctx: crescent.Context) -> None:
        params = ctx.options.copy()
        del params["starboard"]

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
