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
from typing import List, Optional, cast


@dataclass
class Config:
    # development
    development: bool = False
    dev_notify: Optional[int] = None
    dev_guild: Optional[int] = None

    # starboard settings restrictions
    max_whn_len: int = 32
    max_wha_len: int = 512
    min_required: int = 1
    max_required: int = 512
    min_required_remove: int = -1
    max_required_remove: int = 500
    max_cooldown_period: int = 60
    max_cooldown_cap: int = 60
    max_star_emojis: int = 5
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

    # non-premium restrictions
    np_max_starboards: int = 3
    np_max_autostar: int = 1
    np_max_asc_emojis: int = 3
    np_max_star_emojis: int = 3
    np_allow_webhook: bool = False

    # functionality
    max_xp: int = 999_999_999
    leaderboard_length: int = 50
    asc_cooldown_cap: int = 5
    asc_cooldown_period: int = 10
    credits_per_month: int = 3
    days_per_month: int = 32  # just be safe

    # links
    docs_link: Optional[str] = None
    support_invite: Optional[str] = None
    bot_invite: Optional[str] = None
    source_link: Optional[str] = None

    # bot style
    color: int = int("FFE19C", 16)

    # ipc stuff
    host: str = "HOST OF BRAIN SERVER"
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
        with pth.open("w+") as f:
            f.write(json.dumps(asdict(self), indent=4))

    @classmethod
    def load(cls) -> "Config":
        pth = Path("config.json")

        if not pth.exists():
            c = Config()
        else:
            with pth.open("r") as f:
                c = Config(
                    **{
                        k: v
                        for k, v in cast(dict, json.loads(f.read())).items()
                        if k in inspect.signature(Config).parameters
                    }
                )

        c.save()
        return c


CONFIG = Config.load()
