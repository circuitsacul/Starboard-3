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

from typing import TYPE_CHECKING

import emoji
import hikari

if TYPE_CHECKING:
    from starboard.bot import Bot


def stored_to_emoji(
    e: str, bot: Bot
) -> hikari.CustomEmoji | hikari.UnicodeEmoji | None:
    try:
        if custom := bot.cache.get_emoji(int(e)):
            return custom
    except ValueError:
        pass

    if emoji.is_emoji(em := hikari.UnicodeEmoji.parse(e)):  # type: ignore
        return em

    return None


def emoji_to_stored(e: hikari.CustomEmoji | hikari.UnicodeEmoji) -> str:
    if isinstance(e, hikari.CustomEmoji):
        return str(e.id)
    return str(e)
