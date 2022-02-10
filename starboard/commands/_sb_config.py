from __future__ import annotations

from typing import Any, TypeVar

import crescent

from starboard.undefined import UNDEF

from ._converters import any_emoji_str, convert, hex_color, none_or

_T = TypeVar("_T")


def optiond(type: type[_T], *args, **kwargs) -> _T | UNDEF:
    return crescent.option(
        type, *args, **kwargs, default=UNDEF.UNDEF  # type: ignore
    )


class EditStarboardConfig:
    def __init_subclass__(cls) -> None:
        for k, v in EditStarboardConfig.__dict__.items():
            if not isinstance(v, crescent.ClassCommandOption):
                continue
            setattr(cls, k, v)

    color = optiond(str, "The color of the starboard embeds")
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
    webhook_name = optiond(
        str, "The name for webhooks, if enabled", name="webhook-name"
    )
    webhook_avatar = optiond(
        str, "The avatar for webhooks, if enabled", name="webhook-avatar"
    )
    required = optiond(
        int, "The number of reactions required for a message to be starboarded"
    )
    required_remove = optiond(
        int,
        "The fewest number of stars a message can have before it is removed",
        name="required-remove",
    )
    self_star = optiond(
        bool,
        "Whether to allow users to star their own messages",
        name="self-star",
    )
    allow_bots = optiond(
        bool,
        "Whether to allow messages from bots to be starboarded",
        name="allow-bots",
    )
    images_only = optiond(
        bool,
        "Whether to require messages to include an image",
        name="images-only",
    )
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
    disable_xp = optiond(
        bool, "Whether to disable XP for a starboard", name="disable-xp"
    )
    private = optiond(
        bool,
        "Whether to prevent `random` and `moststarred` from using this "
        "starboard",
    )
    extra_embeds = optiond(
        bool,
        "Whether to add extra embeds below the main message content",
        name="extra-embeds",
    )
    enabled = optiond(bool, "Whether the starboard is enabled")

    def _options(self) -> dict[str, Any]:
        pk = EditStarboardConfig.__dict__.copy().keys()
        params = self.__dict__.copy()

        for k, v in list(params.items()):
            if k not in pk or v is UNDEF.UNDEF:
                del params[k]

        # conversion
        convert("color", params, hex_color)
        convert("display_emoji", params, none_or(any_emoji_str))

        return params
