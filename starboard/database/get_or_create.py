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

from .models.guild import Guild
from .models.member import Member
from .models.message import Message
from .models.user import User


async def goc_guild(guild_id: int) -> Guild:
    if (g := await Guild.exists(id=guild_id)) is not None:
        return g
    return await Guild(id=guild_id).create()


async def goc_user(user_id: int, is_bot: bool) -> User:
    if (u := await User.exists(id=user_id)) is not None:
        return u
    return await User(id=user_id, is_bot=is_bot).create()


async def goc_member(guild_id: int, user_id: int, is_bot: bool) -> Member:
    if (
        m := await Member.exists(guild_id=guild_id, user_id=user_id)
    ) is not None:
        return m

    await goc_guild(guild_id)
    await goc_user(user_id, is_bot)

    return await Member(guild_id=guild_id, user_id=user_id).create()


async def goc_message(
    guild_id: int,
    channel_id: int,
    message_id: int,
    is_nsfw: bool,
    author_id: int,
    is_author_bot: bool,
) -> Message:
    if (m := await Message.exists(id=message_id)) is not None:
        return m

    await goc_member(guild_id, author_id, is_author_bot)

    return await Message(
        guild_id=guild_id,
        author_id=author_id,
        channel_id=channel_id,
        id=message_id,
        is_nsfw=is_nsfw,
    ).create()
