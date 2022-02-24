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

from .models import (
    aschannel,
    guild,
    member,
    message,
    override,
    posrole,
    sb_message,
    star,
    starboard,
    user,
    xprole,
    permrole
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
            a.id
            for a in await aschannel.AutoStarChannel.fetch_query().fetchmany()
        }
        print("Autostar channels loaded.")

    guilds = guild.Guild
    users = user.User
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
    stars = star.Star

    indexes = [apgorm.Index(sb_messages, sb_messages.sb_message_id)]
