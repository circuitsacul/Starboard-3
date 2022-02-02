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

import nox


@nox.session
def pytest_and_mypy(session: nox.Session) -> None:
    session.install("poetry")
    session.run("poetry", "install")

    session.run("mypy", ".")
    session.run(
        "poetry",
        "run",
        "python",
        "-m",
        "pytest",
        "--cov=starboard/",
        "--cov-report=xml",
    )


@nox.session
def flake8(session: nox.Session) -> None:
    session.install("flake8")
    session.run("flake8")


@nox.session
def black(session: nox.Session) -> None:
    session.install("black")
    session.run("black", ".", "--check")


@nox.session
def isort(session: nox.Session) -> None:
    session.install("isort")
    session.run("isort", ".", "--check")
