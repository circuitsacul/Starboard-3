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

from contextlib import suppress
from typing import TYPE_CHECKING

from hikari import BadRequestError, ButtonStyle, ForbiddenError

from starboard.config import CONFIG

if TYPE_CHECKING:
    from starboard.bot import Bot


async def _dm_channel(app: Bot, user_id: int) -> int | None:
    if (ch := app.cache.get_dm_channel_id(user_id)) is not None:
        return ch

    try:
        ch = (await app.rest.create_dm_channel(user_id)).id
    except BadRequestError:
        return None
    app.cache.set_dm_channel_id(user_id, ch)
    return ch


async def notify(app: Bot, user_id: int, text: str) -> None:
    row = app.rest.build_message_action_row()
    button = row.add_button(ButtonStyle.SECONDARY, "none.dismiss")
    button.set_label("Dismiss")
    button.add_to_container()

    if CONFIG.dev_notify is not None:
        dest = await _dm_channel(app, CONFIG.dev_notify)
        if not dest:
            print(
                f"Couldn't find user {CONFIG.dev_notify}, skipping "
                "notification."
            )
            return
        await app.rest.create_message(
            dest, f"Notifying <@{user_id}> | `{user_id}`", component=row
        )
    elif CONFIG.development:
        print("Skipping notification (development mode)")
        return
    else:
        dest = await _dm_channel(app, user_id)
        if not dest:
            return

    with suppress(ForbiddenError):
        await app.rest.create_message(dest, text, component=row)
