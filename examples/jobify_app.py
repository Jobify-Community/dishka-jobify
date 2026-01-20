import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dishka import FromDishka, Provider, Scope, make_async_container, provide
from jobify import JobContext, Jobify

from dishka_jobify import JobifyProvider, inject, setup_dishka


class GreetingService:
    def __init__(self, job_id: str) -> None:
        self._job_id = job_id

    def greet(self, name: str) -> str:
        return f"Hello, {name}! (job_id={self._job_id})"


class CounterService:
    def __init__(self) -> None:
        self._count = 0

    def increment(self) -> int:
        self._count += 1
        return self._count


class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def greeting_service(self, context: JobContext) -> GreetingService:
        return GreetingService(job_id=str(context.job.id))

    @provide(scope=Scope.APP)
    def counter_service(self) -> CounterService:
        return CounterService()


UTC = ZoneInfo("UTC")
app = Jobify(tz=UTC)

provider = MyProvider()
container = make_async_container(provider, JobifyProvider())
setup_dishka(container=container, app=app)


@app.task
@inject
async def my_cron(
    greeting: FromDishka[GreetingService],
    counter: FromDishka[CounterService],
) -> None:
    count = counter.increment()
    print(f"[cron] {greeting.greet('cron')} count={count}")


@app.task
@inject
async def my_job(
    name: str,
    greeting: FromDishka[GreetingService],
    counter: FromDishka[CounterService],
) -> None:
    count = counter.increment()
    now = datetime.now(tz=UTC)
    print(f"{greeting.greet(name)} at {now!r} count={count}")


async def main() -> None:
    async with app:
        run_next_seven_seconds = datetime.now(tz=UTC) + timedelta(seconds=7)
        job_at = await my_job.schedule(name="Connor").at(run_next_seven_seconds)
        job_delay = await my_job.schedule(name="Sara").delay(seconds=5)

        job_cron = await my_cron.schedule().cron(
            cron="* * * * *", job_id="greeting_cron", replace=True
        )

        await job_at.wait()
        await job_delay.wait()
        await job_cron.wait()


if __name__ == "__main__":
    asyncio.run(main())
