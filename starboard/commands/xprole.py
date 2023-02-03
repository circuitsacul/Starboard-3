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

from starboard.core.xprole import refresh_xpr
from starboard.database import Guild, PosRole, XPRole
from starboard.exceptions import StarboardError

from ._checks import has_guild_perms, premium_guild

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin(
    command_hooks=[
        has_guild_perms(hikari.Permissions.MANAGE_ROLES),
        premium_guild,
    ]
)
xprole = crescent.Group("xproles", "Manage XP roles")


@plugin.include
@crescent.user_command(name="Refresh XProles")
async def refresh_xproles(ctx: crescent.Context, user: hikari.User) -> None:
    bot = cast("Bot", ctx.app)
    assert ctx.guild_id
    await ctx.defer(True)
    ret = await refresh_xpr(bot, ctx.guild_id, user.id)
    if ret:
        await ctx.respond("Refreshed roles.", ephemeral=True)
    else:
        await ctx.respond(
            "You're using this command too much, please try again later.",
            ephemeral=True,
        )


@plugin.include
@xprole.child
@crescent.command(name="create", description="Creates an XPRole")
class AddXPRole:
    role = crescent.option(hikari.Role, "The role to make an XPRole")
    xp = crescent.option(
        int,
        "How much XP is required for a user to gain this XPRole",
        name="required-xp",
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
            raise StarboardError("That role cannot be used as an XPRole.")

        # check if it exists
        if await XPRole.exists(role_id=self.role.id):
            raise StarboardError(f"**{self.role}** is already an XPRole.")

        # check if it's a PosRole
        if await PosRole.exists(role_id=self.role.id):
            raise StarboardError(
                f"**{self.role}** is a Posrole. A role cannot be a PosRole "
                "and an XPRole."
            )

        # create the xprole
        await XPRole(
            role_id=self.role.id, guild_id=ctx.guild_id, required=self.xp
        ).create()
        await ctx.respond(f"**{self.role}** is now an XPRole.")


@plugin.include
@xprole.child
@crescent.command(
    name="required-xp", description="Set the required XP for an XPRole"
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

        xpr = await XPRole.exists(role_id=self.xprole.id)
        if not xpr:
            raise StarboardError(f"**{self.xprole}** is not an XPRole.")

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
        ret = (
            await XPRole.delete_query().where(role_id=self.xprole.id).execute()
        )
        if not ret:
            raise StarboardError(f"**{self.xprole}** is not an XPRole.")

        await ctx.respond(f"Deleted XPRole **{self.xprole}**.")


@plugin.include
@xprole.child
@crescent.command(name="view", description="View the XPRoles for this server")
async def view_xproles(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    bot = cast("Bot", ctx.app)

    xpr = await XPRole.fetch_query().where(guild_id=ctx.guild_id).fetchmany()
    if not xpr:
        raise StarboardError("This server has no XPRoles.")

    embed = bot.embed(
        title="XPRoles",
        description="\n".join(
            f"<@&{r.role_id}>: **{r.required}** XP" for r in xpr
        ),
    ).set_footer("Note: XPRoles are a premium-only feature.")
    await ctx.respond(embed=embed)
