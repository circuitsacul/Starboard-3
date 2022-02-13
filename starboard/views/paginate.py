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

from typing import Sequence

import crescent
import hikari
import miru
from miru.ext.nav import NavButton, NavigatorView  # type: ignore


class Paginator(NavigatorView):
    def __init__(
        self, user_id: int, pages: Sequence[str | hikari.Embed]
    ) -> None:
        self.user_id = user_id
        super().__init__(pages=pages)

    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.user_id

    async def send(
        self, ctx: crescent.Context, ephemeral: bool = False
    ) -> None:
        self.current_page = 0
        self._ephemeral = ephemeral

        for button in self.children:
            if isinstance(button, NavButton):
                await button.before_page_change()

        payload = self._get_page_payload(self.pages[0])
        message = await ctx.respond(
            **payload, ensure_message=True, ephemeral=ephemeral
        )

        self.start(message)
