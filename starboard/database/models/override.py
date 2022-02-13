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

import json
from typing import Any

from apgorm import ForeignKey, Model, Unique, types

from ._validators import array_len
from ._converters import DecimalArrayC, DecimalC
from .guild import Guild
from .starboard import Starboard

from starboard.config import CONFIG


class Override(Model):
    id = types.Serial().field()
    guild_id = types.Numeric().field().with_converter(DecimalC)
    name = types.VarChar(32).field()

    starboard_id = types.Numeric().field().with_converter(DecimalC)

    channel_ids = (
        types.Array(types.Numeric())
        .field(default_factory=list)
        .with_converter(DecimalArrayC)
    )

    _overrides = types.Json().field(default="{}")

    primary_key = (id,)

    name_unique = Unique(guild_id, name)

    guild_fk = ForeignKey(guild_id, Guild.id)
    starboard_fk = ForeignKey(starboard_id, Starboard.id)

    # validators
    channel_ids.add_validator(array_len("channels", CONFIG.max_ov_channels))

    @property
    def overrides(self) -> dict[str, Any]:
        if not hasattr(self, "__loaded_overrides"):
            self.__loaded_overrides = json.loads(self._overrides)
        return self.__loaded_overrides  # type: ignore

    @overrides.setter
    def overrides(self, value: dict[str, Any]) -> None:
        self.__loaded_overrides = value
        self._overrides = json.dumps(value)
