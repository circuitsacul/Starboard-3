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

import hikari
import tanjun

from starboard.database import Starboard

if TYPE_CHECKING:
    from starboard.bot import Bot


C = tanjun.Component()


starboards = tanjun.slash_command_group("starboards", "Manage Starboards")
starboards = tanjun.with_guild_check(starboards)
starboards = tanjun.with_author_permission_check(
    hikari.Permissions.MANAGE_GUILD
)(starboards)
starboards = C.with_command(starboards)


@starboards.with_command
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to view info for. Leave blank to view all.",
    default=None,
)
@tanjun.as_slash_command(
    "view", "View starboards or settings for a starboard."
)
async def view_starboard_settings(
    ctx: tanjun.abc.SlashContext, starboard: hikari.InteractionChannel | None
):
    bot = cast("Bot", ctx.interaction.app)
    if starboard is None:
        all_starboards = await Starboard.fetch_query().fetchmany()
        if len(all_starboards) == 0:
            return await ctx.respond("There are no starboards in this guild.")
        embed = bot.embed(
            title="Starboards",
            description="\n".join([f"<#{s.id.v}>" for s in all_starboards]),
        )
        await ctx.respond(embed=embed)
    else:
        s = await Starboard.exists(id=starboard.id)
        if not s:
            return await ctx.respond(f"<#{starboard.id}> is not a starboard.")
        await ctx.respond(repr(s))


@starboards.with_command
@tanjun.with_channel_slash_option(
    "channel", "The channel to make a starboard."
)
@tanjun.as_slash_command("add", "Add a Starboard.")
async def add_starboard(
    ctx: tanjun.abc.SlashContext, channel: hikari.InteractionChannel
):
    exists = await Starboard.exists(id=channel.id)
    if exists:
        return await ctx.respond(f"<#{channel.id}> is already a starboard.")

    await Starboard(
        id=channel.id,
        guild_id=ctx.guild_id,
    ).create()

    await ctx.respond(f"<#{channel.id}> is now a starboard.")


@starboards.with_command
@tanjun.with_channel_slash_option("starboard", "The starboard to remove.")
@tanjun.as_slash_command("remove", "Remove a starboard.")
async def remove_starboard(
    ctx: tanjun.abc.SlashContext, starboard: hikari.InteractionChannel
):
    res = await Starboard.delete_query().where(id=starboard.id).execute()
    if len(res) == 0:
        return await ctx.respond(f"<#{starboard.id}> is not a starboard.")
    await ctx.respond(f"Deleted starboard <#{starboard.id}>.")


load = C.make_loader()
