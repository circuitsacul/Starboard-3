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

from typing import cast, TYPE_CHECKING

import asyncpg
import crescent
import hikari

from starboard.database import PermRole, goc_guild
from starboard.exceptions import StarboardErr
from starboard.core.permrole import get_permroles

from ._checks import has_guild_perms
from ._converters import disid

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("permrole-commands")
permrole = crescent.Group(
    "permroles",
    "Manage permroles",
    [has_guild_perms(hikari.Permissions.MANAGE_ROLES)],
)


@plugin.include
@permrole.child
@crescent.command(name="view", description="View permroles for this server")
async def view_permroles(ctx: crescent.Context) -> None:
    assert ctx.guild
    bot = cast("Bot", ctx.app)

    pr = await get_permroles(ctx.guild)

    if not pr:
        raise StarboardErr("This server has no permroles.")

    embed = bot.embed(title="Permroles")
    for r in pr:
        obj = ctx.guild.get_role(r.permrole.id)
        if obj:
            name = obj.name
        else:
            name = f"Deleted Role {r.permrole.id}"
        embed.add_field(
            name=name,
            inline=True,
            value=(
                f"give-stars: {r.permrole.give_stars}\n"
                f"receive-stars: {r.permrole.recv_stars}\n"
                f"gain-xproles: {r.permrole.xproles}\n"
                f"gain-posroles: {r.permrole.posroles}"
                + (
                    "\n".join(
                        f"\nPermissions for <#{sid}>\n"
                        f"give-stars: {conf.give_stars}\n"
                        f"receive-stars: {conf.recv_stars}\n"
                        for sid, conf in r.starboards.items()
                    )
                )
            )
        )

    await ctx.respond(embed=embed)


@plugin.include
@permrole.child
@crescent.command(name="create", description="Create a permrole")
class CreatePermRole:
    role = crescent.option(hikari.Role, "The role to use as a permrole")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        await goc_guild(ctx.guild_id)
        try:
            await PermRole(id=self.role.id, guild_id=ctx.guild_id).create()
        except asyncpg.UniqueViolationError:
            raise StarboardErr(f"**{self.role}** is already a permrole.")

        await ctx.respond(f"**{self.role}** is now a permrole.")


@plugin.include
@permrole.child
@crescent.command(name="delete", description="Delete a permrole")
class DeletePermRole:
    permrole = crescent.option(
        hikari.Role, "The permrole to delete", default=None
    )
    by_id = crescent.option(
        str, "The ID of the permrole to delete", default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        if not (self.permrole or self.by_id):
            raise StarboardErr("Please specify a permrole to delete.")

        if self.permrole and self.by_id:
            raise StarboardErr(
                "You can only specify either the role or the ID."
            )

        roleid: int
        if self.permrole:
            roleid = self.permrole.id
        else:
            roleid = disid(self.by_id)

        ret = (
            await PermRole.delete_query()
            .where(id=roleid, guild_id=ctx.guild_id)
            .execute()
        )
        if self.by_id:
            name = self.by_id
        else:
            assert self.permrole
            name = self.permrole.name
        if not ret:
            raise StarboardErr(f"**{name}** is not a permrole.")

        await ctx.respond(f"Deleted permrole **{name}**.")
