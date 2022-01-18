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

import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Literal, Optional, Union


@dataclass
class Config:
    # ipc stuff
    host: str
    port: int
    total_servers: int
    clusters_per_server: int
    shards_per_cluster: int
    ipc_token: str
    certificate_path: Optional[str]

    # discord
    discord_token: str
    testing_guilds: Union[List[int], Literal[False]]

    # database
    db_name: str
    db_user: Union[str, None]
    db_password: Union[str, None]

    @classmethod
    def load(cls) -> "Config":
        pth = Path("config.json")

        if not pth.exists():
            with pth.open("w+") as f:
                ad = asdict(
                    Config(
                        host="HOST OF BRAIN SERVER",
                        port=8888,
                        total_servers=1,
                        clusters_per_server=1,
                        shards_per_cluster=1,
                        ipc_token=secrets.token_urlsafe(32),
                        certificate_path=None,
                        discord_token="DISCORD BOT TOKEN",
                        testing_guilds=False,
                        db_name="DATABASE NAME",
                        db_user=None,
                        db_password=None,
                    )
                )
                f.write(json.dumps(ad, indent=4))

        with pth.open("r") as f:
            return Config(**json.loads(f.read()))
