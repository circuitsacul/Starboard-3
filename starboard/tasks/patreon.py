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
from dataclasses import dataclass
from math import floor
from typing import TYPE_CHECKING, Any

import aiohttp

from starboard.config import CONFIG
from starboard.core.notifications import notify
from starboard.database import PatreonStatus, User, goc_user

if TYPE_CHECKING:
    from starboard.bot import Bot


SES: aiohttp.ClientSession | None = None


@dataclass
class Patron:
    total_cents: int
    discord_id: int
    status: PatreonStatus


async def loop_update_patrons(bot: Bot) -> None:
    try:
        while True:
            try:
                await _update_patrons(bot)
            except Exception:
                traceback.print_exc()

            await asyncio.sleep(60 * 5)
    except asyncio.CancelledError:
        global SES
        if SES is not None and not SES.closed:
            await SES.close()


async def _update_patrons(bot: Bot) -> None:
    all_patrons = await _get_all_patrons()
    for p in all_patrons:
        if p.discord_id is None:
            continue

        user = await goc_user(p.discord_id, False)
        if user.patreon_status is not p.status:
            user.patreon_status = p.status
            await user.save()
            await _notify_for_status(user, bot)

        if user.last_patreon_total_cents != p.total_cents:
            user.last_patreon_total_cents = p.total_cents
            user.credits = _credits(user)
            await user.save()


async def _notify_for_status(user: User, bot: Bot) -> None:
    assert user.patreon_status is not PatreonStatus.NONE

    if user.patreon_status is PatreonStatus.FORMER:
        msg = (
            "Hey! It looks like you've removed your pledge on Patreon. We're "
            "sorry to see you go, but we're grateful for all the support "
            "you've given. All the credits you currently have will remain on "
            "your account, and any servers you've enabled premium on will "
            "continue to have premium until the expire.\n\nNote: If you "
            "believe you didn't receive any credits you payed for, you can "
            "get a link to the support server by running `/help` and we'll "
            "sort things out."
        )
    elif user.patreon_status is PatreonStatus.ACTIVE:
        msg = (
            "Thanks for becoming a patron! We appreciate your support. If you "
            "ever have any questions you can get an invite to the support "
            "server by running `/help`.\n\nEssentially, each U.S. dollar we "
            "received is 1 credit you receive. Once you receive "
            f"{CONFIG.credits_per_month} credits, you can redeem 1 month of "
            "premium on any server of your choice."
        )
    elif user.patreon_status is PatreonStatus.DECLINED:
        msg = (
            "Hey! Just wanted to let you know that it looks like Patreon "
            "declined your pledge. This probably means you entered payment "
            "info incorrectly. You won't receive more credits until Patreon "
            "accepts the pledge. If you have any questions, you can get a "
            "link to the support server by running `/help`."
        )

    obj = await bot.cache.gof_user(user.id)
    if obj is not None:
        await notify(obj, msg)


def _credits(user: User) -> int:
    return floor(user.last_patreon_total_cents / 100)


async def _get_session() -> aiohttp.ClientSession:
    global SES
    if SES and not SES.closed:
        return SES
    SES = aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {CONFIG.patreon_token}"}
    )
    return SES


async def _get_all_patrons() -> list[Patron]:
    c = await _fetch("https://www.patreon.com/api/oauth2/v2/campaigns")
    assert len(c["data"]) == 1

    campid = c["data"][0]["id"]

    patrons: list[dict[str, Any]] = []
    users: dict[str, dict[str, Any]] = {}
    next_link: str | None = None
    while True:
        if next_link:
            _p = await _fetch(next_link)
        else:
            _p = await _fetch(
                "https://www.patreon.com/api/oauth2/v2/campaigns/{}/members?"
                "fields[member]=campaign_lifetime_support_cents,patron_status&"
                "include=user&fields[user]=social_connections".format(campid)
            )

        patrons.extend(
            {
                "total_cents": r["attributes"][
                    "campaign_lifetime_support_cents"
                ],
                "user_id": r["relationships"]["user"]["data"]["id"],
                "patron_status": r["attributes"]["patron_status"],
            }
            for r in _p["data"]
        )
        for r in _p["included"]:
            try:
                discord = int(
                    r["attributes"]["social_connections"]["discord"]["user_id"]
                )
            except (KeyError, TypeError):
                discord = None
            users[r["id"]] = {"discord_id": discord}

        try:
            next_link = _p["links"]["next"]
        except KeyError:
            break

    final: list[Patron] = []
    for p in patrons:
        if p["patron_status"] == "active_patron":
            s = PatreonStatus.ACTIVE
        elif p["patron_status"] == "declined_patron":
            s = PatreonStatus.DECLINED
        elif p["patron_status"] == "former_patron":
            s = PatreonStatus.FORMER
        else:
            s = PatreonStatus.NONE
        final.append(
            Patron(p["total_cents"], users[p["user_id"]]["discord_id"], s)
        )

    return final


async def _fetch(path: str, params: dict | None = None) -> dict:
    s = await _get_session()
    async with s.get(path, **(params or {})) as resp:
        resp.raise_for_status()
        d = await resp.json()

    assert isinstance(d, dict)
    return d