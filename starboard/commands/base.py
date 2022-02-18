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

from starboard.config import CONFIG

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("base-commands")


@plugin.include
@crescent.command(name="ping", description="Pong!")
async def ping_command(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    guild = bot.cache.get_guild(ctx.guild_id) if ctx.guild_id else None
    shard = guild.shard_id if guild else 0
    await ctx.respond(
        f"Pong! Cluster {bot.cluster.cluster_id}, shard {shard}, "
        f"{round(bot.heartbeat_latency*1000)} ms latency."
    )


@plugin.include
@crescent.command(name="help", description="Get help with starboard")
async def help_command(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    act = bot.rest.build_action_row()
    if CONFIG.docs_link:
        (
            act.add_button(hikari.ButtonStyle.LINK, CONFIG.docs_link)
            .set_label("Read the Docs")
            .add_to_container()
        )
    if CONFIG.support_invite:
        (
            act.add_button(hikari.ButtonStyle.LINK, CONFIG.support_invite)
            .set_label("Get Support")
            .add_to_container()
        )
    if CONFIG.bot_invite:
        (
            act.add_button(hikari.ButtonStyle.LINK, CONFIG.bot_invite)
            .set_label("Invite Starboard")
            .add_to_container()
        )

    emb = bot.embed(
        title="Starboard Help",
        description=(
            "Starboard is a Discord bot that lets you create starboard for "
            "your server. A starboard is similar to channel pins, except that "
            'people can "vote" to pin messages. A typical setup would be to '
            "create a starboard named #starboard such that when a message "
            "receives 3 :star: reactions, the message will be reposted to "
            "that channel."
        ),
    )
    emb.add_field(
        name="Useful Commands",
        value=(
            "`/starboards view`: View all your starboards\n"
            "`/starboards create`: Create a starboard\n"
            "`/starboards edit`: Change the settings for a starboard\n"
        ),
    )
    emb.add_field(
        name="Features",
        value=(
            "Starboard's key (free) features are:\n"
            " - Multiple starboards per server\n"
            " - Autostar channels\n"
            " - Award roles\n"
            " - Channel-specific settings for each starboard\n"
            " - Advanced role permission system"
        ),
    )
    emb.add_field(
        name="Privacy Policy",
        value=(
            "Starboard tracks the bare minimum information necessary to keep "
            "the bot running. The only data that is really included are "
            "object IDs (message IDs, channel IDs, user IDs, etc.) as well as "
            "bot-specific information (how much XP a user has, how many stars "
            "a message has, etc.). Starboard does not store usernames, guild "
            "names, or message content."
        ),
    )

    await ctx.respond(
        embed=emb, component=act if act.components else hikari.UNDEFINED
    )
