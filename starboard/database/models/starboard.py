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

from typing import Any, Callable, Iterable

import apgorm
from apgorm import Unique, types
from apgorm.exceptions import InvalidFieldValue

from starboard.config import CONFIG
from starboard.exceptions import StarboardNotFound
from starboard.utils import seconds_to_human

from ._converters import DecimalC, NonNullArray, NullDecimalC
from ._validators import num_range, valid_emoji
from .guild import Guild


def _validate(
    key: str, changes: dict[str, Any], func: Callable[[Any], bool]
) -> None:
    if key in changes:
        ret = func(changes[key])
        if not ret:
            raise RuntimeError("Validation failed.")


def delta_range(name: str, max: int) -> Callable[[int], bool]:
    def validator(value: int) -> bool:
        if value is None:
            return True
        if max is not None and value > max:
            raise InvalidFieldValue(
                f"{name} must be at most {seconds_to_human(max)}."
            )

        return True

    return validator


def validate_sb_changes(**changes: Any) -> None:
    _validate(
        "cooldown_period",
        changes,
        num_range(
            "the cooldown period (seconds)", None, CONFIG.max_cooldown_period
        ),
    )
    _validate("display_emoji", changes, valid_emoji)


class Starboard(apgorm.Model):
    __slots__: Iterable[str] = ()

    id = types.Serial().field()
    name = types.Text().field()
    channel_id = types.Numeric().field().with_converter(DecimalC)
    guild_id = types.Numeric().field().with_converter(DecimalC)

    webhook_id = types.Numeric().nullablefield().with_converter(NullDecimalC)
    prem_locked = types.Boolean().field(default=False)

    # General Style
    display_emoji = types.Text().nullablefield(default="⭐")
    ping_author = types.Boolean().field(default=False)
    use_server_profile = types.Boolean().field(default=True)
    extra_embeds = types.Boolean().field(default=True)
    use_webhook = types.Boolean().field(default=False)

    # Embed Style
    color = types.Int().field(default=CONFIG.color)
    jump_to_message = types.Boolean().field(default=True)
    attachments_list = types.Boolean().field(default=True)
    replied_to = types.Boolean().field(default=True)

    # Requirements
    required = types.SmallInt().field(default=3)
    required_remove = types.SmallInt().field(default=0)
    upvote_emojis = (
        types.Array(types.Text())
        .field(default_factory=lambda: ["⭐"])
        .with_converter(NonNullArray(str))
    )
    downvote_emojis = (
        types.Array(types.Text())
        .field(default_factory=list)
        .with_converter(NonNullArray(str))
    )
    self_vote = types.Boolean().field(default=False)
    allow_bots = types.Boolean().field(default=True)
    require_image = types.Boolean().field(default=False)
    older_than = types.BigInt().field(default=0)
    newer_than = types.BigInt().field(default=0)

    # Behavior
    enabled = types.Boolean().field(default=True)
    autoreact_upvote = types.Boolean().field(default=True)
    autoreact_downvote = types.Boolean().field(default=True)
    remove_invalid = types.Boolean().field(default=True)
    link_deletes = types.Boolean().field(default=False)
    link_edits = types.Boolean().field(default=True)
    private = types.Boolean().field(default=False)
    xp_multiplier = types.Real().field(default=1.0)
    cooldown_enabled = types.Boolean().field(default=False)
    cooldown_count = types.SmallInt().field(default=5)
    cooldown_period = types.SmallInt().field(default=5)

    # ForeignKeys & PrimaryKey
    sb_guild_name_unique = Unique(guild_id, name)

    guild_id_fk = apgorm.ForeignKey(guild_id, Guild.guild_id)

    primary_key = (id,)

    # methods
    @staticmethod
    async def from_name(guild_id: int, name: str) -> Starboard:
        if s := await Starboard.exists(guild_id=guild_id, name=name):
            return s
        else:
            raise StarboardNotFound(name)
