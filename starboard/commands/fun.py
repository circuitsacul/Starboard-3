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

import datetime
from typing import TYPE_CHECKING, Any, Iterator, cast

import crescent
import hikari
from apgorm import LazyList
from apgorm import raw as r

from starboard.config import CONFIG
from starboard.cooldowns import cooldown
from starboard.core.config import get_config
from starboard.core.embed_message import embed_message
from starboard.core.emojis import stored_to_emoji
from starboard.core.leaderboard import get_leaderboard, refresh_xp
from starboard.database import Guild, Member, Message, SBMessage, Starboard
from starboard.exceptions import StarboardError
from starboard.utils import human_to_seconds, parse_date
from starboard.views import InfiniteScroll, Paginator

from ._autocomplete import starboard_autocomplete
from ._checks import guild_only

if TYPE_CHECKING:
    from starboard.bot import Bot


plugin = crescent.Plugin()


@plugin.include
@crescent.hook(guild_only)
@crescent.command(name="refresh-xp", description="Refresh your XP")
async def refresh_my_xp(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    ret = await refresh_xp(ctx.guild_id, ctx.user.id)
    if ret:
        await ctx.respond("Your XP has been refreshed.", ephemeral=True)
    elif ret is None:
        await ctx.respond("You don't have any XP.", ephemeral=True)
    else:
        await ctx.respond(
            "You can't refresh your XP right now. Please try again later.",
            ephemeral=True,
        )


def _build_leaderboard(
    entries: Iterator[tuple[int, int | float]]
) -> list[str]:
    pages: list[str] = []
    current_page = ""
    for x, entry in enumerate(entries):
        if x % 10 == 0 and x != 0:
            pages.append(current_page)
            current_page = ""

        current_page += (
            f"#{str(x+1).zfill(3)}: <@{entry[0]}> with {entry[1]} XP\n"
        )

    if current_page:
        pages.append(current_page)

    return pages


@plugin.include
@crescent.hook(guild_only)
@crescent.command(
    name="leaderboard", description="Shows the server's leaderboard"
)
async def leaderboard(ctx: crescent.Context) -> None:
    assert ctx.guild_id
    bot = cast("Bot", ctx.app)

    embeds: list[hikari.Embed] = [
        bot.embed(title="Leaderboard", description=page)
        for page in _build_leaderboard(
            (u, s.xp) for u, s in (await get_leaderboard(ctx.guild_id)).items()
        )
    ]
    if not embeds:
        raise StarboardError("There is no one on the leaderboard.")

    nav = Paginator(ctx.user.id, embeds)
    await nav.send(ctx.interaction)


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(cooldown(2, 10))
@crescent.command(
    name="custom-leaderboard", description="Create a custom leaderboard"
)
class CustomLeaderboard:
    starboard_name = crescent.option(
        str,
        "The starboard to build the leaderboard for",
        autocomplete=starboard_autocomplete,
    )
    limit = crescent.option(
        int,
        "How many people to show on the leaderboard",
        min_value=5,
        max_value=100,
        default=10,
    )
    newer_than = crescent.option(
        str,
        "How new the votes must be (e.x 10 seconds)",
        default=None,
        name="newer-than",
    )
    older_than = crescent.option(
        str,
        "How old the votes must be (e.x 10 seconds)",
        default=None,
        name="older-than",
    )
    created_after = crescent.option(
        str,
        "A date that the votes must have been created after (dd-mm-yyyy)",
        default=None,
        name="created-after",
    )
    created_before = crescent.option(
        str,
        "A date that the votes must have been created before (dd-mm-yyyy)",
        default=None,
        name="created-before",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id

        newer_than = (
            hikari.Snowflake.from_datetime(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(
                        seconds=human_to_seconds(self.newer_than)
                    )
                )
            )
            if self.newer_than
            else None
        )
        older_than = (
            hikari.Snowflake.from_datetime(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(
                        seconds=human_to_seconds(self.older_than)
                    )
                )
            )
            if self.older_than
            else None
        )
        created_after = (
            hikari.Snowflake.from_datetime(parse_date(self.created_after))
            if self.created_after
            else None
        )
        created_before = (
            hikari.Snowflake.from_datetime(parse_date(self.created_before))
            if self.created_before
            else None
        )

        if created_after and newer_than:
            raise StarboardError(
                "You can only specify created-after *or* newer-than."
            )
        if created_before and older_than:
            raise StarboardError(
                "You can only specify created-before *or* older-than."
            )

        starboard = await Starboard.from_name(
            ctx.guild_id, self.starboard_name
        )

        query = """
        SELECT
            COUNT(*) FILTER (WHERE is_downvote=false)
                - COUNT(*) FILTER (WHERE is_downvote=true)
                AS stars,
            target_author_id
        FROM votes
            WHERE starboard_id=$1
            AND ($3::numeric IS NULL OR message_id > $3) -- newer than
            AND ($4::numeric IS NULL OR message_id < $4) -- older than
        GROUP BY target_author_id
        ORDER BY
            COUNT(*) FILTER (WHERE is_downvote=false)
                - COUNT(*) FILTER (WHERE is_downvote=true)
            DESC
        LIMIT $2
        """

        result: LazyList[Any, dict[str, Any]] = await bot.database.fetchmany(
            query,
            [
                starboard.id,
                self.limit,
                created_after or newer_than,
                created_before or older_than,
            ],
        )
        embeds: list[hikari.Embed] = [
            bot.embed(
                title=f"Custom Leaderboard for '{starboard.name}'",
                description=page,
            )
            for page in _build_leaderboard(
                (
                    entry["target_author_id"],
                    entry["stars"] * starboard.xp_multiplier,
                )
                for entry in list(result)
            )
        ]
        if not embeds:
            raise StarboardError("There is nothing to display!")
        nav = Paginator(ctx.user.id, embeds)
        await nav.send(ctx.interaction)


@plugin.include
@crescent.hook(guild_only)
@crescent.command(name="rank", description="Show a users rank")
class Rank:
    user = crescent.option(
        hikari.User, "The user to show the rank for", default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        user = self.user or ctx.user
        is_self = user.id == ctx.user.id

        lb = await get_leaderboard(ctx.guild_id)
        stats = lb.get(user.id)

        xp: float
        rank: int | None
        if stats:
            xp = stats.xp
            rank = stats.rank
        else:
            rank = None
            m = await Member.exists(user_id=user.id, guild_id=ctx.guild_id)
            xp = m.xp if m else 0

        if is_self:
            await ctx.respond(
                f"You have **{xp}** XP"
                + (
                    f", and you're **#{rank}** on the leaderboard."
                    if rank
                    else "."
                )
            )
        else:
            await ctx.respond(
                f"{user} has **{xp}** XP"
                + (
                    f", and is **#{rank}** on the leaderboard."
                    if rank
                    else "."
                )
            )


@plugin.include
@crescent.hook(cooldown(*CONFIG.random_cooldown))
@crescent.hook(guild_only)
@crescent.command(
    name="random", description="A random message from the starboards"
)
class Random:
    starboard = crescent.option(
        str,
        "The starboard to get a random message from",
        autocomplete=starboard_autocomplete,
    )
    channel = crescent.option(
        hikari.TextableGuildChannel,
        "Only show messages sent in this channel",
        default=None,
    )
    min_points = crescent.option(
        int,
        "Only show messages with at least this many points",
        default=None,
        min_value=1,
        name="min-points",
    )
    max_points = crescent.option(
        int,
        "Only show messages with at most this many points",
        default=None,
        min_value=1,
        name="max-points",
    )
    allow_nsfw = crescent.option(
        bool,
        "Whether to allow messages from NSFW channels",
        default=False,
        name="allow-nsfw",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        bot = cast("Bot", ctx.app)

        channel_is_nsfw = await bot.cache.gof_guild_channel_nsfw(
            ctx.channel_id
        )
        if self.allow_nsfw and not channel_is_nsfw:
            await ctx.respond(
                "To show NSFW messages, run this command in an NSFW channel.",
                ephemeral=True,
            )
            return

        s = await Starboard.from_name(ctx.guild_id, self.starboard)
        if s.private:
            raise StarboardError(f"{s.name} is a private starboard.")

        q = SBMessage.fetch_query()
        q.where(starboard_id=s.id)
        q.where(SBMessage.sb_message_id.is_null.not_)

        sbq = Message.fetch_query()
        sbq.where(message_id=SBMessage.message_id)
        sbq.where(trashed=False)
        if not self.allow_nsfw:
            sbq.where(is_nsfw=False)
        if self.channel:
            sbq.where(channel_id=self.channel.id)

        q.where(sbq.exists())

        if self.min_points:
            q.where(SBMessage.last_known_point_count.gteq(self.min_points))
        if self.max_points:
            q.where(SBMessage.last_known_point_count.lteq(self.max_points))

        q.order_by(r("random()"))

        ret = await q.fetchone()

        if not ret:
            raise StarboardError("Nothing to show.")

        orig = await Message.fetch(message_id=ret.message_id)
        obj = await bot.cache.gof_message(orig.channel_id, orig.message_id)
        if not obj:
            raise StarboardError("Something went wrong.")

        config = await get_config(bot, s, obj.channel_id)

        guild = await Guild.fetch(guild_id=ctx.guild_id)

        raw, e, es = await embed_message(
            bot,
            obj,
            ctx.guild_id,
            config.color,
            stored_to_emoji(config.display_emoji, bot)
            if config.display_emoji
            else None,
            config.use_server_profile,
            config.ping_author,
            ret.last_known_point_count,
            orig.frozen,
            s.id in orig.forced_to,
            guild.premium_end is not None,
            config.attachments_list,
            config.jump_to_message,
            config.replied_to,
        )

        await ctx.respond(content=raw, embeds=[e, *es])


@plugin.include
@crescent.hook(cooldown(*CONFIG.moststarred_cooldown))
@crescent.hook(guild_only)
@crescent.command(
    name="moststarred", description="Shows the most starred messages"
)
class MostStarred:
    starboard = crescent.option(
        str,
        "The starboard to get the most starred messages from",
        autocomplete=starboard_autocomplete,
    )
    channel = crescent.option(
        hikari.TextableGuildChannel,
        "Only show messages sent in this channel",
        default=None,
    )
    min_points = crescent.option(
        int,
        "Only show messages with at least this many points",
        default=None,
        min_value=1,
        name="min-points",
    )
    max_points = crescent.option(
        int,
        "Only show messages with at most this many points",
        default=None,
        min_value=1,
        name="max-points",
    )
    allow_nsfw = crescent.option(
        bool,
        "Whether to allow messages from NSFW channels",
        default=False,
        name="allow-nsfw",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        bot = cast("Bot", ctx.app)

        channel_is_nsfw = await bot.cache.gof_guild_channel_nsfw(
            ctx.channel_id
        )
        if self.allow_nsfw and not channel_is_nsfw:
            await ctx.respond(
                "To show NSFW messages, run this command in an NSFW channel.",
                ephemeral=True,
            )
            return

        s = await Starboard.from_name(ctx.guild_id, self.starboard)
        if s.private:
            raise StarboardError(f"{s.name} is a private starboard.")

        q = SBMessage.fetch_query()
        q.where(starboard_id=s.id)
        q.where(SBMessage.sb_message_id.is_null.not_)

        sbq = Message.fetch_query()
        sbq.where(message_id=SBMessage.message_id)
        sbq.where(trashed=False)
        if not self.allow_nsfw:
            sbq.where(is_nsfw=False)
        if self.channel:
            sbq.where(channel_id=self.channel.id)

        q.where(sbq.exists())

        if self.min_points:
            q.where(SBMessage.last_known_point_count.gteq(self.min_points))
        if self.max_points:
            q.where(SBMessage.last_known_point_count.lteq(self.max_points))

        q.order_by(SBMessage.last_known_point_count, True)
        cursor = q.cursor()

        guild = await Guild.fetch(guild_id=ctx.guild_id)

        async def next_page() -> tuple[list[hikari.Embed], str] | None:
            assert s is not None

            try:
                sql_msg = await cursor.__anext__()
            except StopAsyncIteration:
                return None
            orig = await Message.fetch(message_id=sql_msg.message_id)
            obj = await bot.cache.gof_message(orig.channel_id, orig.message_id)
            assert obj is not None

            config = await get_config(bot, s, orig.channel_id)
            raw, e, es = await embed_message(
                bot,
                obj,
                cast(int, ctx.guild_id),
                config.color,
                stored_to_emoji(config.display_emoji, bot)
                if config.display_emoji
                else None,
                config.use_server_profile,
                config.ping_author,
                sql_msg.last_known_point_count,
                orig.frozen,
                s.id in orig.forced_to,
                guild.premium_end is not None,
                config.attachments_list,
                config.jump_to_message,
                config.replied_to,
            )

            return [e, *es], raw

        paginator = InfiniteScroll(ctx.user.id, next_page)
        first_page = await paginator.get_page(0)
        if not first_page:
            raise StarboardError("Nothing to show.")
        first_embeds, first_content = first_page
        initial = await ctx.respond(
            content=first_content,
            embeds=first_embeds,
            components=paginator.build(),
            ensure_message=True,
        )
        await paginator.start(initial)
        try:
            await paginator.wait()
        finally:
            await cursor.aclose()
