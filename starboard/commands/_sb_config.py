from __future__ import annotations

import re
from typing import Any

import crescent

from starboard.exceptions import StarboardErr
from starboard.undefined import UNDEF

from ._converters import any_emoji_str, convert, hex_color, none_or
from ._utils import optiond


class BaseEditStarboardStyle:
    def __init_subclass__(cls) -> None:
        for k, v in BaseEditStarboardStyle.__dict__.items():
            if not isinstance(v, crescent.ClassCommandOption):
                continue
            setattr(cls, k, v)

    display_emoji = optiond(
        str, "The emoji next to the point count", name="display-emoji"
    )
    ping_author = optiond(
        bool,
        "Whether to ping users when their post is starboarded",
        name="ping-author",
    )
    use_server_profile = optiond(
        bool,
        "Whether to use nicknames and server avatars",
        name="use-server-profile",
    )
    use_webhook = optiond(
        bool,
        "Whether to use webhooks for starboard messages",
        name="use-webhook",
    )

    def _options(self) -> dict[str, Any]:
        pk = BaseEditStarboardStyle.__dict__.copy().keys()
        params = self.__dict__.copy()

        for k, v in list(params.items()):
            if k not in pk or v is UNDEF.UNDEF:
                del params[k]

        # conversion
        convert("display_emoji", params, none_or(any_emoji_str))

        return params


class BaseEditStarboardEmbedStyle:
    def __init_subclass__(cls) -> None:
        for k, v in BaseEditStarboardEmbedStyle.__dict__.items():
            if not isinstance(v, crescent.ClassCommandOption):
                continue
            setattr(cls, k, v)

    color = optiond(str, "The color of the starboard embeds")
    jump_to_message = optiond(
        bool, "Whether to include the message link", name="jump-to-message"
    )
    attachments_list = optiond(
        bool,
        "Whether to include the list of attachments",
        name="attachments-list",
    )
    replied_to = optiond(
        bool,
        "Whether to include the message that was replied to",
        name="replied-to",
    )

    def _options(self) -> dict[str, Any]:
        pk = BaseEditStarboardEmbedStyle.__dict__.copy().keys()
        params = self.__dict__.copy()

        for k, v in list(params.items()):
            if k not in pk or v is UNDEF.UNDEF:
                del params[k]

        # conversion
        convert("color", params, hex_color)

        return params


class BaseEditStarboardRequirements:
    def __init_subclass__(cls) -> None:
        for k, v in BaseEditStarboardRequirements.__dict__.items():
            if not isinstance(v, crescent.ClassCommandOption):
                continue
            setattr(cls, k, v)

    required = optiond(
        int, "The number of points required for a message to be starboarded"
    )
    required_remove = optiond(
        int,
        "The fewest number of points a message can have before it is removed",
        name="required-remove",
    )
    self_vote = optiond(
        bool,
        "Whether to allow users to vote on their own messages",
        name="self-vote",
    )
    allow_bots = optiond(
        bool,
        "Whether to allow messages from bots to be starboarded",
        name="allow-bots",
    )
    require_image = optiond(
        bool,
        "Whether to require messages to include an image",
        name="require-image",
    )

    def _options(self) -> dict[str, Any]:
        pk = BaseEditStarboardRequirements.__dict__.copy().keys()
        params = self.__dict__.copy()

        for k, v in list(params.items()):
            if k not in pk or v is UNDEF.UNDEF:
                del params[k]

        return params


class BaseEditStarboardBehaviour:
    def __init_subclass__(cls) -> None:
        for k, v in BaseEditStarboardBehaviour.__dict__.items():
            if not isinstance(v, crescent.ClassCommandOption):
                continue
            setattr(cls, k, v)

    autoreact = optiond(
        bool,
        "Whether to automatically react to messages sent to the starboard",
    )
    remove_invalid = optiond(
        bool, "Whether to remove invalid reactions", name="remove-invalid"
    )
    link_deletes = optiond(
        bool,
        "Whether to unstarboard messages if the original was deleted",
        name="link-deletes",
    )
    link_edits = optiond(
        bool,
        "Whether to update the starboard message if the original is edited",
        name="link-edits",
    )
    extra_embeds = optiond(
        bool,
        "Whether to add extra embeds below the main message content",
        name="extra-embeds",
    )
    cooldown_enabled = optiond(
        bool, "Whether to enable the cooldown", name="cooldown-enabled"
    )
    cooldown = optiond(
        str,
        "Set the capacity and period of the cooldown (e.g. 5/6 means 5 votes "
        "per 6 seconds)",
    )
    enabled = optiond(bool, "Whether the starboard is enabled")

    def _options(self) -> dict[str, Any]:
        pk = BaseEditStarboardBehaviour.__dict__.copy().keys()
        params = self.__dict__.copy()

        for k, v in list(params.items()):
            if k not in pk or v is UNDEF.UNDEF:
                del params[k]

        # conversion
        if c := params.pop("cooldown", None):
            count, secs = _parse_cooldown(c)
            params["cooldown_count"] = count
            params["cooldown_period"] = secs

        return params


_RE_C = re.compile(r"(?P<count>\d+).+?(?P<secs>\d+)")


def _parse_cooldown(text: str) -> tuple[int, float]:
    m = _RE_C.match(text)
    if not m:
        raise StarboardErr(
            f"'{text}' is not a valid cooldown. You need to pass both the "
            "capacity and the period. For example, '5 6' means 5 votes per 6 "
            "seconds."
        )
    gd = m.groupdict()
    _c = gd["count"]
    _s = gd["secs"]

    try:
        count = int(_c)
    except ValueError:
        raise StarboardErr(f"{_c} is not a valid integer.")

    try:
        secs = int(_s)
    except ValueError:
        raise StarboardErr(f"{_s} is not a valid integer.")

    return count, secs
