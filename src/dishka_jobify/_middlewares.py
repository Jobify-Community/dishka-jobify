from typing import Any, Final

from dishka import AsyncContainer, Container
from jobify import Job, JobContext, RequestState, Runnable, State
from jobify.middleware import BaseMiddleware, CallNext
from typing_extensions import override

from dishka_jobify._consts import CONTAINER_NAME


def _build_context_data(context: JobContext) -> dict[Any, Any]:
    return {
        JobContext: context,
        Job: context.job,
        State: context.state,
        RequestState: context.request_state,
        Runnable: context.runnable,
    }


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
