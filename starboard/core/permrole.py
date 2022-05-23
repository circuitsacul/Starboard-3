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

from dataclasses import dataclass
from typing import Iterable

import hikari

from starboard.database import PermRole, PermRoleStarboard


@dataclass
class Permissions:
    vote: bool = True
    recv_votes: bool = True
    xproles: bool = True


class PermRoleConfig:
    def __init__(
        self, permrole: PermRole, starboard_perms: Iterable[PermRoleStarboard]
    ) -> None:
        self.permrole = permrole
        self.starboards: dict[int, PermRoleStarboard] = {
            sr.starboard_id: sr for sr in starboard_perms
        }


async def get_permroles(guild: hikari.Guild) -> list[PermRoleConfig]:
    configs: list[PermRoleConfig] = []
    pr = await PermRole.fetch_query().where(guild_id=guild.id).fetchmany()
    pr_ids: set[int] = set()
    for r in pr:
        pr_ids.add(r.id)
        sr = (
            await PermRoleStarboard.fetch_query()
            .where(permrole_id=r.id)
            .fetchmany()
        )
        configs.append(PermRoleConfig(r, sr))

    role_indices: dict[int, int] = {
        r.id: r.position for r in guild.get_roles().values() if r.id in pr_ids
    }
    configs.sort(key=lambda c: role_indices.get(c.permrole.id, -1))
    return configs


async def get_permissions(
    guild: hikari.Guild,
    role_ids: set[int] | None = None,
    starboard_id: int | None = None,
) -> Permissions:
    role_ids = role_ids or set()

    permroles = await get_permroles(guild)
    perms = Permissions()

    for role in permroles:
        if role.permrole.id not in role_ids:
            continue

        if role.permrole.vote is not None:
            perms.vote = role.permrole.vote
        if role.permrole.recv_votes is not None:
            perms.recv_votes = role.permrole.recv_votes
        if role.permrole.xproles is not None:
            perms.xproles = role.permrole.xproles

        if starboard_id in role.starboards and starboard_id is not None:
            sbperms = role.starboards[starboard_id]
            if sbperms.vote is not None:
                perms.vote = sbperms.vote
            if sbperms.recv_votes is not None:
                perms.recv_votes = sbperms.recv_votes

    return perms
