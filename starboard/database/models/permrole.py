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

from ._converters import DecimalC
from .permgroup import PermGroup


class PermRole(apgorm.Model):
    permgroup_id = types.Int().field()
    role_id = types.Numeric().field().with_converter(DecimalC)

    index = types.SmallInt().field()
    allow_commands = types.Boolean().nullablefield()
    on_starboard = types.Boolean().nullablefield()
    give_stars = types.Boolean().nullablefield()
    gain_xp = types.Boolean().nullablefield()
    pos_roles = types.Boolean().nullablefield()
    xp_roles = types.Boolean().nullablefield()

    pgid_fk = apgorm.ForeignKey(permgroup_id, PermGroup.id)

    primary_key = (
        permgroup_id,
        role_id,
    )
