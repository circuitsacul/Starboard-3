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
from cachetools import TTLCache
from hikari.impl.cache import CacheImpl

from starboard.undefined import UNDEF

if TYPE_CHECKING:
    from starboard.bot import Bot


class Cache(CacheImpl):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.__messages = TTLCache[int, "hikari.Message | None"](5000, 30)

        if TYPE_CHECKING:
            self._app = cast(Bot, self._app)

    async def gof_message(
        self,
        channel: hikari.SnowflakeishOr[hikari.TextableChannel],
        message: hikari.SnowflakeishOr[hikari.PartialMessage],
    ) -> hikari.Message | None:
        msg: UNDEF | None | hikari.Message
        if (msg := self.get_message(message)) is not None:
            return msg

        msg = self.__messages.get(int(message), UNDEF.UNDEF)
        if msg is not UNDEF.UNDEF:
            return msg

        try:
            msg = await self._app.rest.fetch_message(channel, message)
        except hikari.NotFoundError:
            msg = None

        self.__messages[int(message)] = msg
        return msg
