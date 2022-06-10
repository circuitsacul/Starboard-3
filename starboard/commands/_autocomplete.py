from __future__ import annotations

from difflib import get_close_matches
from typing import cast

import crescent
import hikari

from starboard.database import AutoStarChannel, Override, Starboard


async def override_autocomplete(
    ctx: crescent.Context, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    if not ctx.guild_id:
        return []
    prefix = cast(str, option.value).lower()
    ovs = await Override.fetch_query().where(guild_id=ctx.guild_id).fetchmany()
    ov_names = [ov.name for ov in ovs]
    return [
        hikari.CommandChoice(name=name, value=name)
        for name in get_close_matches(prefix, ov_names, 10, 0.2)
    ]


async def starboard_autocomplete(
    ctx: crescent.Context, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    if not ctx.guild_id:
        return []
    prefix = cast(str, option.value).lower()
    sbs = (
        await Starboard.fetch_query().where(guild_id=ctx.guild_id).fetchmany()
    )
    sb_names = [sb.name for sb in sbs]
    return [
        hikari.CommandChoice(name=name, value=name)
        for name in get_close_matches(prefix, sb_names, 10, 0.2)
    ]


async def asc_autocomplete(
    ctx: crescent.Context, option: hikari.AutocompleteInteractionOption
) -> list[hikari.CommandChoice]:
    if not ctx.guild_id:
        return []
    prefix = cast(str, option.value).lower()
    ascs = (
        await AutoStarChannel.fetch_query()
        .where(guild_id=ctx.guild_id)
        .fetchmany()
    )
    asc_names = [asc.name for asc in ascs]
    return [
        hikari.CommandChoice(name=name, value=name)
        for name in get_close_matches(prefix, asc_names, 10, 0.2)
    ]
