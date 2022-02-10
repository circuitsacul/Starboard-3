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
from typing import TYPE_CHECKING

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


def pretty_sb_config(config: StarboardConfig, bot: Bot) -> _PrettyConfig:
    de = pretty_emoji_str(config.display_emoji, bot=bot)
    wha = (
        f"[view]({config.webhook_avatar})" if config.webhook_avatar else "none"
    )
    appearance = (
        f"color: {config.color}\n"
        f"display-emoji: {de}\n"
        f"ping-author: {config.ping_author}\n"
        f"use-server-profile: {config.use_server_profile}\n"
        f"extra-embeds: {config.extra_embeds}\n"
        f"use-webhook: {config.use_webhook}\n"
        f"webhook-name: {config.webhook_name}\n"
        f"webhook-avatar: {wha}\n"
    )

    se = pretty_emoji_str(*config.star_emojis, bot=bot)
    requirements = (
        f"required: {config.required}\n"
        f"required-remove: {config.required_remove}\n"
        f"star-emojis: {se}\n"
        f"self-star: {config.self_star}\n"
        f"allow-bots: {config.allow_bots}\n"
        f"images-only: {config.images_only}\n"
    )

    behaviour = (
        f"autoreact: {config.autoreact}\n"
        f"remove-invalid: {config.remove_invalid}\n"
        f"link-deletes: {config.link_deletes}\n"
        f"link-edits: {config.link_edits}\n"
        f"disable-xp: {config.disable_xp}\n"
        f"private: {config.private}\n"
        f"enabled: {config.enabled}\n"
    )

    return _PrettyConfig(
        appearance=appearance, behaviour=behaviour, requirements=requirements
    )


def pretty_emoji_str(*emojis: str | None, bot: Bot) -> str:
    converted = [
        stored_to_emoji(e, bot)
        for e in emojis
        if e is not None  # make mypy happy
    ]

    return (
        ", ".join(
            e.mention if isinstance(e, hikari.CustomEmoji) else str(e)
            for e in converted
            if e is not None
        )
        or "none"
    )
