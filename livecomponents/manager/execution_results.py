import abc

from pydantic import BaseModel, ConfigDict, Field

from livecomponents.types import StateAddress


class IExecutionResult(abc.ABC):
    @abc.abstractmethod
    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        ...


class ComponentDirty(IExecutionResult):
    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        results.dirty_components.add(state_address)


class ParentDirty(IExecutionResult):
    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        results.dirty_components.add(state_address.must_get_parent())


class ComponentClean(IExecutionResult):
    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        pass


class RefreshPage(IExecutionResult):
    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        results.response_headers["HX-Refresh"] = "true"


class RedirectPage(IExecutionResult):
    def __init__(self, url: str):
        self.url = url

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        results.response_headers["HX-Redirect"] = self.url


class ExecutionResults(BaseModel):
    dirty_components: set[StateAddress] = Field(default_factory=set)
    response_headers: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    def is_partial_render_necessary(self) -> bool:
        full_rerender_headers = ["HX-Redirect", "HX-Refresh"]
        for header in self.response_headers:
            if header in full_rerender_headers:
                return False
        return True

    def process_returned_value(
        self,
        state_address: StateAddress,
        value: list[IExecutionResult] | IExecutionResult | None,
    ) -> None:
        """Process the method's returned value."""
        if value is None:
            value = [ComponentDirty()]
        if not isinstance(value, list):
            value = [value]
        for command in value:
            if not isinstance(command, IExecutionResult):
                raise RuntimeError(
                    "The function returned an invalid value. "
                    "Expected None or a subclass of IComponentCommand."
                )
            command.process(state_address, self)
