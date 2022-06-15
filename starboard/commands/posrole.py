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

from typing import TYPE_CHECKING, cast

import crescent
import hikari
from apgorm import sql
from asyncpg import UniqueViolationError

from starboard.config import CONFIG
from starboard.core.posrole import update_posroles
from starboard.database import Guild, PosRole, PosRoleMember, XPRole
from starboard.exceptions import StarboardError

from ._checks import has_guild_perms, premium_guild

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin(
    "posrole-commands",
    command_hooks=[
        has_guild_perms(hikari.Permissions.MANAGE_ROLES),
        premium_guild,
    ],
)
posrole = crescent.Group("posroles", "Manage PosRoles")


@plugin.include
@posrole.child
@crescent.command(
    name="refresh", description="Refreshes PosRoles for the server"
)
async def refresh_posroles(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    await ctx.defer(True)
    ret = await update_posroles(cast("Bot", ctx.app), ctx.guild_id)
    if ret:
        msg = "Updated PosRoles."
    else:
        msg = (
            "This server cannot refresh PosRoles right now. Please try again "
            "later."
        )

    await ctx.respond(msg, ephemeral=True)


@plugin.include
@crescent.user_command(name="Refetch PosRoles")
async def refretch_roles(ctx: crescent.Context, user: hikari.User) -> None:
    bot = cast("Bot", ctx.app)
    assert ctx.guild_id

    member = await bot.cache.gof_member(ctx.guild_id, user.id)
    if not member:
        raise StarboardError("I couldn't find that member.")

    prids = {
        p.role_id
        for p in await PosRole.fetch_query()
        .where(guild_id=ctx.guild_id)
        .fetchmany()
    }
    if not prids:
        raise StarboardError("This server has no PosRoles.")

    prmrs = {
        prm.role_id
        for prm in await PosRoleMember.fetch_query()
        .where(user_id=user.id, role_id=sql(prids).any)
        .fetchmany()
    }

    current_proles = set(member.role_ids).intersection(prids)

    for rid in current_proles.difference(prmrs):
        # roles to add
        await PosRoleMember(role_id=rid, user_id=member.id).create()

    # roles to remove
    await PosRoleMember.delete_query().where(
        user_id=member.id, role_id=sql(prmrs.difference(current_proles)).any
    ).execute()

    await ctx.respond(
        "Refetched roles. Use `/posroles refresh` to apply updates.",
        ephemeral=True,
    )


@plugin.include
@posrole.child
@crescent.command(name="create", description="Create a PosRole")
class CreatePosRole:
    role = crescent.option(hikari.Role, "The role to use for a PosRole")
    members = crescent.option(
        int,
        "How many users can have this role",
        min_value=CONFIG.min_pr_members,
        max_value=CONFIG.max_pr_members,
        name="max-members",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await Guild.get_or_create(ctx.guild_id)

        # check if the role can be managed
        if (
            self.role.is_managed
            or self.role.is_premium_subscriber_role
            or self.role.position == 0
        ):
            raise StarboardError("That role cannot be used as an PosRole.")

        # check if exists
        if await PosRole.exists(role_id=self.role.id):
            raise StarboardError(f"**{self.role}** is already a PosRole.")

        # check if it's an XPRole
        if await XPRole.exists(role_id=self.role.id):
            raise StarboardError(
                f"**{self.role}** is an XPRole. A role cannot be a PosRole "
                "and an XPRole."
            )

        # check if they've reached the limit for PosRoles
        if await PosRole.count(guild_id=ctx.guild_id) >= CONFIG.max_posroles:
            raise StarboardError(
                f"You can only have up to {CONFIG.max_posroles} PosRoles."
            )

        # create the posrole
        try:
            await PosRole(
                role_id=self.role.id,
                guild_id=ctx.guild_id,
                max_members=self.members,
            ).create()
        except UniqueViolationError:
            raise StarboardError(
                "There is already a PosRole with max-members set to "
                f"{self.members}."
            ) from None
        await ctx.respond(f"**{self.role}** is now a PosRole.")


@plugin.include
@posrole.child
@crescent.command(
    name="max-members",
    description="Set the maximum members that can have a PosRole",
)
class SetPosRoleMembers:
    posrole = crescent.option(hikari.Role, "The PosRole to modify")
    members = crescent.option(
        int,
        "The maximum members that can have this PosRole",
        min_value=CONFIG.min_pr_members,
        max_value=CONFIG.max_pr_members,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        pr = await PosRole.exists(role_id=self.posrole.id)
        if not pr:
            raise StarboardError(f"**{self.posrole}** is not a PosRole.")

        pr.max_members = self.members
        try:
            await pr.save()
        except UniqueViolationError:
            raise StarboardError(
                "There is already a PosRole with max-members set to "
                f"{self.members}."
            ) from None
        await ctx.respond(
            f"Set the maximum members for **{self.posrole}** to "
            f"{self.members}."
        )


@plugin.include
@posrole.child
@crescent.command(name="delete", description="Deletes a PosRole")
class DeletePosRole:
    posrole = crescent.option(hikari.Role, "The PosRole to delete")

    async def callback(self, ctx: crescent.Context) -> None:
        ret = (
            await PosRole.delete_query()
            .where(role_id=self.posrole.id)
            .execute()
        )
        if not ret:
            raise StarboardError(f"**{self.posrole}** is not a PosRole.")

        await ctx.respond(f"Deleted PosRole **{self.posrole}**.")


@plugin.include
@posrole.child
@crescent.command(name="view", description="View the PosRoles for this server")
async def view_posroles(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    bot = cast("Bot", ctx.app)

    pr = (
        await PosRole.fetch_query()
        .where(guild_id=ctx.guild_id)
        .order_by(PosRole.max_members)
        .fetchmany()
    )
    if not pr:
        raise StarboardError("This server has no PosRoles.")

    embed = bot.embed(
        title="PosRoles",
        description="\n".join(
            f"<@&{r.role_id}>: {r.max_members} members" for r in pr
        ),
    ).set_footer("Note: PosRoles are a premium-only feature")
    await ctx.respond(embed=embed)
