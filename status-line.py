#!/usr/bin/env python3

from dataclasses import dataclass
from functools import partial
from itertools import count
from locale import str as format_float
from operator import pow
from os import environ
from time import sleep
from typing import Any, cast

from psutil import cpu_percent, disk_io_counters, net_io_counters, virtual_memory

_INTERVAL = 1

_LO_TIDE = 40
_HI_TIDE = 80

_LO, _MED, _HI, _TRANS = (
    environ["tmux_colour_low"],
    environ["tmux_colour_med"],
    environ["tmux_colour_hi"],
    environ["tmux_trans"],
)


@dataclass(frozen=True)
class _Stats:
    cpu_percent: int
    mem_percent: int
    disk_read: int
    disk_write: int
    net_sent: int
    net_recv: int


def _human_readable_size(size: float, precision: int = 3) -> str:
    units = ("", "K", "M", "G", "T", "P", "E", "Z", "Y")
    step = partial(pow, 10)
    steps = zip(map(step, count(0, step=3)), units)
    for factor, unit in steps:
        divided = size / factor
        if abs(divided) < 1000:
            fmt = format_float(round(divided, precision))
            return f"{fmt}{unit}"
    else:
        raise ValueError(f"unit over flow: {size}")


def _measure() -> _Stats:
    _ = cpu_percent()
    disk_1 = cast(Any, disk_io_counters())
    net_1 = cast(Any, net_io_counters())

    sleep(_INTERVAL)

    cpu = int(cast(float, cpu_percent()))
    mem = virtual_memory()
    disk_2 = cast(Any, disk_io_counters())
    net_2 = cast(Any, net_io_counters())

    stats = _Stats(
        cpu_percent=cpu,
        mem_percent=int(mem.percent),
        disk_read=disk_2.read_bytes - disk_1.read_bytes,
        disk_write=disk_2.write_bytes - disk_1.write_bytes,
        net_sent=net_2.bytes_sent - net_1.bytes_sent,
        net_recv=net_2.bytes_recv - net_1.bytes_recv,
    )
    return stats


def _colour(val: int) -> str:
    if val < _LO_TIDE:
        return f"#[bg={_LO}]"
    elif val < _HI_TIDE:
        return f"#[bg={_MED}]"
    else:
        return f"#[bg={_HI}]"


def main() -> None:
    stats = _measure()

    cpu = f"{format(stats.cpu_percent, '3d')}%"
    mem = f"{format(stats.mem_percent, '3d')}%"

    disk_read = f"{_human_readable_size(stats.disk_read,precision=0)}B"
    disk_write = f"{_human_readable_size(stats.disk_write,precision=0)}B"

    net_sent = f"{_human_readable_size(stats.net_sent,precision=0)}B"
    net_recv = f"{_human_readable_size(stats.net_recv,precision=0)}B"

    line = (
        f"[⇡ {net_sent} ⇣ {net_recv}] "
        f"[📖 {disk_read} ✏️  {disk_write}] "
        f"{_colour(stats.cpu_percent)} λ{cpu} {_TRANS} "
        f"{_colour(stats.mem_percent)} τ{mem} {_TRANS}"
    )
    print(line)


main()
