from typing import TYPE_CHECKING, Union
from langgraph.graph.graph import CompiledGraph

# Unfortunately need this to avoid Circular Imports
if TYPE_CHECKING:
    from ra_aid.agents.ciayn_agent import CiaynAgent
    
    RAgents = Union[CompiledGraph, CiaynAgent]
else:
    RAgents = Union[CompiledGraph, object]
