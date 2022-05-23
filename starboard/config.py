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

import inspect
import json
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

_ALWAYS_SAVE = ["discord_token", "db_name", "ipc_token"]


@dataclass
class Config:
    # misc
    development: bool = False
    dev_notify: Optional[int] = None
    main_guild: Optional[int] = None
    patron_role: Optional[int] = None
    donor_role: Optional[int] = None

    # starboard settings restrictions
    max_xp_mul: float = 10.0
    min_xp_mul: float = -10.0
    min_required: int = 1
    max_required: int = 512
    min_required_remove: int = -1
    max_required_remove: int = 500
    max_cooldown_period: int = 60
    max_cooldown_cap: int = 60
    max_upvote_emojis: int = 5
    max_starboards: int = 10

    # autostar settings restrictions
    max_maxchars: int = 4000
    max_minchars: int = 4000
    max_asc_emojis: int = 5
    max_autostar: int = 10

    # override settings restrictions
    max_ov_name: int = 32
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
    np_max_autostar: int = 1
    np_max_asc_emojis: int = 3
    np_max_upvote_emojis: int = 3

    # functionality
    max_xp: int = 999_999_999
    leaderboard_length: int = 50
    asc_cooldown_cap: int = 5
    asc_cooldown_period: int = 10
    xpr_cooldown_cap: int = 10
    xpr_cooldown_period: int = 60
    pr_cooldown_cap: int = 1
    pr_cooldown_period: int = 60 * 5
    refresh_xp_cap: int = 1
    refresh_xp_period: int = 60
    edit_cooldown_cap: int = 3
    edit_cooldown_period: int = 20
    guild_vote_cooldown_cap: int = 500
    guild_vote_cooldown_period: int = 30
    credits_per_month: int = 3
    days_per_month: int = 32  # just be safe

    # tasks
    check_expired_premium_delay: int = 60 * 60
    update_patreons_delay: int = 60 * 5
    post_stats_delay: int = 60 * 10

    # cache
    member_cache_size: int = 1_000
    user_null_cache_size: int = 1_000
    message_cache_size: int = 1_000
    message_null_cache_size: int = 1_000
    webhook_cache_size: int = 1_000
    vote_emoji_cache_size: int = 1_000

    # botlists & stats
    api_keys: Dict[str, str] = field(default_factory=dict)
    """See botblock.org for more details."""

    # links
    docs_link: Optional[str] = None
    support_invite: Optional[str] = None
    bot_invite: Optional[str] = None
    source_link: Optional[str] = None
    patreon_link: Optional[str] = None

    # bot style
    color: int = int("FFE19C", 16)

    # ipc stuff
    host: str = "localhost"
    port: int = 8888
    total_servers: int = 1
    clusters_per_server: int = 1
    shards_per_cluster: int = 1
    ipc_token: str = secrets.token_urlsafe(32)
    certificate_path: Optional[str] = None

    # discord
    discord_token: str = "DISCORD TOKEN"
    owners: List[int] = field(default_factory=list)

    # database
    db_host: str = "localhost"
    db_name: str = "DATABASE NAME"
    db_user: Optional[str] = None
    db_password: Optional[str] = None

    # apis
    tenor_token: Optional[str] = None
    giphy_token: Optional[str] = None
    patreon_token: Optional[str] = None

    def save(self):
        pth = Path("config.json")

        dct = asdict(self)
        tosave: dict[str, Any] = {}
        defaults = self.__class__()
        for k, v in dct.items():
            if k not in _ALWAYS_SAVE and getattr(defaults, k) == v:
                continue

            tosave[k] = v

        with pth.open("w+") as f:
            f.write(json.dumps(tosave, indent=4))

    @classmethod
    def load(cls) -> "Config":
        pth = Path("config.json")

        if not pth.exists():
            c = Config()
        else:
            keys = set(inspect.signature(Config).parameters)
            with pth.open("r") as f:
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
