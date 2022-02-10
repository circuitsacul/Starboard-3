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

from typing import cast, TYPE_CHECKING
from apgorm import raw as r

import crescent
import hikari

from starboard.database import SBMessage, Starboard, Message
from starboard.exceptions import StarboardErr, StarboardNotFound
from starboard.core.embed_message import embed_message
from starboard.core.emojis import stored_to_emoji
from starboard.core.config import get_config

from ._checks import guild_only

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("fun")


@plugin.include
@crescent.hook(guild_only)
@crescent.command(
    name="random", description="A random message from the starboards"
)
class Random:
    starboard = crescent.option(
        hikari.TextableGuildChannel, "The starboard to pull from"
    )
    channel = crescent.option(
        hikari.TextableGuildChannel,
        "Only show messages sent in this channel",
        default=None,
    )
    min_stars = crescent.option(
        int,
        "Only show messages with at least this many stars",
        default=None,
        min_value=1,
    )
    max_stars = crescent.option(
        int,
        "Only show messages with at most this many stars",
        default=None,
        min_value=1,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        s = await Starboard.exists(id=self.starboard.id)
        if not s:
            raise StarboardNotFound(self.starboard.id)

        q = SBMessage.fetch_query()
        q.where(starboard_id=self.starboard.id)
        q.where(SBMessage.sb_message_id.is_null.not_)

        sbq = Message.fetch_query()
        sbq.where(id=SBMessage.message_id)
        sbq.where(trashed=False)
        if self.channel:
            sbq.where(channel_id=self.channel.id)

        q.where(sbq.exists())

        if self.min_stars:
            q.where(SBMessage.last_known_star_count.gt(self.min_stars))
        if self.max_stars:
            q.where(SBMessage.last_known_star_count.lt(self.max_stars))

        q.order_by(r("random()"))

        ret = await q.fetchone()

        if not ret:
            raise StarboardErr("Nothing to show.")

        orig = await Message.fetch(id=ret.message_id)
        obj = await bot.cache.gof_message(orig.channel_id, orig.id)
        if not obj:
            raise StarboardErr("Something went wrong.")

        config = await get_config(s, obj.channel_id)

        raw, e, es = await embed_message(
            bot,
            obj,
            ctx.guild_id,
            config.color,
            stored_to_emoji(config.display_emoji, bot)
            if config.display_emoji
            else None,
            config.use_server_profile,
            config.ping_author,
            ret.last_known_star_count,
            orig.frozen,
            s.id in orig.forced_to,
        )

        await ctx.respond(content=raw, embeds=[e, *es])
