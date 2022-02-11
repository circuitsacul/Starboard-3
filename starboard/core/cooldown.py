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

import asyncio
from time import time

from starboard.config import CONFIG


class SlidingWindow:
    __slots__ = ("capacity", "period", "cur_time", "pre_count", "cur_count")

    def __init__(self, capacity: int, period: int):
        self.capacity = capacity
        self.period = period

        self.cur_time = time()
        self.pre_count = capacity
        self.cur_count = 0

    def trigger(self) -> bool:
        now = time()
        if (now - self.cur_time) > self.period:
            self.cur_time = now
            self.pre_count = self.cur_count
            self.cur_count = 0

        ec = (
            self.pre_count
            * (self.period - (now - self.cur_time))
            / self.period
        ) + self.cur_count

        if ec > self.capacity:
            return False

        self.cur_count += 1
        return True


class Cooldown:
    def __init__(self) -> None:
        self.old: dict[tuple[int, int], SlidingWindow] = {}
        self.cur: dict[tuple[int, int], SlidingWindow] = {}

    def __getitem__(self, key: tuple[int, int]) -> SlidingWindow:
        if v := self.old.pop(key, None):
            self.cur[key] = v
        return self.cur[key]

    def __setitem__(self, key: tuple[int, int], value: SlidingWindow) -> None:
        self.cur[key] = value

    async def loop_cycle(self) -> None:
        while True:
            await asyncio.sleep(CONFIG.max_cooldown_period*2)

            del self.old
            self.old = self.cur
            self.cur = dict()

    def get_bucket(
        self, key: tuple[int, int], cap: int, period: int
    ) -> SlidingWindow:
        try:
            return self[key]
        except KeyError:
            b = SlidingWindow(cap, period)
            self.cur[key] = b
            return b

    def trigger(self, key: tuple[int, int], cap: int, period: int) -> bool:
        return self.get_bucket(key, cap, period).trigger()
