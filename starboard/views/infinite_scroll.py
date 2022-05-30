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

import asyncio
from typing import TYPE_CHECKING, Awaitable, Callable, List, Tuple, cast

import hikari
import miru

if TYPE_CHECKING:
    from starboard.bot import Bot

PAGE = Tuple[List[hikari.Embed], str]


class InfiniteScroll(miru.View):
    def __init__(
        self, user_id: int, next_page: Callable[[], Awaitable[PAGE]]
    ) -> None:
        self.user_id = user_id
        self.next_page = next_page
        self.index = 0
        self.cached_pages: list[PAGE] = []
        super().__init__()

    async def wait(self) -> None:
        bot = cast("Bot", self.app)
        assert bot.cluster.stop_future
        await asyncio.wait(
            (
                asyncio.create_task(super().wait()),
                asyncio.create_task(bot.cluster.join()),
            ),
            return_when=asyncio.FIRST_COMPLETED,
        )

    async def get_page(self, index: int) -> PAGE | None:
        if index < 0:
            return None

        self.index = index
        while self.index > (len(self.cached_pages) - 1):
            try:
                self.cached_pages.append(await self.next_page())
            except Exception:
                self.index = len(self.cached_pages) - 1
                return None
        return self.cached_pages[self.index]

    async def finish(self) -> None:
        for item in self.children:
            item.disabled = True

        assert self.message
        await self.message.edit(components=self.build())

    async def on_timeout(self) -> None:
        await self.finish()
        return await super().on_timeout()

    async def set_page(self, page: PAGE, ctx: miru.Context) -> None:
        embeds, content = page

        await ctx.edit_response(
            content=content, embeds=embeds, components=self.build()
        )

    async def view_check(self, context: miru.Context) -> bool:
        return self.user_id == context.user.id

    @miru.button(label="<<", custom_id="infinite-scroll:first")
    async def first(self, btn: miru.Button, ctx: miru.Context) -> None:
        page = await self.get_page(0)
        if page:
            await self.set_page(page, ctx)

    @miru.button(label="<", custom_id="infinite-scroll:prev")
    async def prev(self, btn: miru.Button, ctx: miru.Context) -> None:
        page = await self.get_page(self.index - 1)
        if page:
            await self.set_page(page, ctx)

    @miru.button(label=">", custom_id="infinite-scroll:next")
    async def next(self, btn: miru.Button, ctx: miru.Context) -> None:
        page = await self.get_page(self.index + 1)
        if page:
            await self.set_page(page, ctx)

    @miru.button(label=">>", custom_id="infinite-scroll:last")
    async def last(self, btn: miru.Button, ctx: miru.Context) -> None:
        page = await self.get_page(len(self.cached_pages) - 1)
        if page:
            await self.set_page(page, ctx)
