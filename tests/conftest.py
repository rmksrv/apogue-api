from typing import Iterable


def pytest_make_parametrize_id(config, val, argname):
    if argname == "anyio_backend":
        return None
    if isinstance(val, int | str):
        return f"{argname}={val}"
    if isinstance(val, Iterable):
        return f"{argname}={str(val)}"
    return None
