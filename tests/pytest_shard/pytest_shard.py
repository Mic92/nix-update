"""Shard tests to support parallelism across multiple machines."""

import hashlib
from collections.abc import Iterable, Sequence

from _pytest import nodes  # for type checking only
from _pytest.config import Config
from _pytest.config.argparsing import Parser


def positive_int(x: object) -> int:
    x = int(x)
    if x < 0:
        msg = f"Argument {x} must be positive"
        raise ValueError(msg)
    return x


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-shard specific configuration parameters."""
    group = parser.getgroup("shard")
    group.addoption(
        "--shard-id",
        dest="shard_id",
        type=positive_int,
        default=0,
        help="Number of this shard.",
    )
    group.addoption(
        "--num-shards",
        dest="num_shards",
        type=positive_int,
        default=1,
        help="Total number of shards.",
    )


def pytest_report_collectionfinish(config: Config, items: Sequence[nodes.Node]) -> str:
    """Log how many and, if verbose, which items are tested in this shard."""
    msg = f"Running {len(items)} items in this shard"
    if config.option.verbose > 0:
        msg += ": " + ", ".join([item.nodeid for item in items])
    return msg


def sha256hash(x: str) -> int:
    return int.from_bytes(hashlib.sha256(x.encode()).digest(), "little")


def filter_items_by_shard(
    items: Iterable[nodes.Node],
    shard_id: int,
    num_shards: int,
) -> Sequence[nodes.Node]:
    """Computes `items` that should be tested in `shard_id` out of `num_shards` total shards."""
    shards = [sha256hash(item.nodeid) % num_shards for item in items]

    new_items = []
    for shard, item in zip(shards, items, strict=True):
        if shard == shard_id:
            new_items.append(item)
    return new_items


def pytest_collection_modifyitems(config: Config, items: list[nodes.Node]) -> None:
    """Mutate the collection to consist of just items to be tested in this shard."""
    shard_id = config.getoption("shard_id")
    shard_total = config.getoption("num_shards")
    if shard_id >= shard_total:
        msg = f"shard_id={shard_id} must be less than num_shards={shard_total}"
        raise ValueError(msg)

    items[:] = filter_items_by_shard(items, shard_id, shard_total)
