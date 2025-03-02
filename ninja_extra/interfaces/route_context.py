from abc import ABC, abstractmethod


class RouteContextBase(ABC):
    @property
    @abstractmethod
    def has_computed_route_parameters(self) -> bool: ...

    @abstractmethod
    def compute_route_parameters(self) -> None: ...
