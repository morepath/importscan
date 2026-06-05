from __future__ import annotations

calls = 0


def call() -> None:
    global calls
    calls += 1


def reset() -> None:
    global calls
    calls = 0
