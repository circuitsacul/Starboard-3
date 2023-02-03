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
from starboard.constants import MESSAGE_LEN
from starboard.database import User
from starboard.exceptions import StarboardError
from starboard.utils import trunc_list

from ._checks import owner_only

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin()
owner = crescent.Group("owner", "Owner only commands", hooks=[owner_only])


@plugin.include
@owner.child
@crescent.command(
    name="give-credits",
    description="Gives a user credits",
    guild=CONFIG.main_guild,
)
class GiveCredits:
    user = crescent.option(str, "The id of the user")
    credits = crescent.option(int, "The number of credits to give")

    async def callback(self, ctx: crescent.Context) -> None:
        try:
            uid = int(self.user)
        except ValueError:
            raise StarboardError(f"{self.user} is not a valid id.") from None

        bot = cast("Bot", ctx.app)
        try:
            obj = await bot.rest.fetch_user(uid)
        except hikari.NotFoundError:
            raise StarboardError(f"No user with id {uid} was found.") from None

        u = await User.get_or_create(uid, obj.is_bot)
        u.credits = u.credits + self.credits
        await u.save()
        await ctx.respond(
            f"Gave {obj} {self.credits} credits. They now have {u.credits} "
            "credits.",
            ephemeral=True,
        )


@plugin.include
@owner.child
@crescent.command(
    name="clear-cache",
    description="Clears the cache entirely",
    guild=CONFIG.main_guild,
)
async def clear_cache(ctx: crescent.Context) -> None:
    bot = cast("Bot", ctx.app)
    bot.cache.clear_safe()
    await ctx.respond("Cleared the cache.", ephemeral=True)


@plugin.include
@owner.child
@crescent.command(
    name="eval", description="Evaluate code", guild=CONFIG.main_guild
)
class Eval:
    code = crescent.option(str, "Code to evaluate")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        await ctx.defer(True)

        stdout, obj = await bot.exec_code(
            self.code, {"_bot": bot, "_ctx": ctx}
        )
        await ctx.respond(
            embed=bot.embed(title="Output", description=stdout).add_field(
                name="Return", value=repr(obj)
            )
        )


class Rollback(Exception):
    """Rollback the transaction."""


@plugin.include
@owner.child
@crescent.command(
    name="sql", description="Execute raw SQL", guild=CONFIG.main_guild
)
class RunSQL:
    sql = crescent.option(str, "The SQL to run")
    rollback = crescent.option(
        bool, "Whether to rollback any changes", default=True
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert bot.database.pool
        await ctx.defer(ephemeral=True)
        try:
            async with bot.database.pool.acquire() as con:
                async with con.transaction():
                    ret: list[str] = []
                    async for r in con.cursor(self.sql, []):
                        ret.append(f"\n - {repr(r)}")

                        if len(ret) >= 50:
                            break

                    ret = trunc_list(
                        ret, MESSAGE_LEN - 8, lambda x: f"\n - And {x} others."
                    )
                    result = "```\n" + "".join(ret) + "\n```"
                    if self.rollback:
                        raise Rollback
        except Rollback:
            pass
        except Exception as e:
            result = str(e)

        await ctx.followup(result)
