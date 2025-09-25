# OPBaseWrapper.DAT
from abc import ABC, abstractmethod
import td

class OPBaseWrapper(ABC):
    """Common interface for single and group wrappers."""
    @abstractmethod
    def __getattr__(self, name):
        pass  # Shared delegation to OP(s)

    def _extend(self, attr_name, value):
        # Shared extension logic (add to base, inherited by both)
        setattr(self, attr_name, value)
        return self
