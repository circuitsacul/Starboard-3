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
from typing import TYPE_CHECKING

from starboard.config import CONFIG
from starboard.stats import post_stats

if TYPE_CHECKING:
    from starboard.bot import Bot


async def loop_post_stats(bot: Bot) -> None:
    if CONFIG.development:
        return

    if bot.cluster.cluster_id != 0:
        return

    while True:
        await asyncio.sleep(CONFIG.post_delay)

        try:
            work, fail = await post_stats(bot)
        except Exception:
            traceback.print_exc()

        if fail:
            bot.cluster.logger.warn(
                "The following bot lists failed to post:\n - "
                + "\n - ".join(fail)
            )


async def loop_broadcast_stats(bot: Bot) -> None:
    while True:
        await asyncio.sleep(CONFIG.post_delay - 30)

        await bot.cluster.ipc.send_event(
            [bot.cluster.ipc.clusters_by_cluster_id[0].uid],
            "cluster_stats",
            {"guild_count": len(bot.cache._guild_entries)},
        )

        await asyncio.sleep(30)
