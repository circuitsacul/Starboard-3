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

from starboard.config import CONFIG

from ._converters import DecimalC, NullDecimalC, NonNullArray
from .guild import Guild


class Starboard(apgorm.Model):
    id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)

    webhook_id = types.Numeric().nullablefield().with_converter(NullDecimalC)

    # Appearance
    color = types.Int().field(default=CONFIG.color)
    display_emoji = types.Text().nullablefield(default="⭐")
    ping_author = types.Boolean().field(default=False)
    use_server_profile = types.Boolean().field(default=True)
    extra_embeds = types.Boolean().field(default=True)
    use_webhook = types.Boolean().field(default=False)
    webhook_name = types.Text().field(default="Starboard")
    webhook_avatar = types.Text().nullablefield()

    # Requirements
    required = types.SmallInt().field(default=3)
    required_remove = types.SmallInt().field(default=0)
    star_emojis = types.Array(types.Text()).field(
        default_factory=lambda: list(["⭐"])
    ).with_converter(NonNullArray[str])
    self_star = types.Boolean().field(default=False)
    allow_bots = types.Boolean().field(default=True)
    images_only = types.Boolean().field(default=False)

    # Behaviour
    enabled = types.Boolean().field(default=True)
    autoreact = types.Boolean().field(default=True)
    remove_invalid = types.Boolean().field(default=True)
    link_deletes = types.Boolean().field(default=False)
    link_edits = types.Boolean().field(default=True)
    disable_xp = types.Boolean().field(default=False)
    private = types.Boolean().field(default=False)

    # ForeignKeys & PrimaryKey
    guild_id_fk = apgorm.ForeignKey(guild_id, Guild.id)

    primary_key = (id,)
