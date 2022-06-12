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

# NOTE: changes
# - guild_id of reactions (btree, allow for ordering)
# - drop reaction id=21150258
# Drop indexes/FKs for
# - votes
# - members
# - orig messages
# - sb messages

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import emoji
import hikari
from apgorm.connection import Connection as OrmCon
from asyncpg.connection import Connection as ApgCon
from hikari import GatewayBot
from tqdm import tqdm

import starboard.database as newdb
from starboard.config import CONFIG
from starboard.database import Database as NewDB

from .old_db import Database as OldDB
from .old_reaction_valid import is_user_blacklisted

CHUNK = 10_000


@dataclass
class App:
    new: NewDB
    old: OldDB
    bot: GatewayBot


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

    bot = GatewayBot(CONFIG.discord_token)
    await bot.start()

    app = App(newdb, olddb, bot)

    print("dropping indexes...")
    with open("migrate/drop_indexes.sql") as f:
        await newdb.execute(f.read(), [])

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

    print("creating indexes...")
    with open("migrate/create_indexes.sql") as f:
        await newdb.execute(f.read(), [])

    await bot.close()


async def _run(
    app: App, func: Callable[[OrmCon, ApgCon, GatewayBot], Awaitable[None]]
) -> None:
    assert app.new.pool
    async with app.old.pool.acquire() as old:
        async with old.transaction():
            async with app.new.pool.acquire() as new:
                async with new.transaction():
                    await func(new, old, app.bot)


async def _migrate_guilds(new: OrmCon, old: ApgCon, bot: GatewayBot) -> None:
    for oldguild in tqdm(await old.fetch("SELECT * FROM guilds"), "Guilds"):
        prem_end: datetime | None = oldguild["premium_end"]
        if prem_end:
            prem_end = prem_end.replace(tzinfo=timezone.utc)
        await new.execute(
            "INSERT INTO guilds (guild_id, premium_end) VALUES ($1, $2)",
            [oldguild["id"], prem_end],
        )


async def _migrate_users(new: OrmCon, old: ApgCon, bot: GatewayBot) -> None:
    total = await old.fetchval("SELECT count(1) FROM users")
    count = 0
    args: list[list[Any]] = []

    async def do_insert():
        await new.con.copy_records_to_table(
            "users",
            records=args,
            columns=[
                "user_id",
                "is_bot",
                "credits",
                "donated_cents",
                "patreon_status",
            ],
        )
        args.clear()

    with tqdm(desc="Users", total=total) as pb:
        async for olduser in old.cursor("SELECT * FROM users", prefetch=CHUNK):
            count += 1
            if count % CHUNK == 0:
                pb.update(count)
                count = 0
                await do_insert()
            args.append(
                [olduser["id"], olduser["is_bot"], olduser["credits"], 0, 0]
            )
        await do_insert()
        pb.update(count)


async def _migrate_members(new: OrmCon, old: ApgCon, bot: GatewayBot) -> None:
    total = await old.fetchval("SELECT count(1) FROM members")
    count = 0
    args: list[list[Any]] = []

    async def do_insert():
        await new.con.copy_records_to_table(
            "members",
            records=args,
            columns=["user_id", "guild_id", "xp", "autoredeem_enabled"],
        )
        args.clear()

    with tqdm(desc="Members", total=total) as pb:
        async for oldmemb in old.cursor(
            "SELECT * FROM members", prefetch=CHUNK
        ):
            count += 1
            if count % CHUNK == 0:
                pb.update(count)
                count = 0
                await do_insert()
            args.append(
                [
                    oldmemb["user_id"],
                    oldmemb["guild_id"],
                    oldmemb["xp"],
                    oldmemb["autoredeem"],
                ]
            )
        pb.update(count)
        await do_insert()


async def _migrate_autostars(
    new: OrmCon, old: ApgCon, bot: GatewayBot
) -> None:
    bad_emojis: int = 0
    for x, oldasc in enumerate(
        tqdm(
            await old.fetch("SELECT * FROM aschannels ORDER BY guild_id"),
            "AutoStar Channels",
        )
    ):
        ch = bot.cache.get_guild_channel(int(oldasc["id"]))
        chname = ch.name if ch else "autostar"
        channel_name = f"{chname}-{x}"

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
            "INSERT INTO aschannels (name, channel_id, guild_id, emojis, "
            "min_chars, require_image, delete_invalid, prem_locked) VALUES "
            "($1, $2, $3, $4, $5, $6, $7, false)",
            [
                channel_name,
                oldasc["id"],
                oldasc["guild_id"],
                newemojis,
                oldasc["min_chars"],
                oldasc["require_image"],
                oldasc["delete_invalid"],
            ],
        )

    print(f"Bad Emojis: {bad_emojis}")


async def _migrate_starboards(
    new: OrmCon, old: ApgCon, bot: GatewayBot
) -> None:
    bad_emojis: int = 0
    for x, oldsb in enumerate(
        tqdm(await old.fetch("SELECT * FROM starboards"), "Starboards")
    ):
        ch = bot.cache.get_guild_channel(int(oldsb["id"]))
        chname = ch.name if ch else "starboard"
        channel_name = f"{chname}-{x}"

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
            name=channel_name,
            channel_id=oldsb["id"],
            guild_id=oldsb["guild_id"],
            required=oldsb["required"],
            required_remove=max(-1, oldsb["rtl"]),
            self_vote=oldsb["self_star"],
            allow_bots=oldsb["bots_on_sb"],
            link_edits=oldsb["link_edits"],
            link_deletes=oldsb["link_deletes"],
            upvote_emojis=newemojis,
            require_image=oldsb["require_image"],
        ).create(con=new)

    print(f"Bad Emojis: {bad_emojis}")


async def _migrate_orig_messages(
    new: OrmCon, old: ApgCon, bot: GatewayBot
) -> None:
    sbids_guild: dict[int, set[int]] = {}
    for sb in await new.fetchmany("SELECT * FROM starboards"):
        sbids_guild.setdefault(sb["guild_id"], set()).add(sb["id"])

    total = await old.fetchval(
        "SELECT count(1) FROM messages WHERE is_orig=True"
    )
    count = 0
    args: list[list[Any]] = []

    async def do_insert():
        await new.con.copy_records_to_table(
            "messages",
            records=args,
            columns=[
                "message_id",
                "guild_id",
                "channel_id",
                "author_id",
                "is_nsfw",
                "forced_to",
                "trashed",
                "trash_reason",
                "frozen",
            ],
        )
        args.clear()

    with tqdm(desc="Original Messages", total=total) as pb:
        async for oldmsg in old.cursor(
            "SELECT * FROM messages WHERE is_orig=True", prefetch=CHUNK
        ):
            count += 1
            if count % CHUNK == 0:
                pb.update(count)
                count = 0
                await do_insert()
            forced_to = (
                set()
                if not oldmsg["is_forced"]
                else sbids_guild.get(oldmsg["guild_id"], set())
            )
            args.append(
                [
                    oldmsg["id"],
                    oldmsg["guild_id"],
                    oldmsg["channel_id"],
                    oldmsg["user_id"],
                    oldmsg["is_nsfw"],
                    forced_to,
                    oldmsg["is_trashed"],
                    None,
                    oldmsg["is_frozen"],
                ]
            )
        pb.update(count)
        count = 0
        await do_insert()


async def _migrate_starboard_messages(
    new: OrmCon, old: ApgCon, bot: GatewayBot
) -> None:
    sbids: set[int] = {
        r["id"] for r in await old.fetch("SELECT id FROM starboards")
    }
    pairs: set[tuple[int, int]] = set()
    valid_orig_ids: set[int] = {
        r["message_id"]
        for r in await new.fetchmany("SELECT message_id FROM messages")
    }
    sb_chid_to_sbid: dict[int, int] = {
        s.channel_id: s.id for s in await newdb.Starboard.fetchmany(new)
    }

    missing_sb: int = 0
    missing_orig: int = 0
    duplicate: int = 0

    count = 0
    total = await old.fetchval(
        "SELECT count(1) FROM messages WHERE is_orig=False"
    )
    args: list[list[Any]] = []

    async def do_insert():
        await new.con.copy_records_to_table(
            "sb_messages",
            records=args,
            columns=[
                "message_id",
                "starboard_id",
                "sb_message_id",
                "last_known_point_count",
            ],
        )
        args.clear()

    with tqdm(desc="Starboard Messages", total=total) as pb:
        async for oldmsg in old.cursor(
            "SELECT * FROM messages WHERE is_orig=False", prefetch=CHUNK
        ):
            count += 1
            if count % CHUNK == 0:
                pb.update(count)
                count = 0
                await do_insert()

            if oldmsg["channel_id"] not in sbids:
                missing_sb += 1
                continue

            uq = (oldmsg["orig_message_id"], oldmsg["channel_id"])
            if uq in pairs:
                duplicate += 1
                continue
            pairs.add(uq)

            if oldmsg["orig_message_id"] not in valid_orig_ids:
                missing_orig += 1
                continue

            args.append(
                [
                    oldmsg["orig_message_id"],
                    sb_chid_to_sbid[int(oldmsg["channel_id"])],
                    oldmsg["id"],
                    oldmsg["points"] or 0,
                ]
            )
        pb.update(count)
        count = 0
        await do_insert()

    print(f"Missing Orig: {missing_orig}")
    print(f"Missing Starboard: {missing_sb}")
    print(f"Duplicates: {duplicate}")


async def _migrate_reactions(
    new: OrmCon, old: ApgCon, bot: GatewayBot
) -> None:
    sb_emoji_map: dict[int, dict[int, set[str]]] = {}
    sb_chid_to_sbid: dict[int, int] = {
        s.channel_id: s.id for s in await newdb.Starboard.fetchmany(new)
    }
    current_guild: int = -1
    current_guild_member_roles: dict[int, set[int]] = {}
    current_guild_role_wl: dict[int, set[int]] = {}
    current_guild_role_bl: dict[int, set[int]] = {}
    current_guild_check_rbl: bool = True
    current_guild_message_authors: dict[int, int] = {}
    unique: set[tuple[int, int, int, int]] = set()

    for s in await newdb.Starboard.fetch_query(new).fetchmany():
        sb_emoji_map.setdefault(s.guild_id, dict()).setdefault(
            s.channel_id, set()
        ).update(s.upvote_emojis)

    def get_sb(guild: int, reaction: str) -> set[int] | None:
        sbids: set[int] = set()
        sb = sb_emoji_map.get(guild)
        if not sb:
            return None
        for sid, emojis in sb.items():
            if reaction in emojis:
                sbids.add(sid)

        return sbids

    no_starboards = 0
    duplicate = 0
    role_blacklisted = 0
    left_guilds_with_bl = 0

    total = await old.fetchval("SELECT count(1) FROM reactions")
    count = 0
    args: list[tuple[Any, ...]] = []

    async def do_insert():
        await new.con.copy_records_to_table(
            "votes",
            records=args,
            columns=[
                "message_id",
                "starboard_id",
                "user_id",
                "target_author_id",
                "is_downvote",
            ],
        )
        args.clear()

    with tqdm(desc="Reactions", total=total) as pb:
        async for oldreact in old.cursor(
            "SELECT * FROM reactions ORDER BY guild_id", prefetch=CHUNK
        ):
            count += 1
            if not (count % CHUNK):
                pb.update(count)
                count = 0
                await do_insert()

            sbids = get_sb(int(oldreact["guild_id"]), oldreact["name"])
            if not sbids:
                no_starboards += 1
                continue

            if current_guild != oldreact["guild_id"]:
                unique.clear()
                current_guild = oldreact["guild_id"]
                current_guild_role_bl.clear()
                current_guild_role_wl.clear()

                for sbid in sb_emoji_map[current_guild].keys():
                    role_wl = set(
                        r["role_id"]
                        for r in await old.fetch(
                            "SELECT role_id FROM rolebl WHERE "
                            "is_whitelist=True AND starboard_id=$1",
                            sbid,
                        )
                    )
                    role_bl = set(
                        r["role_id"]
                        for r in await old.fetch(
                            "SELECT role_id FROM rolebl WHERE "
                            "is_whitelist=False AND starboard_id=$1",
                            sbid,
                        )
                    )
                    if role_wl:
                        current_guild_role_wl[sbid] = role_wl
                    if role_bl:
                        current_guild_role_bl[sbid] = role_bl

                current_guild_check_rbl = False
                if current_guild_role_wl or current_guild_role_bl:
                    try:
                        current_guild_member_roles = {
                            m.id: set(m.role_ids)
                            for m in await bot.rest.fetch_members(
                                current_guild
                            )
                        }
                    except hikari.ForbiddenError:
                        left_guilds_with_bl += 1
                    else:
                        current_guild_check_rbl = True

                current_guild_message_authors = {
                    m["id"]: m["user_id"]
                    for m in await old.fetch(
                        "SELECT * FROM messages WHERE is_orig=True AND "
                        "guild_id=$1",
                        current_guild,
                    )
                }

            for id in sbids:
                # check if the user is blacklisted, if so, skip the reaction
                if current_guild_check_rbl:
                    if is_user_blacklisted(
                        current_guild_member_roles.get(
                            int(oldreact["user_id"])
                        ),
                        current_guild_role_bl.get(id),
                        current_guild_role_wl.get(id),
                    ):
                        role_blacklisted += 1
                        continue

                key = (
                    oldreact["message_id"],
                    sb_chid_to_sbid[id],
                    oldreact["user_id"],
                    current_guild_message_authors[oldreact["message_id"]],
                )
                if key in unique:
                    duplicate += 1
                    continue
                unique.add(key)
                args.append((*key, False))
        pb.update(count)
        count = 0
        await do_insert()

    print(f"Role Blacklisted: {role_blacklisted}")
    print(f"Duplicates: {duplicate}")
    print(f"Reactions that belonged to no starboards: {no_starboards}")
    print(f"Left guilds with blacklists: {left_guilds_with_bl}")


async def _migrate_xproles(new: OrmCon, old: ApgCon, bot: GatewayBot) -> None:
    for oldxp in tqdm(await old.fetch("SELECT * FROM xproles"), "XPRoles"):
        await newdb.XPRole(
            role_id=oldxp["id"],
            guild_id=oldxp["guild_id"],
            required=max(5, oldxp["req_xp"]),
        ).create(new)


async def _migrate_posroles(new: OrmCon, old: ApgCon, bot: GatewayBot) -> None:
    for oldpr in tqdm(await old.fetch("SELECT * FROM posroles"), "PosRoles"):
        gid = oldpr["guild_id"]
        mu = oldpr["max_users"]
        if await newdb.PosRole.exists(new, guild_id=gid, max_members=mu):
            mu += 1
        await newdb.PosRole(
            role_id=oldpr["id"], guild_id=gid, max_members=mu
        ).create(con=new)


async def _migrate_channel_bl(
    new: OrmCon, old: ApgCon, bot: GatewayBot
) -> None:
    sb: newdb.Starboard
    for x, sb in enumerate(
        tqdm(
            await newdb.Starboard.fetch_query(new).fetchmany(), "Channel BL/WL"
        )
    ):
        oldbl = await old.fetch(
            "SELECT * FROM channelbl WHERE starboard_id=$1 AND "
            "is_whitelist=False",
            sb.channel_id,
        )
        oldwl = await old.fetch(
            "SELECT * FROM channelbl WHERE starboard_id=$1 AND "
            "is_whitelist=True",
            sb.channel_id,
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


async def _migrate_role_bl(new: OrmCon, old: ApgCon, bot: GatewayBot) -> None:
    role_bl_and_wl = 0

    sb: newdb.Starboard
    for sb in tqdm(
        await newdb.Starboard.fetch_query(new).fetchmany(), "Role BL/WL"
    ):
        role_wl = await old.fetch(
            "SELECT * FROM rolebl WHERE starboard_id=$1 AND is_whitelist=True",
            sb.channel_id,
        )
        role_bl = await old.fetch(
            "SELECT * FROM rolebl WHERE starboard_id=$1 AND "
            "is_whitelist=False",
            sb.channel_id,
        )

        if (not role_wl) and (not role_bl):
            continue

        bl_roles: list[int] = [r["role_id"] for r in role_bl]
        wl_roles: list[int] = [r["role_id"] for r in role_wl]

        if wl_roles and not bl_roles:
            bl_roles.append(sb.guild_id)

        async def create(rid: int, wl: bool) -> None:
            nonlocal role_bl_and_wl
            pr = await newdb.PermRole.exists(new, role_id=rid)
            if not pr:
                pr = await newdb.PermRole(
                    role_id=rid, guild_id=sb.guild_id
                ).create(new)

            if await newdb.PermRoleStarboard.exists(
                new, permrole_id=pr.role_id, starboard_id=sb.id
            ):
                role_bl_and_wl += 1
                return

            await newdb.PermRoleStarboard(
                permrole_id=pr.role_id, starboard_id=sb.id, vote=wl
            ).create(new)

        for role in bl_roles:
            await create(role, False)
        for role in wl_roles:
            await create(role, True)

    print(f"Roles that were blacklisted and whitelisted: {role_bl_and_wl}")
