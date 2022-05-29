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

import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING, cast

import hikari
from pycooldown import FixedCooldown

from starboard.config import CONFIG
from starboard.core.notifications import notify
from starboard.database import AutoStarChannel

from .emojis import stored_to_emoji
from .has_image import has_image

if TYPE_CHECKING:
    from starboard.bot import Bot


COOLDOWN: FixedCooldown[int] = FixedCooldown(
    CONFIG.asc_cooldown_period, CONFIG.asc_cooldown_cap
)


async def handle_message(event: hikari.MessageCreateEvent) -> None:
    bot = cast("Bot", event.app)

    if (
        event.message.author.is_bot
        or event.channel_id not in bot.database.asc
        or COOLDOWN.update_rate_limit(event.channel_id)
    ):
        return

    asc = await AutoStarChannel.exists(id=event.channel_id)
    if not asc:
        bot.database.asc.discard(event.channel_id)
        return

    if asc.prem_locked:
        return

    # validation
    valid: bool = True
    content = event.message.content or ""
    ln = len(content)
    if ln < asc.min_chars:
        valid = False
    elif asc.max_chars is not None and ln > asc.max_chars:
        valid = False
    elif asc.require_image and not has_image(event.message):
        await asyncio.sleep(0.5)
        m = await bot.cache.gof_message(event.channel_id, event.message_id)
        if m is None:
            return
        valid = has_image(m)

    if not valid:
        if asc.delete_invalid:
            with suppress(hikari.ForbiddenError):
                await event.message.delete()

            await notify(
                event.message.author,
                f"Your message in <#{event.channel_id}> was deleted because "
                "it didn't meet the requirements for that autostar channel. "
                "Here is the content of your message:",
            )
            await notify(
                event.message.author,
                event.message.content
                or "Your message doesn't seem to have any text content.",
            )

        return

    # react
    _emojis = {stored_to_emoji(e, bot) for e in asc.emojis}
    _emojis.discard(None)
    emojis = cast("set[hikari.CustomEmoji | hikari.UnicodeEmoji]", _emojis)

    for e in emojis:
        with suppress(
            hikari.ForbiddenError, hikari.NotFoundError, hikari.BadRequestError
        ):
            await event.message.add_reaction(e)
