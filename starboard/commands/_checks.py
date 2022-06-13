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

from typing import Awaitable, Callable

import crescent
import hikari

from starboard.config import CONFIG
from starboard.database import Guild


async def owner_only(ctx: crescent.Context) -> crescent.HookResult | None:
    if ctx.user.id not in CONFIG.owners:
        await ctx.respond("Only owners can use this command.", ephemeral=True)
        return crescent.HookResult(True)

    return None


async def guild_only(ctx: crescent.Context) -> crescent.HookResult | None:
    if not ctx.guild_id:
        await ctx.respond(
            "This command can only be used inside servers.", ephemeral=True
        )
        return crescent.HookResult(True)

    return None


async def premium_guild(ctx: crescent.Context) -> crescent.HookResult | None:
    await guild_only(ctx)
    assert ctx.guild_id is not None

    guild = await Guild.exists(guild_id=ctx.guild_id)
    if not guild or guild.premium_end is None:
        await ctx.respond(
            "This command can only be used in premium servers.", ephemeral=True
        )
        return crescent.HookResult(exit=True)

    return None


def has_guild_perms(
    perms: hikari.Permissions,
) -> Callable[[crescent.Context], Awaitable[crescent.HookResult | None]]:
    async def check(ctx: crescent.Context) -> crescent.HookResult | None:
        await guild_only(ctx)
        assert ctx.guild_id is not None
        assert ctx.member is not None
        assert isinstance(member := ctx.member, hikari.InteractionMember)

        guild = ctx.app.cache.get_guild(ctx.guild_id)
        assert guild is not None

        if perms not in member.permissions:
            await ctx.respond(
                "You don't have permission to use this command.",
                ephemeral=True,
            )
            return crescent.HookResult(True)

        return None

    return check
