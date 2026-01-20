__all__ = ("JobifyProvider", "inject", "setup_dishka")

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, overload

from dishka import AsyncContainer, Container, Provider, Scope, from_context
from jobify import (
    Job,
    JobContext,
    Jobify,
    RequestState,
    Runnable,
    State,
)

from dishka_jobify._consts import CONTAINER_NAME
from dishka_jobify._injectors import ParamsP, ReturnT, inject_async, inject_sync
from dishka_jobify._middlewares import DishkaAsyncMiddleware, DishkaSyncMiddleware


class JobifyProvider(Provider):
    context = from_context(JobContext, scope=Scope.REQUEST)
    job = from_context(Job, scope=Scope.REQUEST)
    state = from_context(State, scope=Scope.REQUEST)
    request_state = from_context(RequestState, scope=Scope.REQUEST)
    runnable = from_context(Runnable, scope=Scope.REQUEST)


@overload
def inject(func: Callable[ParamsP, ReturnT]) -> Callable[..., ReturnT]: ...


@overload
def inject(
    func: Callable[ParamsP, Awaitable[ReturnT]],
) -> Callable[..., Awaitable[ReturnT]]: ...


def inject(func: Callable[ParamsP, Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(func):
        return inject_async(func)
    return inject_sync(func)


def setup_dishka(container: AsyncContainer | Container, app: Jobify) -> None:
    app.state[CONTAINER_NAME] = container

    if isinstance(container, AsyncContainer):
        app.add_middleware(DishkaAsyncMiddleware(container))
    else:
        app.add_middleware(DishkaSyncMiddleware(container))
