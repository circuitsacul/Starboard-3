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
    patron_role: int | None = None
    donor_role: int | None = None

    # starboard settings restrictions
    max_xp_mul: float = 10.0
    min_xp_mul: float = -10.0
    min_required: int = 1
    max_required: int = 500
    min_required_remove: int = -500
    max_required_remove: int = 490
    max_cooldown_period: int = 60
    max_cooldown_cap: int = 60
    max_newer_than: int = 86_400 * 7  # 1 week
    max_older_than: int = 86_400 * 7
    max_vote_emojis: int = 10
    max_starboards: int = 10
    max_starboard_name: int = 32
    min_starboard_name: int = 3

    # autostar settings restrictions
    max_maxchars: int = 4_000
    max_minchars: int = 4_000
    max_asc_emojis: int = 10
    max_autostar: int = 10
    max_asc_name: int = 32
    min_asc_name: int = 3

    # override settings restrictions
    max_ov_name: int = 32
    min_ov_name: int = 3
    max_ov_channels: int = 100
    max_ov_per_starboard: int = 10

    # xprole restrictions
    max_xp_roles: int = 10
    max_xpr_xp: int = 5_000
    min_xpr_xp: int = 5

    # posrole restrictions
    max_posroles: int = 10
    max_pr_members: int = 1_000
    min_pr_members: int = 1

    # permrole restrictions
    max_permroles: int = 50

    # non-premium restrictions
    np_max_starboards: int = 3
    np_max_autostar: int = 3
    np_max_asc_emojis: int = 3
    np_max_vote_emojis: int = 3

    # functionality
    max_xp: int = 999_999_999
    min_xp: int = -999_999_999
    leaderboard_length: int = 50
    refresh_xp_cap: int = 1
    refresh_xp_period: int = 60
    credits_per_month: int = 3
    days_per_month: int = 32  # just be safe

    # command cooldowns
    random_cooldown: tuple[int, int] = (5, 10)
    moststarred_cooldown: tuple[int, int] = (1, 10)
    global_cooldown: tuple[int, int] = (10, 10)

    # functionality cooldowns
    guild_vote_cooldown: tuple[int, int] = (500, 30)
    guild_message_send_cooldown: tuple[int, int] = (10, 60 * 5)
    guild_message_delete_cooldown: tuple[int, int] = (10, 10)
    guild_message_edit_cooldown: tuple[int, int] = (2, 20)
    guild_asc_cooldown: tuple[int, int] = (5, 10)
    user_xpr_cooldown: tuple[int, int] = (5, 60)
    guild_pr_cooldown: tuple[int, int] = (1, 60 * 5)

    # tasks
    check_expired_premium_delay: int = 60 * 60
    update_patreons_delay: int = 60 * 5
    post_stats_delay: int = 60 * 10
    broadcast_stats_delay: int = 60

    # cache
    dm_channel_cache_size: int = 1_000
    member_cache_size: int = 1_000
    message_cache_size: int = 1_000
    message_null_cache_size: int = 1_000
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
    patreon_token: str | None = None

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
