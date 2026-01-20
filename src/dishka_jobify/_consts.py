from inspect import Parameter
from typing import Final

from jobify import INJECT, RequestState

CONTAINER_NAME: Final[str] = "dishka_container"

REQUEST_STATE_PARAM: Final[Parameter] = Parameter(
    name="___dishka_request_state",
    annotation=RequestState,
    kind=Parameter.KEYWORD_ONLY,
    default=INJECT,
)
