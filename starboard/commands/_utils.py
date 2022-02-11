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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

import hikari

from starboard.core.config import StarboardConfig
from starboard.core.emojis import stored_to_emoji

if TYPE_CHECKING:
    from starboard.bot import Bot


@dataclass
class _PrettyConfig:
    appearance: str
    behaviour: str
    requirements: str


def pretty_sb_config(
    config: StarboardConfig, bot: Bot, bold: Iterable[str] | None = None
) -> _PrettyConfig:
    b: set[str] = set(b.replace("_", "-") for b in bold) if bold else set()

    de = pretty_emoji_str(config.display_emoji, bot=bot)
    wha = (
        f"[view]({config.webhook_avatar})" if config.webhook_avatar else "none"
    )
    appearance = {
        "color": config.color,
        "display-emoji": de,
        "ping-author": config.ping_author,
        "use-server-profile": config.use_server_profile,
        "extra-embeds": config.extra_embeds,
        "use-webhook": config.use_webhook,
        "webhook-name": config.webhook_name,
        "webhook-avatar": wha,
    }

    se = pretty_emoji_str(*config.star_emojis, bot=bot)
    requirements = {
        "required": config.required,
        "required-remove": config.required_remove,
        "star-emojis": se,
        "self-star": config.self_star,
        "allow-bots": config.allow_bots,
        "images-only": config.images_only,
    }

    stars = config.cooldown_count
    secs = config.cooldown_period
    behaviour = {
        "autoreact": config.autoreact,
        "remove-invalid": config.remove_invalid,
        "link-deletes": config.link_deletes,
        "link-edits": config.link_edits,
        "disable-xp": config.disable_xp,
        "private": config.private,
        "enabled": config.enabled,
        "cooldown-enabled": config.cooldown_enabled,
        "cooldown": f"{stars} stars per {secs} seconds"
    }

    if "cooldown-seconds" in b or "cooldown-stars" in b:
        b.add("cooldown")

    def gen(dct: dict[str, Any]) -> str:
        return "\n".join(
            (f"{k}: {str(v)}" if k not in b else f"**{k}**: {str(v)}")
            for k, v in dct.items()
        )

    return _PrettyConfig(
        appearance=gen(appearance),
        behaviour=gen(behaviour),
        requirements=gen(requirements),
    )


def pretty_emoji_str(*emojis: str | None, bot: Bot) -> str:
    converted = [
        stored_to_emoji(e, bot)
        for e in emojis
        if e is not None
    ]

    return (
        ", ".join(
            e.mention if isinstance(e, hikari.CustomEmoji) else str(e)
            for e in converted
            if e is not None
        )
        or "none"
    )
