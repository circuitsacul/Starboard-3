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
from hikari.api.config import CacheComponents
from hikari.impl.cache import CacheImpl
from hikari.impl.config import CacheSettings

from starboard.config import CONFIG
from starboard.database import Starboard
from starboard.database.models.override import Override
from starboard.undefined import UNDEF

if TYPE_CHECKING:
    from starboard.bot import Bot


class Cache(CacheImpl):
    def __init__(self, app: Bot) -> None:
        settings = CacheSettings(
            components=(
                CacheComponents.GUILDS
                | CacheComponents.GUILD_CHANNELS
                | CacheComponents.ROLES
                | CacheComponents.EMOJIS
                | CacheComponents.MESSAGES
                | CacheComponents.ME
                | CacheComponents.MEMBERS
                | CacheComponents.DM_CHANNEL_IDS
            ),
            max_messages=CONFIG.message_cache_size,
            max_dm_channel_ids=CONFIG.dm_channel_cache_size,
        )
        super().__init__(app, settings=settings)

        # discord side
        self.__null_messages: LFUCache[int, None] = LFUCache(
            CONFIG.message_null_cache_size
        )
        self.__members: LFUCache[
            tuple[int, int], hikari.Member | None
        ] = LFUCache(CONFIG.member_cache_size)
        self.__webhooks: LFUCache[int, hikari.ExecutableWebhook] = LFUCache(
            CONFIG.webhook_cache_size
        )

        # db side
        self.__vote_emojis: LFUCache[int, set[str]] = LFUCache(
            CONFIG.vote_emoji_cache_size
        )

        if TYPE_CHECKING:
            self._app = cast(Bot, self._app)

    def clear_safe(self) -> None:
        self.__null_messages.clear()
        self.__members.clear()
        self.__webhooks.clear()
        self.__vote_emojis.clear()
        self.clear_messages()
        self.clear_dm_channel_ids()

    def clear(self) -> None:
        self.clear_safe()
        super().clear()

    # vote emojis
    async def guild_vote_emojis(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild]
    ) -> set[str]:
        gid = int(guild)
        ge: set[str]
        _ge = self.__vote_emojis.get(gid, None)
        if _ge is None:
            sbs = await Starboard.fetch_query().where(guild_id=gid).fetchmany()
            ovs = await Override.fetch_query().where(guild_id=gid).fetchmany()
            ge = set()
            for s in sbs:
                ge = ge.union(s.upvote_emojis).union(s.downvote_emojis)
            for ov in ovs:
                ge = ge.union(ov.overrides.get("upvote_emojis", []))
                ge = ge.union(ov.overrides.get("downvote_emojis", []))

            self.__vote_emojis[gid] = ge
            return ge
        return _ge

    def invalidate_vote_emojis(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild]
    ) -> None:
        self.__vote_emojis.pop(int(guild), None)

    # webhooks
    async def gof_webhook(
        self, webhook_id: hikari.SnowflakeishOr[hikari.PartialWebhook]
    ) -> hikari.ExecutableWebhook | None:
        wh_id = int(webhook_id)
        if (c := self.__webhooks.get(wh_id)) is not None:
            return c

        try:
            obj = await self._app.rest.fetch_webhook(wh_id)
        except hikari.NotFoundError:
            return None

        assert isinstance(obj, hikari.ExecutableWebhook)

        self.__webhooks[wh_id] = obj
        return obj

    # members
    async def gof_member(
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        user: hikari.SnowflakeishOr[hikari.PartialUser],
    ) -> hikari.Member | None:
        key = (int(guild), int(user))
        c = self.__members.get(key, UNDEF.UNDEF)
        if c is not UNDEF.UNDEF:
            return c

        try:
            obj = await self._app.rest.fetch_member(*key)
        except hikari.NotFoundError:
            obj = None

        self._set_member_maybe_none(key, obj)
        return obj

    def get_member(
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        user: hikari.SnowflakeishOr[hikari.PartialUser],
        /,
    ) -> hikari.Member | None:
        return self.__members.get((int(guild), int(user)))

    def delete_member(
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        user: hikari.SnowflakeishOr[hikari.PartialUser],
        /,
    ) -> hikari.Member | None:
        key = (int(guild), int(user))
        orig = self.__members.get(key)
        if orig:
            self.__members[key] = None
        return orig

    def update_member(
        self, member: hikari.Member, /
    ) -> tuple[hikari.Member | None, hikari.Member]:
        cached = self.get_member(member.guild_id, member.user.id)
        self.set_member(member)
        return cached, member

    def set_member(self, member: hikari.Member, /) -> None:
        key = (int(member.guild_id), int(member.user.id))
        self._set_member_maybe_none(key, member)

    def _set_member_maybe_none(
        self, key: tuple[int, int], member: hikari.Member | None
    ) -> None:
        self.__members[key] = member
        if member:
            self._set_user(member.user)

    # messages
    async def gof_message(
        self,
        channel: hikari.SnowflakeishOr[hikari.TextableChannel],
        message: hikari.SnowflakeishOr[hikari.PartialMessage],
    ) -> hikari.Message | None:
        msg_id = int(message)

        if ic := self.get_message(msg_id):
            return ic

        if (
            c := self.__null_messages.get(msg_id, UNDEF.UNDEF)
        ) is not UNDEF.UNDEF:
            return c

        try:
            obj = await self._app.rest.fetch_message(channel, msg_id)
        except hikari.NotFoundError:
            self.__null_messages[msg_id] = None
            return None

        self.set_message(obj)
        return obj

    def delete_message(
        self, message: hikari.SnowflakeishOr[hikari.PartialMessage], /
    ) -> hikari.Message | None:
        msg_id = int(message)
        self.__null_messages[msg_id] = None
        return super().delete_message(msg_id)

    # channels
    async def gof_guild_channel_nsfw(
        self, channel: hikari.SnowflakeishOr[hikari.PartialChannel]
    ) -> bool | None:
        cached: (
            hikari.PermissibleGuildChannel | hikari.GuildThreadChannel | None
        ) = self.get_guild_channel(channel)
        if cached is None or cached.is_nsfw is None:
            try:
                _ret = await self._app.rest.fetch_channel(channel)
            except hikari.NotFoundError:
                return None
            assert isinstance(
                _ret,
                (hikari.PermissibleGuildChannel, hikari.GuildThreadChannel),
            )

            if _ret.type in {
                hikari.ChannelType.GUILD_NEWS_THREAD,
                hikari.ChannelType.GUILD_PUBLIC_THREAD,
                hikari.ChannelType.GUILD_PRIVATE_THREAD,
            }:
                assert _ret.parent_id is not None
                parent_nsfw = await self.gof_guild_channel_nsfw(_ret.parent_id)
                assert parent_nsfw is not None
                _ret.is_nsfw = parent_nsfw

            cached = _ret
            if isinstance(cached, hikari.PermissibleGuildChannel):
                self.update_guild_channel(cached)

        assert cached.is_nsfw is not None
        return cached.is_nsfw
