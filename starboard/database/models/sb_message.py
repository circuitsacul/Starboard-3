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

from typing import Iterable

import apgorm
from apgorm import types

from ._converters import DecimalC, NullDecimalC
from .message import Message
from .starboard import Starboard


class SBMessage(apgorm.Model):
    __slots__: Iterable[str] = ()

    message_id = types.Numeric().field().with_converter(DecimalC)
    starboard_id = types.Numeric().field().with_converter(DecimalC)
    sb_message_id = (
        types.Numeric().nullablefield().with_converter(NullDecimalC)
    )

    last_known_point_count = types.SmallInt().field(default=0)

    message_id_fk = apgorm.ForeignKey(message_id, Message.id)
    starboard_id_fk = apgorm.ForeignKey(starboard_id, Starboard.id)

    primary_key = (message_id, starboard_id)
