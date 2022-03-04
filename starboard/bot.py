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
import subprocess
import traceback
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from textwrap import indent
from typing import Any

import aiohttp
import crescent
import hikari
import miru
from hikari_clusters import (
    Brain,
    Cluster,
    ClusterLauncher,
    Server,
    commands,
    events,
    payload,
)

from .cache import Cache
from .config import CONFIG, Config
from .cooldown import Cooldown
from .database import Database
from .tasks import expired_premium, patreon, post_stats


class Bot(crescent.Bot):
    cluster: Cluster

    def __init__(self) -> None:
        intents = (
            hikari.Intents.GUILD_MESSAGE_REACTIONS
            | hikari.Intents.GUILD_MESSAGES
            | hikari.Intents.GUILD_MEMBERS
            | hikari.Intents.GUILDS
        )
        self._real_cache = Cache(self)
        super().__init__(
            token=CONFIG.discord_token,
            tracked_guilds=[CONFIG.main_guild] if CONFIG.main_guild else None,
            default_guild=CONFIG.main_guild if CONFIG.development else None,
            intents=intents,
        )

        self.bot_stats: dict[int, int] = {}

        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._tasks: list[asyncio.Task] = []
        self.database = Database()

        miru.load(self)

        # locks and cooldowns
        self.star_cooldown: Cooldown[tuple[int, int]] = Cooldown(
            CONFIG.max_cooldown_period
        )
        self.edit_cooldown: Cooldown[int] = Cooldown(
            CONFIG.edit_cooldown_period
        )
        self.asc_cooldown: Cooldown[int] = Cooldown(CONFIG.asc_cooldown_period)
        self.xpr_cooldown: Cooldown[int] = Cooldown(CONFIG.xpr_cooldown_period)
        self.pr_cooldown: Cooldown[int] = Cooldown(CONFIG.pr_cooldown_period)
        self.guild_star_cooldown: Cooldown[int] = Cooldown(
            CONFIG.guild_star_cooldown_period
        )

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
        assert (u := self.get_me())
        return u

    async def session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            self._aiohttp_session = aiohttp.ClientSession()
        return self._aiohttp_session

    async def start(self, **kwargs) -> None:
        self.cluster.ipc.commands.include(BOT_CMD)
        self.cluster.ipc.commands.cmd_kwargs["bot"] = self
        self.cluster.ipc.events.include(BOT_EVENT)
        self.cluster.ipc.events.event_kwargs["bot"] = self

        await self.database.connect(
            migrate=self.cluster.cluster_id == 0,
            host=CONFIG.db_host,
            database=CONFIG.db_name,
            user=CONFIG.db_user,
            password=CONFIG.db_password,
        )

        # tasks
        self._tasks.append(
            asyncio.create_task(expired_premium.check_expired_premium(self))
        )
        self._tasks.append(
            asyncio.create_task(patreon.loop_update_patrons(self))
        )
        self._tasks.append(
            asyncio.create_task(post_stats.loop_post_stats(self))
        )
        self._tasks.append(
            asyncio.create_task(post_stats.loop_broadcast_stats(self))
        )

        await super().start(
            **kwargs, activity=hikari.Activity(name="Mention me for help")
        )

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
    server = Server(
        host=config.host,
        port=config.port,
        token=config.ipc_token,
        cluster_launcher=_get_cluster_launcher(),
        certificate_path=config.certificate_path,
    )
    server.ipc.commands.include(SERVER_CMD)
    return server


BOT_CMD = commands.CommandGroup()


@BOT_CMD.add("eval")
async def eval_cmd(pl: payload.COMMAND, bot: Bot) -> payload.DATA:
    assert pl.data.data
    out, ret = await bot.exec_code(pl.data.data["code"], {"_bot": bot})
    return {"result": f"Return:\n{ret}\n\nOutput:\n{out}"}


BOT_EVENT = events.EventGroup()


@BOT_EVENT.add("cluster_stats")
async def set_cluster_stats(pl: payload.EVENT, bot: Bot) -> None:
    assert pl.data.data
    bot.bot_stats[pl.author] = pl.data.data["guild_count"]


SERVER_CMD = commands.CommandGroup()


@SERVER_CMD.add("run_shell")
async def run_shell(pl: payload.COMMAND) -> payload.DATA:
    assert pl.data.data
    command = pl.data.data["command"]
    p = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    return {"result": (out or err).decode()}
