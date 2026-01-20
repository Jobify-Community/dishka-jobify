from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from dishka.integrations.base import wrap_injection

from dishka_jobify._consts import REQUEST_STATE_PARAM
from dishka_jobify._getters import (
    get_async_container_from_args_kwargs,
    get_sync_container_from_args_kwargs,
)

ReturnT = TypeVar("ReturnT")
ParamsP = ParamSpec("ParamsP")


def inject_async(
    func: Callable[ParamsP, Awaitable[ReturnT]],
) -> Callable[ParamsP, Awaitable[ReturnT]]:
    return wrap_injection(
        func=func,
        container_getter=get_async_container_from_args_kwargs,
        remove_depends=True,
        is_async=True,
        manage_scope=False,
        additional_params=[REQUEST_STATE_PARAM],
    )


def inject_sync(func: Callable[ParamsP, ReturnT]) -> Callable[ParamsP, ReturnT]:
    return wrap_injection(
        func=func,
        container_getter=get_sync_container_from_args_kwargs,
        remove_depends=True,
        is_async=False,
        manage_scope=False,
        additional_params=[REQUEST_STATE_PARAM],
    )
