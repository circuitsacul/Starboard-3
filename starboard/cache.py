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
from cachetools import LFUCache
from hikari.impl.cache import CacheImpl

from starboard.database import Starboard
from starboard.undefined import UNDEF

if TYPE_CHECKING:
    from starboard.bot import Bot


class Cache(CacheImpl):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # discord side
        self.__messages: LFUCache[int, hikari.Message | None] = LFUCache(1000)
        self.__members: LFUCache[
            tuple[int, int], hikari.Member | None
        ] = LFUCache(1000)
        self.__webhooks: LFUCache[int, hikari.ExecutableWebhook] = LFUCache(
            1000
        )

        # db side
        self.__star_emojis: LFUCache[int, set[str]] = LFUCache(1000)

        if TYPE_CHECKING:
            self._app = cast(Bot, self._app)

    def clear(self) -> None:
        self.__messages.clear()
        self.__members.clear()
        self.__webhooks.clear()
        self.__star_emojis.clear()
        super().clear()

    def invalidate_star_emojis(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild]
    ) -> None:
        print("invalid")
        self.__star_emojis.pop(int(guild), None)

    async def guild_star_emojis(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild]
    ) -> set[str]:
        gid = int(guild)
        ge: set[str]
        _ge = self.__star_emojis.get(gid, None)
        if _ge is None:
            print("fetching")
            sbs = await Starboard.fetch_query().where(guild_id=gid).fetchmany()
            ge = set()
            for s in sbs:
                ge = ge.union(s.star_emojis)

            self.__star_emojis[gid] = ge
            return ge
        print("getting")
        return _ge

    async def gof_webhook(
        self, webhook_id: hikari.SnowflakeishOr[hikari.PartialWebhook]
    ) -> hikari.ExecutableWebhook | None:
        if (c := self.__webhooks.get(int(webhook_id), None)) is not None:
            return c

        try:
            obj = await self._app.rest.fetch_webhook(webhook_id)
        except hikari.NotFoundError:
            return None

        assert isinstance(obj, hikari.ExecutableWebhook)

        self.__webhooks[int(webhook_id)] = obj
        return obj

    async def gof_member(
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        user: hikari.SnowflakeishOr[hikari.PartialUser],
    ) -> hikari.Member | None:
        if (ic := self.get_member(guild, user)) is not None:
            return ic

        c = self.__members.get((int(guild), int(user)), UNDEF.UNDEF)
        if c is not UNDEF.UNDEF:
            return c

        try:
            obj = await self._app.rest.fetch_member(guild, user)
        except hikari.NotFoundError:
            obj = None

        self.__members[(int(guild), int(user))] = obj
        return obj

    async def gof_message(
        self,
        channel: hikari.SnowflakeishOr[hikari.TextableChannel],
        message: hikari.SnowflakeishOr[hikari.PartialMessage],
    ) -> hikari.Message | None:
        if (ic := self.get_message(message)) is not None:
            return ic

        c = self.__messages.get(int(message), UNDEF.UNDEF)
        if c is not UNDEF.UNDEF:
            return c

        try:
            obj = await self._app.rest.fetch_message(channel, message)
        except hikari.NotFoundError:
            obj = None

        self.__messages[int(message)] = obj
        return obj

    async def gof_guild_channel_wnsfw(
        self, channel: hikari.SnowflakeishOr[hikari.PartialChannel]
    ) -> hikari.GuildChannel | None:
        cached = self.get_guild_channel(channel)
        if cached is None:
            return None

        if cached.is_nsfw is None:
            _ret = await self._app.rest.fetch_channel(channel)
            assert isinstance(_ret, hikari.GuildChannel)
            cached = _ret

        assert cached.is_nsfw is not None
        self.update_guild_channel(cached)
        return cached

    def delete_message(
        self, message: hikari.SnowflakeishOr[hikari.PartialMessage], /
    ) -> hikari.Message | None:
        id = int(message)
        if id in self.__messages:
            self.__messages[id] = None
        return super().delete_message(id)

    def delete_member(
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        user: hikari.SnowflakeishOr[hikari.PartialUser],
        /,
    ) -> hikari.Member | None:
        key = (int(guild), int(user))
        if key in self.__members:
            self.__members[key] = None
        return super().delete_member(*key)
