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
import os
import traceback
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from textwrap import indent
from typing import Any

import aiohttp
import crescent
import hikari
import miru

from .cache import Cache
from .config import CONFIG
from .cooldowns import cooldown
from .database import Database

if os.name != "nt":
    import uvloop  # type: ignore

    uvloop.install()  # type: ignore


class Bot(crescent.Bot):
    def __init__(self) -> None:
        intents = (
            hikari.Intents.GUILD_MESSAGE_REACTIONS
            | hikari.Intents.GUILD_MESSAGES
            | hikari.Intents.GUILD_MEMBERS
            | hikari.Intents.GUILDS
            | hikari.Intents.MESSAGE_CONTENT
            | hikari.Intents.GUILD_EMOJIS
        )
        self._real_cache = Cache(self)
        super().__init__(
            token=CONFIG.discord_token,
            tracked_guilds=[CONFIG.main_guild] if CONFIG.main_guild else None,
            intents=intents,
            update_commands=False,
            command_hooks=[cooldown(*CONFIG.global_cooldown)],
            auto_chunk_members=False,
        )

        self.bot_stats: dict[int, int] = {}

        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._tasks: list[asyncio.Task] = []
        self.database = Database()

        miru.load(self)
        self.plugins.load_folder("starboard.commands")
        self.plugins.load_folder("starboard.events")

    @property
    def cache(self) -> Cache:
        return self._real_cache

    @property  # type: ignore
    def _cache(self) -> Cache:  # type: ignore
        return self._real_cache

    @_cache.setter
    def _cache(self, ot: Any) -> None:
        pass

    @property
    def me(self) -> hikari.OwnUser:
        u = self.get_me()
        assert u
        return u

    async def session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            self._aiohttp_session = aiohttp.ClientSession()
        return self._aiohttp_session

    async def start(self, **kwargs) -> None:
        await self.database.connect(
            migrate=True,
            host=CONFIG.db_host,
            database=CONFIG.db_name,
            user=CONFIG.db_user,
            password=CONFIG.db_password,
        )

        await super().start(**kwargs)

        await self._command_handler.register_commands()

    async def close(self) -> None:
        await super().close()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.database.cleanup()
        print("Cleaned up!")

    def embed(
        self,
        title=None,
        description=None,
        url: str | None = None,
        timestamp: datetime | None = None,
    ) -> hikari.Embed:
        return hikari.Embed(
            title=title,
            description=description,
            url=url,
            color=CONFIG.color,
            timestamp=timestamp,
        )

    async def exec_code(
        self, code: str, glbls: dict[str, Any] | None = None
    ) -> tuple[str, Any]:
        code = indent(code, "    ")
        code = (
            f"async def _async_internal_exec_func_wrap():\n{code}\n\nresult="
            "_async_internal_exec_func_wrap()"
        )

        lcls: dict[str, Any] = {}
        f = StringIO()
        with redirect_stdout(f):
            try:
                exec(code, glbls, lcls)
                result = await lcls["result"]
            except Exception:
                return "```py\n" + traceback.format_exc() + "\n```", None

        return f.getvalue(), result
