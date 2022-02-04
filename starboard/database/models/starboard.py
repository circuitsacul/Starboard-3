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

import apgorm
from apgorm import types

from ._converters import DecimalArrayC, DecimalC, NullDecimalC
from ._checks import str_length, int_range, valid_emoji
from .guild import Guild

from starboard.config import CONFIG


class Starboard(apgorm.Model):
    id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)

    webhook_id = types.Numeric().nullablefield().with_converter(NullDecimalC)
    locked = types.Boolean().field(default=False)

    # Appearance
    color = types.Int().nullablefield()
    display_emoji = types.Text().nullablefield()
    ping_author = types.Boolean().field(default=False)
    use_nicknames = types.Boolean().field(default=False)
    use_webhook = types.Boolean().field(default=False)
    webhook_name = types.Text().field(default="Starboard")
    webhook_avatar = types.Text().nullablefield()

    # Requirements
    required = types.SmallInt().field(default=3)
    required_remove = types.SmallInt().field(default=0)
    star_emojis = types.Array(types.Text()).field(default_factory=list)
    self_star = types.Boolean().field(default=False)
    allow_bots = types.Boolean().field(default=True)
    images_only = types.Boolean().field(default=False)

    regex = types.Text().nullablefield()
    exclude_regex = types.Text().nullablefield()

    channel_bl = (
        types.Array(types.Numeric())
        .field(default_factory=list)
        .with_converter(DecimalArrayC)
    )
    channel_wl = (
        types.Array(types.Numeric())
        .field(default_factory=list)
        .with_converter(DecimalArrayC)
    )

    # Behaviour
    autoreact = types.Boolean().field(default=True)
    remove_invalid = types.Boolean().field(default=True)
    link_deletes = types.Boolean().field(default=False)
    link_edits = types.Boolean().field(default=True)
    disable_xp = types.Boolean().field(default=False)
    allow_explore = types.Boolean().field(default=True)

    # validators
    webhook_name.add_validator(str_length("webhook_name", CONFIG.max_whn_len))
    webhook_avatar.add_validator(
        str_length("webhook_avatar", CONFIG.max_wha_len)
    )
    required.add_validator(
        int_range("required", CONFIG.max_required, CONFIG.min_required)
    )
    required_remove.add_validator(
        int_range(
            "required_remove",
            CONFIG.max_required_remove,
            CONFIG.min_required_remove,
        )
    )
    display_emoji.add_validator(valid_emoji)

    # ForeignKeys & PrimaryKey
    guild_id_fk = apgorm.ForeignKey(guild_id, Guild.id)

    primary_key = (id,)
