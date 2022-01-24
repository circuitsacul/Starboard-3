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
from starboard.database.get_or_create import goc_guild
from starboard.undefined import UNDEF
from starboard.views import Confirm

from ._converters import any_emoji_str, hex_color, none_or, none_or_str

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
    types=(hikari.TextableGuildChannel,),
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
    "channel",
    "The channel to make a starboard.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command("add", "Add a Starboard.")
async def add_starboard(
    ctx: tanjun.abc.SlashContext, channel: hikari.InteractionChannel
):
    assert ctx.guild_id
    await goc_guild(ctx.guild_id)
    exists = await Starboard.exists(id=channel.id)
    if exists:
        return await ctx.respond(f"<#{channel.id}> is already a starboard.")

    await Starboard(
        id=channel.id,
        guild_id=ctx.guild_id,
    ).create()

    await ctx.respond(f"<#{channel.id}> is now a starboard.")


@starboards.with_command
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to remove.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command("remove", "Remove a starboard.")
async def remove_starboard(
    ctx: tanjun.abc.SlashContext, starboard: hikari.InteractionChannel
):
    confirm = Confirm(cast("Bot", ctx.interaction.app))
    msg = await ctx.respond(
        "Are you sure?", components=confirm.build(), ensure_result=True
    )
    confirm.start(msg)
    await confirm.wait()

    if confirm.result is True:
        res = await Starboard.delete_query().where(id=starboard.id).execute()
        if len(res) == 0:
            await msg.edit(
                f"<#{starboard.id}> is not a starboard.", components=[]
            )
        else:
            await msg.edit(
                f"Deleted starboard <#{starboard.id}>.", components=[]
            )
    else:
        await msg.edit("Cancelled.", components=[])


if TYPE_CHECKING:
    str_option = tanjun.with_str_slash_option
    bool_option = tanjun.with_bool_slash_option
    int_option = tanjun.with_int_slash_option

else:

    def str_option(*args, **kwargs):
        kwargs.setdefault("default", UNDEF.UNDEF)
        return tanjun.with_str_slash_option(*args, **kwargs)

    def bool_option(*args, **kwargs):
        kwargs.setdefault("default", UNDEF.UNDEF)
        return tanjun.with_bool_slash_option(*args, **kwargs)

    def int_option(*args, **kwargs):
        kwargs.setdefault("default", UNDEF.UNDEF)
        return tanjun.with_int_slash_option(*args, **kwargs)


@starboards.with_command
@str_option(
    "color",
    "The color of the embeds.",
    converters=none_or(hex_color),
)
@str_option(
    "display_emoji",
    "The emoji shown next to the point count.",
    converters=none_or(any_emoji_str),
)
@bool_option(
    "ping_author",
    "Whether to ping the author when their post is starboarded.",
)
@bool_option(
    "use_nicknames",
    "Whether to use nicknames instead of usernames on embeds.",
)
@bool_option(
    "use_webhook",
    "Whether to use webhooks to send messages to this starboard.",
    default=UNDEF.UNDEF,
)
@str_option(
    "webhook_name",
    "The name to use for webhook messages.",
    default=UNDEF.UNDEF,
)
@str_option(
    "webhook_avatar",
    "The url to the avatar to use. Use 'none' to use default.",
    converters=none_or_str,
)
@int_option(
    "required",
    "The number of stars a message needs before it is sent to the starboard.",
)
@int_option(
    "required_remove",
    "The fewest number of stars a message can have before it is removed.",
)
@bool_option(
    "self_star",
    "Whether or not users can star their own messages.",
)
@bool_option(
    "allow_bots", "Whether or not messages by bots can be starboarded."
)
@bool_option(
    "images_only",
    "If enabled, only messages that include images can be starboarded.",
)
@str_option(
    "regex",
    "Specify regex that all messages must match. Use the `reset_regex` "
    "command to disable.",
)
@str_option(
    "exclude_regex",
    "Specify regex that all messages must *not* match. Use the "
    "`reset_exclude_regex` command to disable.",
)
@bool_option(
    "autoreact",
    "Whether to automatically react to messages once sent to the starboard.",
)
@bool_option(
    "remove_invalid", "Whether to remove invalid reactions (e.g. self stars)."
)
@bool_option(
    "link_deletes",
    "If enabled, if a message is deleted then that message will also be "
    "removed from this starboard.",
)
@bool_option(
    "link_edits",
    "If disabled, then once a message is sent to the starboard its content "
    "will not change.",
)
@bool_option(
    "disable_xp",
    "If true, then reactions for this starboard will not count towards the "
    "authors XP.",
)
@bool_option(
    "allow_explore",
    "If true, then commands such as `random` and `moststarred` can pull "
    "messages from this starboard.",
)
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to modify.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command("edit", "Modify a starboard.")
async def edit_starboard(
    ctx: tanjun.abc.SlashContext,
    starboard: hikari.InteractionChannel,
    **kwargs,
):
    s = await Starboard.exists(id=starboard.id)
    if not s:
        return await ctx.respond(f"<#{starboard.id}> is not a starboard.")

    for k, v in kwargs.items():
        if v is UNDEF.UNDEF:
            continue
        s.all_fields[k].v = v

    await s.save()
    await ctx.respond(f"Settings for <#{starboard.id}> updated.")


emojis = tanjun.slash_command_group("emojis", "Modify emojis for a starboard.")
starboards.add_command(emojis)


@emojis.with_command
@tanjun.with_str_slash_option(
    "emoji",
    "The emoji to add.",
    converters=any_emoji_str,
)
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to add a star emoji too.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command("add", "Add a star emoji.")
async def add_star_emoji(
    ctx: tanjun.abc.SlashContext,
    starboard: hikari.InteractionChannel,
    emoji: str,
):
    s = await Starboard.exists(id=starboard.id)
    if not s:
        return await ctx.respond(f"<#{starboard.id}> is not a starboard.")

    emojis = s.star_emojis.v.copy()
    if emoji in emojis:
        return await ctx.respond(
            f"{emoji} is already a star emoji for <#{starboard.id}>."
        )
    emojis.append(emoji)
    s.star_emojis.v = emojis
    await s.save()
    await ctx.respond("Done.")


@emojis.with_command
@tanjun.with_str_slash_option(
    "emoji",
    "The emoji to remove.",
    converters=any_emoji_str,
)
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to remove the star emoji from.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command("remove", "Remove a star emoji.")
async def remove_star_emoji(
    ctx: tanjun.abc.SlashContext,
    starboard: hikari.InteractionChannel,
    emoji: str,
):
    s = await Starboard.exists(id=starboard.id)
    if not s:
        return await ctx.respond(f"<#{starboard.id}> is not a starboard.")

    emojis = s.star_emojis.v.copy()
    if emoji not in emojis:
        return await ctx.respond(
            f"{emoji} is not a star emoji for <#{starboard.id}>."
        )
    emojis.remove(emoji)
    s.star_emojis.v = emojis
    await s.save()
    await ctx.respond("Done.")


@starboards.with_command
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to reset `regex` on.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command("reset_regex", "Reset `regex` for a starboard.")
async def reset_regex(
    ctx: tanjun.abc.SlashContext,
    starboard: hikari.InteractionChannel,
):
    s = await Starboard.exists(id=starboard.id)
    if not s:
        return await ctx.respond(f"<#{starboard.id}> is not a starboard.")

    s.regex.v = None
    await s.save()
    await ctx.respond("Done.")


@starboards.with_command
@tanjun.with_channel_slash_option(
    "starboard",
    "The starboard to reset `exclude_regex` on.",
    types=(hikari.TextableGuildChannel,),
)
@tanjun.as_slash_command(
    "reset_exclude_regex", "Reset `exclude_regex` for a starboard."
)
async def reset_exclude_regex(
    ctx: tanjun.abc.SlashContext,
    starboard: hikari.InteractionChannel,
):
    s = await Starboard.exists(id=starboard.id)
    if not s:
        return await ctx.respond(f"<#{starboard.id}> is not a starboard.")

    s.exclude_regex.v = None
    await s.save()
    await ctx.respond("Done.")


load = C.make_loader()
