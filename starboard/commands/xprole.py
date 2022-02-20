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

from starboard.config import CONFIG
from starboard.database import XPRole, PosRole, goc_guild
from starboard.exceptions import StarboardErr

from ._checks import has_guild_perms

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin("xprole-commands")
xprole = crescent.Group(
    "xproles",
    "Manage XP roles",
    [has_guild_perms(hikari.Permissions.MANAGE_ROLES)],
)


@plugin.include
@xprole.child
@crescent.command(name="stack", description="Manage XPRole stacking")
class StackXPRoles:
    stack = crescent.option(bool, "Whether to stack XPRoles", default=None)

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        guild = await goc_guild(ctx.guild_id)

        if self.stack is not None:
            guild.stack_xproles = self.stack
            await guild.save()
            if self.stack:
                msg = "Enabled XPRole stacking."
            else:
                msg = "Disabled XPRole stacking."
            await ctx.respond(msg)
        else:
            await ctx.respond(
                f"XPRole stacking is currently set to {guild.stack_xproles}."
            )


@plugin.include
@xprole.child
@crescent.command(name="create", description="Creates an XPRole")
class AddXPRole:
    role = crescent.option(hikari.Role, "The role to make an XPRole")
    xp = crescent.option(
        int,
        "How much XP is required for a user to gain this XPRole",
        min_value=CONFIG.min_xpr_xp,
        max_value=CONFIG.max_xpr_xp,
        name="required-xp",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        await goc_guild(ctx.guild_id)

        # check if the role can be managed
        if (
            self.role.is_managed
            or self.role.is_premium_subscriber_role
            or self.role.position == 0
        ):
            raise StarboardErr("That role cannot be used as an XPRole.")

        # check if it exists
        if await XPRole.exists(id=self.role.id):
            raise StarboardErr(f"**{self.role}** is already an XPRole.")

        # check if it's a PosRole
        if await PosRole.exists(id=self.role.id):
            raise StarboardErr(
                f"**{self.role}** is a Posrole. A role cannot be a PosRole "
                "and an XPRole."
            )

        # check if they've reached the limit for XPRoles
        if await XPRole.count(guild_id=ctx.guild_id) >= CONFIG.max_xp_roles:
            raise StarboardErr(
                f"You can only have up to {CONFIG.max_xp_roles} XPRoles."
            )

        # create the xprole
        await XPRole(
            id=self.role.id, guild_id=ctx.guild_id, required=self.xp
        ).create()
        await ctx.respond(f"**{self.role}** is now an XPRole.")


@plugin.include
@xprole.child
@crescent.command(
    name="set-xp", description="Sets the required XP for an XPRole"
)
class SetXPRoleXP:
    xprole = crescent.option(hikari.Role, "The XPRole to set XP for")
    xp = crescent.option(
        int,
        "The required XP for a user to get this XPRole",
        name="required-xp",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        xpr = await XPRole.exists(id=self.xprole.id)
        if not xpr:
            raise StarboardErr(f"**{self.xprole}** is not an XPRole.")

        xpr.required = self.xp
        await xpr.save()
        await ctx.respond(
            f"Set the required XP for **{self.xprole}** to {self.xp}."
        )


@plugin.include
@xprole.child
@crescent.command(name="delete", description="Deletes an XPRole")
class DeleteXPRole:
    xprole = crescent.option(hikari.Role, "The XPRole to delete")

    async def callback(self, ctx: crescent.Context) -> None:
        ret = await XPRole.delete_query().where(id=self.xprole.id).execute()
        if not ret:
            raise StarboardErr(f"**{self.xprole}** is not an XPRole.")

        await ctx.respond(f"Deleted XPRole **{self.xprole}**.")


@plugin.include
@xprole.child
@crescent.command(name="view", description="Views your XPRoles")
async def view_xproles(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    bot = cast("Bot", ctx.app)

    xpr = await XPRole.fetch_query().where(guild_id=ctx.guild_id).fetchmany()
    if not xpr:
        raise StarboardErr("This server has no XPRoles.")

    embed = bot.embed(
        title="XPRoles",
        description="\n".join(f"<@&{r.id}>: **{r.required}** XP" for r in xpr),
    ).set_footer("Note: XPRoles are a premium-only feature.")
    await ctx.respond(embed=embed)
