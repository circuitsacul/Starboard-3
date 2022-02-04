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

from typing import TYPE_CHECKING, Any, Awaitable, Callable, cast

import crescent
import hikari

from starboard.exceptions import CheckErr

if TYPE_CHECKING:
    from starboard.bot import Bot


async def owner_only(
    ctx: crescent.Context, options
) -> None:
    bot = cast("Bot", ctx.app)
    if ctx.user.id not in bot.config.owners:
        raise CheckErr("Only owners can use this command.")

    return None


async def guild_only(
    ctx: crescent.Context, options
) -> None:
    if not ctx.guild_id:
        raise CheckErr("This command can only be used inside servers.")

    return None


def has_guild_perms(
    perms: hikari.Permissions,
) -> Callable[
    [crescent.Context, Any], Awaitable[None]
]:
    async def check(
        ctx: crescent.Context, options
    ) -> None:
        await guild_only(ctx, options)
        assert ctx.guild_id is not None
        assert ctx.member is not None
        assert isinstance(member := ctx.member, hikari.InteractionMember)

        guild = ctx.app.cache.get_guild(ctx.guild_id)
        assert guild is not None

        if perms not in member.permissions:
            raise CheckErr("You don't have permission to use this command.")

        return None

    return check
