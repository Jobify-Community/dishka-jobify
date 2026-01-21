# Jobify integration for Dishka

[![Downloads](https://static.pepy.tech/personalized-badge/dishka-jobify?period=month&units=international_system&left_color=grey&right_color=green&left_text=downloads/month)](https://www.pepy.tech/projects/dishka-jobify)
[![Package version](https://img.shields.io/pypi/v/dishka-jobify?label=PyPI)](https://pypi.org/project/dishka-jobify)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/dishka-jobify.svg)](https://pypi.org/project/dishka-jobify)

Though it is not required, you can use *dishka-jobify* integration. It features:

* *REQUEST* scope management using jobify request scope
* *JobifyProvider* for working with `JobContext`, `Job`, `State`, `RequestState`, `Runnable` in container

You need to specify `@inject` manually.

## Installation

Install using `pip`

```sh
pip install dishka-jobify
```

Or with `uv`

```sh
uv add dishka-jobify
```

## How to use

1. Import

```python
from dishka_jobify import (
    FromDishka,
    inject,
    setup_dishka
)
from dishka import make_async_container, Provider, provide, Scope
```

2. Create provider like here below

```python
class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_greeting_service(self) -> GreetingService:
        return GreetingService(name="Dishka User")

    @provide(scope=Scope.APP)
    def get_counter_service(self) -> CounterService:
        return CounterService()
```

3. Mark those of your handlers parameters which are to be injected with `FromDishka[]`

```python
@app.task
@inject
async def my_cron(
    greeting: FromDishka[GreetingService],
    counter: FromDishka[CounterService],
) -> None:
    count = counter.increment()
    print(f"[cron] {greeting.greet('cron')} count={count}")
```

4. Setup `dishka` integration.

```python
UTC = ZoneInfo("UTC")
app = Jobify(tz=UTC)

provider = MyProvider()
container = make_async_container(provider, JobifyProvider())
setup_dishka(container=container, app=app)
```
