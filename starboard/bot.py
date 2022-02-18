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
import traceback
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING, Any

import aiohttp
import crescent
import hikari
import miru
from hikari_clusters import Brain, Cluster, ClusterLauncher, Server

from .cache import Cache
from .config import CONFIG, Config
from .cooldown import Cooldown
from .database import Database
from .tasks import expired_premium, patreon


class Bot(crescent.Bot):
    cluster: Cluster

    def __init__(self) -> None:
        super().__init__(
            token=CONFIG.discord_token,
            tracked_guilds=[CONFIG.dev_guild] if CONFIG.dev_guild else None,
            default_guild=CONFIG.dev_guild if CONFIG.development else None,
        )

        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._tasks: list[asyncio.Task] = []
        self.database = Database()
        self._cache = Cache(self, self._cache._settings)
        self._event_manager._cache = self._cache

        miru.load(self)

        # locks and cooldowns
        self.refresh_message_lock: set[int] = set()
        self.star_cooldown: Cooldown[tuple[int, int]] = Cooldown()
        self.asc_cooldown: Cooldown[int] = Cooldown()

        def load_modules(parent: Path):
            for module in parent.glob("*.py"):
                if module.name.startswith("_"):
                    continue
                name = "{}.{}".format(
                    str(parent).replace("/", "."), module.name[:-3]
                )
                self.plugins.load(name)

        load_modules(Path("starboard/commands"))
        load_modules(Path("starboard/events"))

    if TYPE_CHECKING:

        @property
        def cache(self) -> Cache:
            ...

    @property
    def me(self) -> hikari.OwnUser:
        assert (u := self.get_me())
        return u

    async def session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            self._aiohttp_session = aiohttp.ClientSession()
        return self._aiohttp_session

    async def start(self, **kwargs) -> None:
        # tasks
        await self.database.connect(
            migrate=self.cluster.cluster_id == 0,
            host=CONFIG.db_host,
            database=CONFIG.db_name,
            user=CONFIG.db_user,
            password=CONFIG.db_password,
        )
        if self.cluster.cluster_id == 0:
            self._tasks.append(
                asyncio.create_task(
                    expired_premium.check_expired_premium(self)
                )
            )
            self._tasks.append(
                asyncio.create_task(patreon.loop_update_patrons(self))
            )
        self._tasks.append(
            asyncio.create_task(self.star_cooldown.loop_cycle())
        )

        await super().start(**kwargs)

    async def close(self) -> None:
        await super().close()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.database.cleanup()
        self.cluster.logger.info("Cleaned up!")

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


def get_brain(config: Config) -> Brain:
    return Brain(
        token=config.ipc_token,
        host=config.host,
        port=config.port,
        total_servers=config.total_servers,
        clusters_per_server=config.clusters_per_server,
        shards_per_cluster=config.shards_per_cluster,
        certificate_path=config.certificate_path,
    )


def _get_cluster_launcher() -> ClusterLauncher:
    return ClusterLauncher(bot_class=Bot)


def get_server(config: Config) -> Server:
    return Server(
        host=config.host,
        port=config.port,
        token=config.ipc_token,
        cluster_launcher=_get_cluster_launcher(),
        certificate_path=config.certificate_path,
    )
