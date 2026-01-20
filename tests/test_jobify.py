from contextlib import AbstractAsyncContextManager
from unittest.mock import Mock

import pytest
from dishka.exception_base import DishkaError
from jobify import Jobify

from dishka_jobify import FromDishka, inject

from .common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppMock,
    AppProvider,
    JobIdDep,
    RequestDep,
)


@pytest.mark.asyncio()
async def test_async_inject_request_scope(
    app_provider: AppProvider,
    jobify_app_async: AbstractAsyncContextManager[Jobify],
) -> None:
    async with jobify_app_async as app:

        @app.task
        @inject
        async def handle(
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
            job_id: FromDishka[JobIdDep],
            mock: FromDishka[Mock],
        ) -> None:
            mock(app_dep, request_dep, job_id)

        async with app:
            job = await handle.schedule().delay(seconds=0.01)
            await job.wait()

        app_provider.mock.assert_called_once_with(
            APP_DEP_VALUE,
            REQUEST_DEP_VALUE,
            JobIdDep(str(job.id)),
        )
        app_provider.request_released.assert_called_once()

    app_provider.app_released.assert_called_once()


@pytest.mark.asyncio()
async def test_sync_inject_request_scope(
    app_provider: AppProvider,
    jobify_app_sync: AbstractAsyncContextManager[Jobify],
) -> None:
    async with jobify_app_sync as app:

        @app.task
        @inject
        def handle(
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
            job_id: FromDishka[JobIdDep],
            mock: FromDishka[Mock],
        ) -> None:
            mock(app_dep, request_dep, job_id)

        async with app:
            job = await handle.schedule().delay(seconds=0.01)
            await job.wait()

        app_provider.mock.assert_called_once_with(
            APP_DEP_VALUE,
            REQUEST_DEP_VALUE,
            JobIdDep(str(job.id)),
        )
        app_provider.request_released.assert_called_once()

    app_provider.app_released.assert_called_once()


@pytest.mark.asyncio()
async def test_async_request_scope_per_job(
    app_provider: AppProvider,
    jobify_app_async: AbstractAsyncContextManager[Jobify],
) -> None:
    async with jobify_app_async as app:

        @app.task
        @inject
        async def handle(
            app_dep: FromDishka[AppDep],
            request_dep: FromDishka[RequestDep],
            job_id: FromDishka[JobIdDep],
            mock: FromDishka[Mock],
        ) -> None:
            mock(app_dep, request_dep, job_id)

        async with app:
            first = await handle.schedule().delay(seconds=0.01)
            second = await handle.schedule().delay(seconds=0.01)
            await first.wait()
            await second.wait()

        assert app_provider.mock.call_count == 2
        assert app_provider.request_released.call_count == 2

    app_provider.app_released.assert_called_once()


@pytest.mark.asyncio()
async def test_app_scope_reuse(
    app_provider: AppProvider,
    jobify_app_async: AbstractAsyncContextManager[Jobify],
) -> None:
    app_mocks: list[AppMock] = []

    async with jobify_app_async as app:

        @app.task
        @inject
        async def handle(
            app_dep: FromDishka[AppDep],
            app_mock: FromDishka[AppMock],
        ) -> None:
            del app_dep
            app_mocks.append(app_mock)

        async with app:
            first = await handle.schedule().delay(seconds=0.01)
            second = await handle.schedule().delay(seconds=0.01)
            await first.wait()
            await second.wait()

        assert app_mocks[0] is app_mocks[1]

    app_provider.app_released.assert_called_once()


@pytest.mark.asyncio()
async def test_missing_setup_dishka_raises() -> None:
    app = Jobify(storage=False)

    @app.task
    @inject
    async def handle(request_dep: FromDishka[RequestDep]) -> None:
        del request_dep

    async with app:
        job = await handle.schedule().delay(seconds=0.01)
        await job.wait()
        assert isinstance(job.exception, DishkaError)
        assert "Container not found" in str(job.exception)


@pytest.mark.asyncio()
async def test_async_task_with_sync_container_raises(
    app_provider: AppProvider,
    jobify_app_sync: AbstractAsyncContextManager[Jobify],
) -> None:
    async with jobify_app_sync as app:

        @app.task
        @inject
        async def handle(app_dep: FromDishka[AppDep]) -> None:
            del app_dep

        async with app:
            job = await handle.schedule().delay(seconds=0.01)
            await job.wait()
        assert isinstance(job.exception, DishkaError)
        assert "Expected AsyncContainer" in str(job.exception)


@pytest.mark.asyncio()
async def test_sync_task_with_async_container_raises(
    app_provider: AppProvider,
    jobify_app_async: AbstractAsyncContextManager[Jobify],
) -> None:
    async with jobify_app_async as app:

        @app.task
        @inject
        def handle(app_dep: FromDishka[AppDep]) -> None:
            del app_dep

        async with app:
            job = await handle.schedule().delay(seconds=0.01)
            await job.wait()
        assert isinstance(job.exception, DishkaError)
        assert "Expected Container" in str(job.exception)
