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

from typing import Awaitable, Callable, Optional

from crescent import Context, HookResult
from crescent.ext.cooldowns import BucketCallbackT
from crescent.ext.cooldowns import cooldown as _cooldown


async def _cooldown_callback(ctx: Context, retry: float) -> None:
    await ctx.respond(
        f"You're using this command too much! Try again in {round(retry)} "
        "second(s).",
        ephemeral=True,
    )


def _user_bucket(ctx: Context) -> int:
    return ctx.user.id


def cooldown(
    capacity: int, period: float, *, bucket: BucketCallbackT = _user_bucket
) -> Callable[[Context], Awaitable[Optional[HookResult]]]:
    call = _cooldown(
        capacity, period, bucket=bucket, callback=_cooldown_callback
    )

    async def wrap(ctx: Context) -> Optional[HookResult]:
        return await call(ctx)

    return wrap
