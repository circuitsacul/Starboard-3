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

from pathlib import Path

import aiohttp
import tanjun
from hikari_clusters import Brain, Cluster, ClusterLauncher, Server

from .cache import CacheControl
from .config import Config
from .database import Database


class Bot(Cluster):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._aiohttp_session: aiohttp.ClientSession | None = None
        self.database = Database()
        self.config = Config.load()
        self.tjbot = tanjun.Client.from_gateway_bot(
            self,
            declare_global_commands=self.config.testing_guilds,
        )
        self.ccache = CacheControl(self)

        def load_modules(parent: Path):
            for module in parent.glob("*.py"):
                if module.name.startswith("_"):
                    continue
                name = "{}.{}".format(
                    str(parent).replace("/", "."), module.name.strip(".py")
                )
                self.tjbot.load_modules(name)

        load_modules(Path("starboard/commands"))
        load_modules(Path("starboard/events"))

    async def session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            self._aiohttp_session = aiohttp.ClientSession()
        return self._aiohttp_session

    async def start(self, **kwargs) -> None:
        await self.database.connect(
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )
        await super().start(**kwargs)

    async def close(self) -> None:
        await super().close()
        await self.database.cleanup()
        self.logger.info("Cleaned up!")


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


def _get_cluster_launcher(config: Config) -> ClusterLauncher:
    return ClusterLauncher(
        bot_class=Bot,
        bot_init_kwargs={"token": config.discord_token},
    )


def get_server(config: Config) -> Server:
    return Server(
        host=config.host,
        port=config.port,
        token=config.ipc_token,
        cluster_launcher=_get_cluster_launcher(config),
        certificate_path=config.certificate_path,
    )
