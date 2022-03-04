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

from time import time
from typing import Generic, TypeVar

_K = TypeVar("_K")


class SlidingWindow:
    # NOTE: This sliding window implementation was copied from the Cooldown
    # class in discord.py.

    __slots__ = ("rate", "per", "_window", "_tokens", "_last")

    def __init__(self, rate: float, per: float) -> None:
        self.rate: int = int(rate)
        self.per: float = float(per)
        self._window: float = 0.0
        self._tokens: int = self.rate
        self._last: float = 0.0

    def get_tokens(self, current: float | None = None) -> int:
        if not current:
            current = time()

        tokens = self._tokens

        if current > self._window + self.per:
            tokens = self.rate
        return tokens

    def get_retry_after(self, current: float | None = None) -> float:
        current = current or time()
        tokens = self.get_tokens(current)

        if tokens == 0:
            return self.per - (current - self._window)

        return 0.0

    def update_rate_limit(self, current: float | None = None) -> float | None:
        current = current or time()
        self._last = current

        self._tokens = self.get_tokens(current)

        # first token used means that we start a new rate limit window
        if self._tokens == self.rate:
            self._window = current

        # check if we are rate limited
        if self._tokens == 0:
            return self.per - (current - self._window)

        # we're not so decrement our tokens
        self._tokens -= 1
        return None

    def reset(self) -> None:
        self._tokens = self.rate
        self._last = 0.0


class Cooldown(Generic[_K]):
    def __init__(self, max_period: float) -> None:
        self.old: dict[_K, SlidingWindow] = {}
        self.cur: dict[_K, SlidingWindow] = {}
        self.max_period = max_period
        self.last_cycle = time()

    def __getitem__(self, key: _K) -> SlidingWindow:
        if v := self.old.pop(key, None):
            self.cur[key] = v
        return self.cur[key]

    def __setitem__(self, key: _K, value: SlidingWindow) -> None:
        self.cur[key] = value

    def get_bucket(self, key: _K, cap: int, period: int) -> SlidingWindow:
        now = time()
        if now > self.last_cycle + self.max_period:
            self.last_cycle = now

            self.old.clear()
            cur = self.cur
            self.cur = self.old
            self.old = cur

        try:
            return self[key]
        except KeyError:
            b = SlidingWindow(cap, period)
            self.cur[key] = b
            return b

    def trigger(self, key: _K, cap: int, period: int) -> bool:
        return self.get_bucket(key, cap, period).update_rate_limit() is None
