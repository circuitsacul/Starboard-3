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

import inspect
import json
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

_ALWAYS_SAVE = {"discord_token", "db_name", "ipc_token"}


@dataclass
class Config:
    # misc
    development: bool = False
    dev_notify: int | None = None
    main_guild: int | None = None

    # functionality
    max_xp: int = 999_999_999
    min_xp: int = -999_999_999
    leaderboard_length: int = 500
    refresh_xp_cap: int = 1
    refresh_xp_period: int = 60
    user_xpr_cooldown: tuple[int, int] = (5, 60)
    guild_pr_cooldown: tuple[int, int] = (1, 60 * 5)
    guild_message_edit_cooldown: tuple[int, int] = (2, 20)
    max_cooldown_period: int = 60

    # command cooldowns
    random_cooldown: tuple[int, int] = (5, 10)
    moststarred_cooldown: tuple[int, int] = (1, 10)
    global_cooldown: tuple[int, int] = (10, 10)

    # cache
    dm_channel_cache_size: int = 1_000
    member_cache_size: int = 1_000
    message_cache_size: int = 1_000
    message_null_cache_size: int = 1_000
    channel_null_cache_size: int = 1_000
    webhook_cache_size: int = 1_000
    vote_emoji_cache_size: int = 1_000

    # botlists & stats
    api_keys: dict[str, str] = field(default_factory=dict)
    """See botblock.org for more details."""

    # links
    docs_link: str | None = None
    support_invite: str | None = None
    bot_invite: str | None = None
    source_link: str | None = None
    patreon_link: str | None = None

    # bot style
    color: int = 0xFFE19C

    # ipc stuff
    host: str = "localhost"
    port: int = 8888
    total_servers: int = 1
    clusters_per_server: int = 1
    shards_per_cluster: int = 1
    ipc_token: str = secrets.token_urlsafe(32)
    certificate_path: str | None = None

    # discord
    discord_token: str = "DISCORD TOKEN"
    owners: list[int] = field(default_factory=list)

    # database
    db_host: str = "localhost"
    db_name: str = "DATABASE NAME"
    db_user: str | None = None
    db_password: str | None = None

    # apis
    tenor_token: str | None = None
    giphy_token: str | None = None

    def save(self) -> None:
        path = Path("config.json")

        dct = asdict(self)
        tosave: dict[str, Any] = {}
        defaults = Config()
        for k, v in dct.items():
            if k not in _ALWAYS_SAVE and getattr(defaults, k) == v:
                continue

            tosave[k] = v

        with path.open("w+") as f:
            f.write(json.dumps(tosave, indent=4))

    @staticmethod
    def load() -> Config:
        path = Path("config.json")

        if not path.exists():
            c = Config()
        else:
            keys = set(inspect.signature(Config).parameters)
            with path.open("r") as f:
                c = Config(
                    **{
                        k: v
                        for k, v in cast(dict, json.loads(f.read())).items()
                        if k in keys
                    }
                )

        c.save()
        return c


CONFIG = Config.load()
