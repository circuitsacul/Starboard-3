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

from typing import Callable

import apgorm
from apgorm import types

from ._converters import DecimalArrayC, DecimalC
from .guild import Guild


def limit_length(max_length: int, name: str) -> Callable[[str | None], bool]:
    def check(text: str | None) -> bool:
        if text is not None and len(text) > max_length:
            raise apgorm.exceptions.InvalidFieldValue(
                f"{name} must be no more than {max_length} chars."
            )
        return True

    return check


class Starboard(apgorm.Model):
    channel_id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)

    webhook_url = types.Text().nullablefield()
    locked = types.Boolean().field(default=False)

    # Appearance
    color = types.Int().nullablefield()
    display_emoji = types.Text().nullablefield()
    ping_author = types.Boolean().field(default=False)
    use_nicknames = types.Boolean().field(default=False)
    use_webhook = types.Boolean().field(default=False)

    webhook_name = types.Text().nullablefield()
    webhook_name.add_validator(limit_length(32, "Webhook name"))

    webhook_avatar = types.Text().nullablefield()
    webhook_avatar.add_validator(limit_length(512, "Webhook avatar"))

    # Requirements
    required = types.SmallInt().field(default=3)
    required_remove = types.SmallInt().field(default=0)
    star_emojis = types.Array(types.Text()).field()
    self_star = types.Boolean().field(default=False)
    allow_bots = types.Boolean().field(default=True)
    images_only = types.Boolean().field(default=False)

    regex = types.Text().field(default="")
    exclude_regex = types.Text().field(default="")

    channel_bl = (
        types.Array(types.Numeric())
        .field(default=[])
        .with_converter(DecimalArrayC)
    )
    channel_wl = (
        types.Array(types.Numeric())
        .field(default=[])
        .with_converter(DecimalArrayC)
    )

    # Behaviour
    autoreact = types.Boolean().field(default=True)
    remove_invalid = types.Boolean().field(default=True)
    link_deletes = types.Boolean().field(default=False)
    link_edits = types.Boolean().field(default=True)
    disable_xp = types.Boolean().field(default=False)
    allow_explore = types.Boolean().field(default=True)

    # ForeignKeys & PrimaryKey
    guild_id_fk = apgorm.ForeignKey(guild_id, Guild.guild_id)

    primary_key = (channel_id,)
