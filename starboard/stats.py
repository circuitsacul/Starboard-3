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

import json
from typing import TYPE_CHECKING

from .config import CONFIG

if TYPE_CHECKING:
    from starboard.bot import Bot


BASE_URL = "https://botblock.org/api/count"


async def post_stats(
    bot: Bot, guild_count: int | None = None
) -> tuple[list[str], list[str]]:
    ses = await bot.session()
    data: dict[str, str | int] = {
        "bot_id": str(bot.me.id),
        "server_count": guild_count or sum(bot.bot_stats.values()),
        **CONFIG.api_keys,
    }
    async with ses.post(BASE_URL, data=json.dumps(data)) as ret:
        ret.raise_for_status()
        data = await ret.json()

    return data["success"].keys(), data["failure"].keys()  # type: ignore
