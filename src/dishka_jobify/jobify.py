__all__ = ("JobifyProvider", "inject", "setup_dishka")

import inspect
from collections.abc import Awaitable, Callable
from inspect import Parameter
from itertools import chain
from typing import Any, Final, ParamSpec, TypeVar, overload

from dishka import AsyncContainer, Container, Provider, Scope, from_context
from dishka.exception_base import DishkaError
from dishka.integrations.base import wrap_injection
from jobify import (
    INJECT,
    Job,
    JobContext,
    Jobify,
    RequestState,
    Runnable,
    State,
)
from jobify.middleware import BaseMiddleware, CallNext
from typing_extensions import override

_ReturnT = TypeVar("_ReturnT")
_ParamsP = ParamSpec("_ParamsP")

CONTAINER_NAME: Final[str] = "dishka_container"
REQUEST_STATE_PARAM: Final[Parameter] = Parameter(
    name="___dishka_request_state",
    annotation=RequestState,
    kind=Parameter.KEYWORD_ONLY,
    default=INJECT,
)


def _build_context_data(context: JobContext) -> dict[Any, Any]:
    return {
        JobContext: context,
        Job: context.job,
        State: context.state,
        RequestState: context.request_state,
        Runnable: context.runnable,
    }


def _inject_async(
    func: Callable[_ParamsP, Awaitable[_ReturnT]],
) -> Callable[_ParamsP, Awaitable[_ReturnT]]:
    return wrap_injection(
        func=func,
        container_getter=_get_async_container_from_args_kwargs,
        remove_depends=True,
        is_async=True,
        manage_scope=False,
        additional_params=[REQUEST_STATE_PARAM],
    )


def _inject_sync(func: Callable[_ParamsP, _ReturnT]) -> Callable[_ParamsP, _ReturnT]:
    return wrap_injection(
        func=func,
        container_getter=_get_sync_container_from_args_kwargs,
        remove_depends=True,
        is_async=False,
        manage_scope=False,
        additional_params=[REQUEST_STATE_PARAM],
    )


class DishkaSyncMiddleware(BaseMiddleware):
    def __init__(self, container: Container) -> None:
        super().__init__()
        self._container: Final[Container] = container

    @override
    async def __call__(self, call_next: CallNext, context: JobContext) -> Any:
        if CONTAINER_NAME in context.request_state:
            return await call_next(context)

        context_data = _build_context_data(context)
        with self._container(context=context_data) as request_container:
            context.request_state[CONTAINER_NAME] = request_container
            try:
                return await call_next(context)
            finally:
                context.request_state.pop(CONTAINER_NAME, None)


class DishkaAsyncMiddleware(BaseMiddleware):
    def __init__(self, container: AsyncContainer) -> None:
        super().__init__()
        self._container: Final[AsyncContainer] = container

    @override
    async def __call__(self, call_next: CallNext, context: JobContext) -> Any:
        if CONTAINER_NAME in context.request_state:
            return await call_next(context)

        context_data = _build_context_data(context)
        async with self._container(context=context_data) as request_container:
            context.request_state[CONTAINER_NAME] = request_container
            try:
                return await call_next(context)
            finally:
                context.request_state.pop(CONTAINER_NAME, None)


def _get_request_state_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> RequestState:
    request_state = kwargs.get(REQUEST_STATE_PARAM.name)
    if isinstance(request_state, RequestState):
        return request_state

    for value in chain(args, kwargs.values()):
        if isinstance(value, RequestState):
            return value

    msg = (
        "Cannot find RequestState. "
        "Make sure you used @inject/@inject_sync and Jobify injected it."
    )

    raise DishkaError(msg)


def _get_container_from_request_state(
    request_state: RequestState,
) -> AsyncContainer | Container:
    container: AsyncContainer | Container | None = request_state.get(CONTAINER_NAME)
    if container is None:
        msg = (
            f"Container not found in request_state['{CONTAINER_NAME}']. "
            "Make sure you called setup_dishka() for the Jobify app."
        )
        raise DishkaError(msg)

    return container


def _get_async_container_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncContainer:
    request_state: RequestState = _get_request_state_from_args_kwargs(args, kwargs)
    container: AsyncContainer | Container = _get_container_from_request_state(
        request_state
    )

    if not isinstance(container, AsyncContainer):
        msg = f"Expected AsyncContainer in request_state for key '{CONTAINER_NAME}'."
        raise DishkaError(msg)

    return container


def _get_sync_container_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Container:
    request_state: RequestState = _get_request_state_from_args_kwargs(args, kwargs)
    container: Container | AsyncContainer = _get_container_from_request_state(
        request_state
    )

    if not isinstance(container, Container):
        msg = f"Expected Container in request_state for key '{CONTAINER_NAME}'."
        raise DishkaError(msg)

    return container


class JobifyProvider(Provider):
    context = from_context(JobContext, scope=Scope.REQUEST)
    job = from_context(Job, scope=Scope.REQUEST)
    state = from_context(State, scope=Scope.REQUEST)
    request_state = from_context(RequestState, scope=Scope.REQUEST)
    runnable = from_context(Runnable, scope=Scope.REQUEST)


@overload
def inject(func: Callable[_ParamsP, _ReturnT]) -> Callable[_ParamsP, _ReturnT]: ...


@overload
def inject(
    func: Callable[_ParamsP, Awaitable[_ReturnT]],
) -> Callable[_ParamsP, Awaitable[_ReturnT]]: ...


def inject(func: Callable[_ParamsP, Any]) -> Callable[_ParamsP, Any]:
    if inspect.iscoroutinefunction(func):
        return _inject_async(func)
    return _inject_sync(func)


def setup_dishka(container: AsyncContainer | Container, app: Jobify) -> None:
    app.state[CONTAINER_NAME] = container

    if isinstance(container, AsyncContainer):
        app.add_middleware(DishkaAsyncMiddleware(container))
    else:
        app.add_middleware(DishkaSyncMiddleware(container))
