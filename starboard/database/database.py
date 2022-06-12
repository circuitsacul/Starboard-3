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
from apgorm import Index, IndexType

from .models import (
    aschannel,
    guild,
    member,
    message,
    override,
    permrole,
    posrole,
    sb_message,
    starboard,
    user,
    vote,
    xprole,
)


class Database(apgorm.Database):
    def __init__(self):
        super().__init__("starboard/database/migrations")

        self.asc: set[int] = set()

    async def connect(
        self, *, migrate: bool = False, **connect_kwargs
    ) -> None:
        await super().connect(**connect_kwargs)
        if self.must_create_migrations():
            raise Exception("There are uncreated migrations.")
        if migrate and await self.must_apply_migrations():
            print("Applying migrations...")
            await self.apply_migrations()

        print("Loading autostar channels...")
        self.asc = {
            a.channel_id
            for a in await aschannel.AutoStarChannel.fetch_query().fetchmany()
        }
        print("Autostar channels loaded.")

    guilds = guild.Guild
    users = user.User
    patrons = user.Patron
    members = member.Member

    starboards = starboard.Starboard
    overrides = override.Override
    permroles = permrole.PermRole
    permrole_starboards = permrole.PermRoleStarboard
    aschannels = aschannel.AutoStarChannel

    xproles = xprole.XPRole
    posroles = posrole.PosRole
    posrole_members = posrole.PosRoleMember

    messages = message.Message
    sb_messages = sb_message.SBMessage
    votes = vote.Vote

    indexes = [
        # patrons
        Index(patrons, patrons.discord_id, IndexType.BTREE),
        # autostar channels
        Index(aschannels, aschannels.channel_id, IndexType.BTREE),
        Index(aschannels, aschannels.guild_id, IndexType.BTREE),
        Index(aschannels, aschannels.name, IndexType.BTREE),
        # guild
        Index(guilds, guilds.premium_end, IndexType.BTREE),
        # member
        Index(members, members.guild_id, IndexType.BTREE),
        Index(members, members.autoredeem_enabled, IndexType.BTREE),
        Index(members, members.xp, IndexType.BTREE),
        # overrides
        Index(
            overrides,
            (overrides.guild_id, overrides.name),
            IndexType.BTREE,
            unique=True,
        ),
        Index(overrides, overrides.starboard_id, IndexType.BTREE),
        Index(overrides, overrides.channel_ids, IndexType.GIN),
        # sbmessages
        Index(sb_messages, sb_messages.sb_message_id, unique=True),
        Index(sb_messages, sb_messages.last_known_point_count),
        Index(sb_messages, sb_messages.starboard_id, IndexType.BTREE),
        # permroles
        Index(permroles, permroles.guild_id, IndexType.BTREE),
        # posroles
        Index(
            posroles, (posroles.guild_id, posroles.max_members), unique=True
        ),
        # starboards
        Index(starboards, starboards.channel_id, IndexType.BTREE),
        Index(starboards, starboards.guild_id, IndexType.BTREE),
        Index(starboards, starboards.upvote_emojis, IndexType.GIN),
        Index(starboards, starboards.downvote_emojis, IndexType.GIN),
        Index(starboards, starboards.name, IndexType.BTREE),
        # xproles
        Index(xproles, xproles.guild_id, IndexType.BTREE),
        # votes
        Index(votes, votes.starboard_id, IndexType.BTREE),
        Index(votes, votes.user_id, IndexType.BTREE),
        Index(votes, votes.message_id, IndexType.BTREE),
        Index(votes, votes.target_author_id, IndexType.BTREE),
        Index(votes, votes.is_downvote, IndexType.BTREE),
    ]
