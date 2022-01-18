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

import re
from typing import TYPE_CHECKING, Optional, Tuple, cast

if TYPE_CHECKING:
    from starboard.bot import Bot

TENOR_BASE = "https://api.tenor.com/v1/gifs?ids={0}&key={1}"
GIPHY_BASE = "https://api.giphy.com/v1/gifs/{0}"

TENOR_PATTERN = re.compile(
    r"^http[s]?:\/\/tenor.com\/view\/[a-zA-Z-]+(?P<id>\d+)$"
)
GIPHY_PATTERN = re.compile(
    r"^http[s]?:\/\/giphy.com\/gifs\/[a-zA-Z-]+-(?P<id>[\w]+)$"
)


def _get_gif_id(url: str) -> Optional[Tuple[str, str]]:
    tenor_result = TENOR_PATTERN.match(url)
    if tenor_result:
        return tenor_result.groupdict()["id"], "tenor"
    giphy_result = GIPHY_PATTERN.match(url)
    if giphy_result:
        return giphy_result.groupdict()["id"], "giphy"
    return None


async def _get(bot: Bot, url: str, *args, **kwargs) -> dict:
    async with (await bot.session()).get(
        url, *args, timeout=3, **kwargs
    ) as resp:
        resp.raise_for_status()
        data = cast(dict, await resp.json())
    return data


async def _get_tenor(bot: Bot, gifid: str) -> Optional[str]:
    if not bot.config.tenor_token:
        return None

    try:
        data = await _get(
            bot, TENOR_BASE.format(gifid, bot.config.tenor_token)
        )
        return cast(str, data["results"][0]["media"][0]["gif"]["url"])
    except Exception:
        return None


async def _get_giphy(bot: Bot, gifid: str) -> Optional[str]:
    if not bot.config.giphy_token:
        return None

    try:
        params = {"api_key": bot.config.giphy_token}
        data = await _get(bot, GIPHY_BASE.format(gifid), params=params)
        return cast(str, data["data"]["images"]["fixed_height"]["url"])
    except Exception:
        return None


async def get_gif_url(bot: Bot, url: str) -> Optional[str]:
    """Gets the direct Tenor or Giphy URL for GIF.

    Args:
        bot (Bot): The bot instance.
        url (str): The URL provided by Discord.

    Returns:
        Optional[str]: The direct URL to the GIF.
    """

    result = _get_gif_id(url)
    if not result:
        return None

    gifid, service = result

    if service == "tenor":
        return await _get_tenor(bot, gifid)
    elif service == "giphy":
        return await _get_giphy(bot, gifid)

    return None
