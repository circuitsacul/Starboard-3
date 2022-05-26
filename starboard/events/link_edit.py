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

from starboard.core.messages import get_orig_message
from starboard.core.starboards import refresh_message

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("link-edit-events")


@plugin.include
@crescent.event
async def on_message_edit(event: hikari.GuildMessageUpdateEvent) -> None:
    bot = cast("Bot", event.app)
    message = await get_orig_message(event.message_id)
    if not message:
        return
    await refresh_message(bot, message, force=True)


@plugin.include
@crescent.event
async def on_message_delete(event: hikari.GuildMessageDeleteEvent) -> None:
    bot = cast("Bot", event.app)
    message = await get_orig_message(event.message_id)
    if not message:
        return
    await refresh_message(bot, message, force=True)
