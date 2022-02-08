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
    # settings restrictions
    max_whn_len: int = 32
    max_wha_len: int = 512
    min_required: int = 1
    max_required: int = 512
    min_required_remove: int = -1
    max_required_remove: int = 500

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
    testing_guild: Optional[int] = None
    owners: List[int] = field(default_factory=list)

    # database
    db_host: str = "localhost"
    db_name: str = "DATABASE NAME"
    db_user: Optional[str] = None
    db_password: Optional[str] = None

    # apis
    tenor_token: Optional[str] = None
    giphy_token: Optional[str] = None

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
