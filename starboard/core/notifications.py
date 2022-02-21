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

from hikari import ButtonStyle, ForbiddenError, NotFoundError, User

from starboard.config import CONFIG

if TYPE_CHECKING:
    from starboard.bot import Bot


async def notify(user: User, text: str) -> None:
    row = user.app.rest.build_action_row()
    button = row.add_button(ButtonStyle.SECONDARY, "none.dismiss")
    button.set_label("Dismiss")
    button.add_to_container()

    if CONFIG.dev_notify is not None:
        dest = await cast("Bot", user.app).cache.gof_user(CONFIG.dev_notify)
        if not dest:
            print(
                f"Couldn't find user {CONFIG.dev_notify}, skipping "
                "notification."
            )
            return
        await dest.send(f"Notifying <@{user.id}> | `{user.id}`", component=row)
        user = dest
    elif CONFIG.development:
        print("Skipping notification (development mode)")
        return

    try:
        await user.send(text, component=row)
    except (ForbiddenError, NotFoundError):
        pass
