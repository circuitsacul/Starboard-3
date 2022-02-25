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

from typing import Any, TypeVar

from apgorm import Model, join, raw, sql

_T = TypeVar("_T", bound=Model)


async def goc(
    model: type[_T], get_fields: dict[str, Any], create_fields: dict[str, Any]
) -> _T:
    ins = sql(
        raw(f"INSERT INTO {model.tablename}"),
        join(raw(","), *(raw(n) for n in create_fields.keys()), wrap=True),
        raw("VALUES"),
        join(raw(","), *create_fields.values(), wrap=True),
        raw("ON CONFLICT"),
        join(raw(","), *(raw(n) for n in get_fields.keys()), wrap=True),
        raw("DO NOTHING RETURNING *"),
    )
    sel = sql(
        raw(f"SELECT * FROM {model.tablename} WHERE"),
        join(
            raw("AND"),
            *(sql(raw(k), raw("="), v) for k, v in get_fields.items()),
        ),
    )
    final = sql(
        raw("WITH ins AS"),
        sql(ins, wrap=True),
        raw(", sel AS"),
        sql(sel, wrap=True),
        raw("\nSELECT * FROM ins UNION SELECT * FROM sel"),
    )
    dct = await model.database.fetchrow(*final.render())
    assert dct
    return model._from_raw(**dct)
