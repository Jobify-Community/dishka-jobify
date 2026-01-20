import inspect
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from dishka import AsyncContainer, Container, make_async_container, make_container
from jobify import Jobify

from dishka_jobify import JobifyProvider, setup_dishka

from .common import AppProvider

UTC = ZoneInfo("UTC")


async def _close_container(container: Any) -> None:
    result = container.close()
    if inspect.isawaitable(result):
        await result


@asynccontextmanager
async def _jobify_app(
    provider: AppProvider,
    *,
    use_async_container: bool,
) -> AsyncIterator[Jobify]:
    app = Jobify(tz=UTC, storage=False)

    container: AsyncContainer | Container

    if use_async_container:
        container = make_async_container(provider, JobifyProvider())
    else:
        container = make_container(provider, JobifyProvider())

    setup_dishka(container, app=app)

    try:
        yield app
    finally:
        await _close_container(container)


@pytest.fixture()
def app_provider() -> AppProvider:
    return AppProvider()


@pytest.fixture()
def jobify_app_async(app_provider: AppProvider) -> AbstractAsyncContextManager[Jobify]:
    return _jobify_app(app_provider, use_async_container=True)


@pytest.fixture()
def jobify_app_sync(app_provider: AppProvider) -> AbstractAsyncContextManager[Jobify]:
    return _jobify_app(app_provider, use_async_container=False)
