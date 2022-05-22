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

from typing import TYPE_CHECKING, Any, Iterable

from apgorm import raw, sql

from starboard.database import Override

if TYPE_CHECKING:
    from starboard.database import Starboard


class StarboardConfig:
    def __init__(
        self, starboard: Starboard, overrides: Iterable[Override] | None
    ) -> None:
        self.starboard = starboard
        self.overrides = overrides or []

    def __getattr__(self, key: str) -> Any:
        for ov in self.overrides:
            if key in ov.overrides.keys():
                return ov.overrides[key]
        return getattr(self.starboard, key)

    # General Style
    display_emoji: str | None
    ping_author: bool
    use_server_profile: bool
    extra_embeds: bool
    use_webhook: bool

    # Embed Style
    color: int
    jump_to_message: bool
    attachments_list: bool

    # Requirements
    required: int
    required_remove: int
    star_emojis: list[str]
    self_star: bool
    allow_bots: bool
    require_image: bool

    # Behaviour
    enabled: bool
    autoreact: bool
    remove_invalid: bool
    link_deletes: bool
    link_edits: bool
    private: bool
    xp_multiplier: float
    cooldown_enabled: bool
    cooldown_count: int
    cooldown_period: int


async def get_config(sb: Starboard, channel_id: int) -> StarboardConfig:
    ov = await fetch_overrides(sb.id, channel_id)
    return StarboardConfig(sb, ov)


async def fetch_overrides(sb: int, ch: int) -> Iterable[Override]:
    q = Override.fetch_query()
    q.where(starboard_id=sb)
    q.where(
        sql(Override.channel_ids, raw("&& array["), ch, raw("]::numeric[]"))
    )
    return await q.fetchmany()
