
from contracts.schemas.workflow import Workflow


class DAGResolver:
    """
    Resolves the execution order of a DAG defined in a Workflow.
    """
    def resolve(self, workflow: Workflow) -> list[list[str]]:
        """
        Returns a list of stages grouped by execution wave (topological sort).
        Each inner list contains stage IDs that can be executed in parallel.
        """
        # Build graph and indegree map
        graph: dict[str, list[str]] = {stage.id: [] for stage in workflow.stages}
        indegree: dict[str, int] = {stage.id: 0 for stage in workflow.stages}
        
        for stage in workflow.stages:
            for dep in stage.depends_on:
                if dep not in graph:
                    raise ValueError(f"Dependency '{dep}' not found in workflow stages.")
                graph[dep].append(stage.id)
                indegree[stage.id] += 1
                
        # Find roots
        queue = [node for node in indegree if indegree[node] == 0]
        waves = []
        
        while queue:
            waves.append(queue)
            next_queue = []
            for node in queue:
                for neighbor in graph[node]:
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue
            
        # Check for cycles
        processed_count = sum(len(wave) for wave in waves)
        if processed_count != len(workflow.stages):
            raise ValueError("Cycle detected in workflow dependencies.")
            
        return waves
