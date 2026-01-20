from itertools import chain
from typing import Any

from dishka import AsyncContainer, Container
from dishka.exception_base import DishkaError
from jobify import RequestState

from dishka_jobify._consts import CONTAINER_NAME, REQUEST_STATE_PARAM


def get_request_state_from_args_kwargs(
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


def get_container_from_request_state(
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


def get_async_container_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncContainer:
    request_state: RequestState = get_request_state_from_args_kwargs(args, kwargs)
    container: AsyncContainer | Container = get_container_from_request_state(
        request_state
    )

    if not isinstance(container, AsyncContainer):
        msg = f"Expected AsyncContainer in request_state for key '{CONTAINER_NAME}'."
        raise DishkaError(msg)

    return container


def get_sync_container_from_args_kwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Container:
    request_state: RequestState = get_request_state_from_args_kwargs(args, kwargs)
    container: Container | AsyncContainer = get_container_from_request_state(
        request_state
    )

    if not isinstance(container, Container):
        msg = f"Expected Container in request_state for key '{CONTAINER_NAME}'."
        raise DishkaError(msg)

    return container
