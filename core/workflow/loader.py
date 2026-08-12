import json
from typing import Any

import yaml

from contracts.schemas.workflow import Workflow


class WorkflowLoader:
    @staticmethod
    def from_dict(data: dict[str, Any]) -> Workflow:
        return Workflow(**data)

    @staticmethod
    def from_json(json_str: str) -> Workflow:
        data = json.loads(json_str)
        return Workflow(**data)

    @staticmethod
    def from_yaml(yaml_str: str) -> Workflow:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise TypeError("YAML must contain a dictionary")
        # In a real app we might have a top level "workflow:" key
        if "workflow" in data:
            data = data["workflow"]
        return Workflow(**data)
