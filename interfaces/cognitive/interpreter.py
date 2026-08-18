import abc

from contracts.schemas.context import ExecutionContext
from contracts.schemas.delta import WorldStateDelta
from contracts.schemas.prompt import PromptAsset
from contracts.schemas.world import Evidence, WorldState
from interfaces.cognitive.vlm_provider import VLMProvider


class BaseInterpreter(abc.ABC):
    """
    Base contract for cognitive interpretation layers.
    Interpreters do not mutate the WorldState directly; they return a WorldStateDelta.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the interpreter"""

    @property
    @abc.abstractmethod
    def consumes(self) -> list[str]:
        """List of domains this interpreter reads from."""

    @property
    @abc.abstractmethod
    def produces(self) -> list[str]:
        """List of domains this interpreter yields operations for."""

    @abc.abstractmethod
    def interpret(
        self,
        world_state: WorldState,
        evidence: Evidence,
        prompt: PromptAsset,
        context: ExecutionContext,
        vlm_provider: VLMProvider,
    ) -> WorldStateDelta:
        """
        Executes interpretation logic over the evidence using the VLM,
        and returns a structured WorldStateDelta representing the findings.
        """
