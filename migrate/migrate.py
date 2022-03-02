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
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable

import emoji
import pytz
from apgorm.connection import Connection as OrmCon
from asyncpg.connection import Connection as ApgCon
from tqdm import tqdm

import starboard.database as newdb
from starboard.config import CONFIG
from starboard.database import Database as NewDB

from .old_db import Database as OldDB


@dataclass
class App:
    new: NewDB
    old: OldDB


async def migrate() -> None:
    newdb = NewDB()
    await newdb.connect(
        migrate=True,
        host=CONFIG.db_host,
        database=CONFIG.db_name,
        user=CONFIG.db_user,
        password=CONFIG.db_password,
    )
    olddb = OldDB()
    await olddb.connect()

    app = App(newdb, olddb)

    await _run(app, _migrate_guilds)
    await _run(app, _migrate_users)
    await _run(app, _migrate_members)
    await _run(app, _migrate_autostars)
    await _run(app, _migrate_starboards)
    await _run(app, _migrate_orig_messages)
    await _run(app, _migrate_starboard_messages)
    await _run(app, _migrate_reactions)
    await _run(app, _migrate_xproles)
    await _run(app, _migrate_posroles)
    await _run(app, _migrate_channel_bl)
    await _run(app, _migrate_role_bl)


async def _run(
    app: App, func: Callable[[OrmCon, ApgCon], Awaitable[None]]
) -> None:
    assert app.new.pool
    async with app.old.pool.acquire() as old:
        async with old.transaction():
            async with app.new.pool.acquire() as new:
                async with new.transaction():
                    await func(new, old)


async def _migrate_guilds(new: OrmCon, old: ApgCon) -> None:
    for oldguild in tqdm(await old.fetch("SELECT * FROM guilds"), "Guilds"):
        prem_end: datetime | None = oldguild["premium_end"]
        if prem_end:
            prem_end = prem_end.replace(tzinfo=pytz.UTC)
        await new.execute(
            "INSERT INTO guilds (id, premium_end) VALUES ($1, $2)",
            [oldguild["id"], prem_end],
        )


async def _migrate_users(new: OrmCon, old: ApgCon) -> None:
    total = await old.fetchval("SELECT count(1) FROM users")
    count = 0
    with tqdm(desc="Users", total=total) as pb:
        async for olduser in old.cursor(
            "SELECT * FROM users", prefetch=10_000
        ):
            count += 1
            if count % 1000 == 0:
                pb.update(count)
                count = 0
            await new.execute(
                "INSERT INTO users (id, is_bot, credits, "
                "last_patreon_total_cents, patreon_status) "
                "VALUES ($1, $2, $3, 0, 0)",
                [olduser["id"], olduser["is_bot"], olduser["credits"]],
            )


async def _migrate_members(new: OrmCon, old: ApgCon) -> None:
    total = await old.fetchval("SELECT count(1) FROM members")
    count = 0
    with tqdm(desc="Members", total=total) as pb:
        async for oldmemb in old.cursor(
            "SELECT * FROM members", prefetch=10_000
        ):
            count += 1
            if count % 1000 == 0:
                pb.update(count)
                count = 0
            await new.execute(
                "INSERT INTO members (user_id, guild_id, xp, "
                "autoredeem_enabled) VALUES ($1, $2, $3, $4)",
                [
                    oldmemb["user_id"],
                    oldmemb["guild_id"],
                    oldmemb["xp"],
                    oldmemb["autoredeem"],
                ],
            )


async def _migrate_autostars(new: OrmCon, old: ApgCon) -> None:
    bad_emojis: int = 0
    for oldasc in tqdm(
        await old.fetch("SELECT * FROM aschannels"), "AutoStar Channels"
    ):
        emojis = await old.fetch(
            "SELECT * FROM asemojis WHERE aschannel_id=$1", oldasc["id"]
        )
        newemojis: list[str] = []
        for e in emojis:
            name = e["name"]
            try:
                int(name)
            except ValueError:
                if not emoji.is_emoji(name):  # type: ignore
                    bad_emojis += 1
                    continue

            newemojis.append(name)

        await new.execute(
            "INSERT INTO aschannels (id, guild_id, emojis, min_chars, "
            "require_image, delete_invalid) VALUES ($1, $2, $3, "
            "$4, $5, $6)",
            [
                oldasc["id"],
                oldasc["guild_id"],
                newemojis,
                oldasc["min_chars"],
                oldasc["require_image"],
                oldasc["delete_invalid"],
            ],
        )

    print(f"Bad Emojis: {bad_emojis}")


async def _migrate_starboards(new: OrmCon, old: ApgCon) -> None:
    bad_emojis: int = 0
    for oldsb in tqdm(
        await old.fetch("SELECT * FROM starboards"), "Starboards"
    ):
        emojis = await old.fetch(
            "SELECT * FROM sbemojis WHERE starboard_id=$1", oldsb["id"]
        )
        newemojis: list[str] = []
        for e in emojis:
            if e["d_id"] is None:
                name = e["name"]
            else:
                name = str(e["d_id"])
            try:
                int(name)
            except ValueError:
                if not emoji.is_emoji(name):  # type: ignore
                    bad_emojis += 1
                    continue

            newemojis.append(name)

        await newdb.Starboard(
            id=oldsb["id"],
            guild_id=oldsb["guild_id"],
            required=oldsb["required"],
            required_remove=max(-1, oldsb["rtl"]),
            self_star=oldsb["self_star"],
            allow_bots=oldsb["bots_on_sb"],
            link_edits=oldsb["link_edits"],
            link_deletes=oldsb["link_deletes"],
            star_emojis=newemojis,
            require_image=oldsb["require_image"],
        ).create(con=new)

    print(f"Bad Emojis: {bad_emojis}")


async def _migrate_orig_messages(new: OrmCon, old: ApgCon) -> None:
    sbids_guild: dict[int, set[int]] = {}
    for sb in await new.fetchmany("SELECT * FROM starboards"):
        sbids_guild.setdefault(sb["guild_id"], set()).add(sb["id"])

    total = await old.fetchval(
        "SELECT count(1) FROM messages WHERE is_orig=True"
    )
    count = 0
    with tqdm(desc="Original Messages", total=total) as pb:
        async for oldmsg in old.cursor(
            "SELECT * FROM messages WHERE is_orig=True", prefetch=10000
        ):
            count += 1
            if count % 1000 == 0:
                pb.update(count)
                count = 0
            forced_to = (
                set()
                if not oldmsg["is_forced"]
                else sbids_guild.get(oldmsg["guild_id"], set())
            )
            await new.execute(
                "INSERT INTO messages (id, guild_id, channel_id, author_id, "
                "is_nsfw, forced_to, trashed, trash_reason, frozen) VALUES "
                "($1, $2, $3, $4, $5, $6, $7, NULL, $8)",
                [
                    oldmsg["id"],
                    oldmsg["guild_id"],
                    oldmsg["channel_id"],
                    oldmsg["user_id"],
                    oldmsg["is_nsfw"],
                    forced_to,
                    oldmsg["is_trashed"],
                    oldmsg["is_frozen"],
                ],
            )


async def _migrate_starboard_messages(new: OrmCon, old: ApgCon) -> None:
    sbids: set[int] = {
        r["id"] for r in await old.fetch("SELECT id FROM starboards")
    }

    missing_sb: int = 0
    missing_orig: int = 0

    count = 0
    total = await old.fetchval(
        "SELECT count(1) FROM messages WHERE is_orig=False"
    )
    with tqdm(desc="Starboard Messages", total=total) as pb:
        async for oldmsg in old.cursor(
            "SELECT * FROM messages WHERE is_orig=False", prefetch=10_000
        ):
            count += 1
            if count % 1000 == 0:
                pb.update(count)
                count = 0

            if oldmsg["channel_id"] not in sbids:
                missing_sb += 1
                continue

            ret = await new.fetchval(
                "SELECT 1 FROM messages WHERE id=$1",
                [oldmsg["orig_message_id"]],
            )
            if not ret:
                missing_orig += 1
                continue

            await new.execute(
                "INSERT INTO sb_messages (message_id, starboard_id, "
                "sb_message_id, last_known_star_count) "
                "VALUES ($1, $2, $3, $4) "
                "ON CONFLICT (message_id, starboard_id) DO NOTHING ",
                [
                    oldmsg["orig_message_id"],
                    oldmsg["channel_id"],
                    oldmsg["id"],
                    oldmsg["points"] or 0,
                ],
            )

    print(f"Missing Starboard: {missing_sb}")
    print(f"Missing Orig: {missing_orig}")


async def _migrate_reactions(new: OrmCon, old: ApgCon) -> None:
    sb_emoji_map: dict[int, dict[int, set[str]]] = {}

    for s in await newdb.Starboard.fetch_query(new).fetchmany():
        sb_emoji_map.setdefault(s.guild_id, dict()).setdefault(
            s.id, set()
        ).update(s.star_emojis)

    def get_sb(guild: int, reaction: str) -> set[int] | None:
        sbids: set[int] = set()
        sb = sb_emoji_map.get(guild)
        if not sb:
            return None
        for sid, emojis in sb.items():
            if reaction in emojis:
                sbids.add(sid)

        return sbids

    invalid = 0

    total = await old.fetchval("SELECT count(1) FROM reactions")
    count = 0
    with tqdm(desc="Reactions", total=total) as pb:
        async for oldreact in old.cursor(
            "SELECT * FROM reactions", prefetch=10_000
        ):
            count += 1
            if count % 1000 == 0:
                pb.update(count)
                count = 0

            sbids = get_sb(int(oldreact["guild_id"]), oldreact["name"])
            if not sbids:
                invalid += 1
                continue

            for id in sbids:
                await new.execute(
                    "INSERT INTO stars (message_id, starboard_id, user_id) "
                    "VALUES ($1, $2, $3) ON CONFLICT (message_id, "
                    "starboard_id, user_id) DO NOTHING",
                    [oldreact["message_id"], id, oldreact["user_id"]],
                )

    print(f"Invalid Reaction: {invalid}")


async def _migrate_xproles(new: OrmCon, old: ApgCon) -> None:
    for oldxp in tqdm(await old.fetch("SELECT * FROM xproles")):
        await newdb.XPRole(
            id=oldxp["id"],
            guild_id=oldxp["guild_id"],
            required=max(5, oldxp["req_xp"]),
        ).create(new)


async def _migrate_posroles(new: OrmCon, old: ApgCon) -> None:
    for oldpr in tqdm(await old.fetch("SELECT * FROM posroles")):
        gid = oldpr["guild_id"]
        mu = oldpr["max_users"]
        if await newdb.PosRole.exists(new, guild_id=gid, max_members=mu):
            mu += 1
        await newdb.PosRole(
            id=oldpr["id"], guild_id=gid, max_members=mu
        ).create(con=new)


async def _migrate_channel_bl(new: OrmCon, old: ApgCon) -> None:
    sb: newdb.Starboard
    for x, sb in enumerate(
        tqdm(await newdb.Starboard.fetch_query(new).fetchmany())
    ):
        oldbl = await old.fetch(
            "SELECT * FROM channelbl WHERE starboard_id=$1 AND "
            "is_whitelist=False",
            sb.id,
        )
        oldwl = await old.fetch(
            "SELECT * FROM channelbl WHERE starboard_id=$1 AND "
            "is_whitelist=True",
            sb.id,
        )

        if oldwl:
            channels = [c["channel_id"] for c in oldwl]
            wl = True
        else:
            channels = [c["channel_id"] for c in oldbl]
            wl = False

        if not channels:
            continue

        await newdb.Override._from_raw(
            guild_id=sb.guild_id,
            name="channel-" + ("wl" if wl else "bl") + f"-{x}",
            starboard_id=sb.id,
            channel_ids=channels,
            _overrides=json.dumps({"enabled": wl is True}),
        ).create(new)
        if wl:
            sb.enabled = False
            await sb.save(new)


async def _migrate_role_bl(new: OrmCon, old: ApgCon) -> None:
    role_bl_and_wl = 0

    sb: newdb.Starboard
    for sb in tqdm(await newdb.Starboard.fetch_query(new).fetchmany()):
        role_wl = await old.fetch(
            "SELECT * FROM rolebl WHERE starboard_id=$1 AND is_whitelist=True",
            sb.id,
        )
        role_bl = await old.fetch(
            "SELECT * FROM rolebl WHERE starboard_id=$1 AND "
            "is_whitelist=False",
            sb.id,
        )

        if (not role_wl) and (not role_bl):
            continue

        bl_roles: list[int] = [r["role_id"] for r in role_bl]
        wl_roles: list[int] = [r["role_id"] for r in role_wl]

        if wl_roles and not bl_roles:
            bl_roles.append(sb.guild_id)

        async def create(rid: int, wl: bool) -> None:
            nonlocal role_bl_and_wl
            pr = await newdb.PermRole.exists(new, id=rid)
            if not pr:
                pr = await newdb.PermRole(id=rid, guild_id=sb.guild_id).create(
                    new
                )

            if await newdb.PermRoleStarboard.exists(
                new, permrole_id=pr.id, starboard_id=sb.id
            ):
                role_bl_and_wl += 1
                return

            await newdb.PermRoleStarboard(
                permrole_id=pr.id, starboard_id=sb.id, give_stars=wl
            ).create(new)

        for role in bl_roles:
            await create(role, False)
        for role in wl_roles:
            await create(role, True)

    print(f"Roles that were blacklisted and whitelisted: {role_bl_and_wl}")
