"""
Key facts gc agent implementation.

This agent is responsible for maintaining the knowledge base by pruning less important
facts when the total number exceeds a specified threshold. The agent evaluates all
key facts and deletes the least valuable ones to keep the database clean and relevant.
"""

import logging
from typing import List

from langchain_core.tools import tool
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

logger = logging.getLogger(__name__)

from ra_aid.agent_utils import create_agent, run_agent_with_retry
from ra_aid.database.repositories.key_fact_repository import get_key_fact_repository
from ra_aid.database.repositories.human_input_repository import HumanInputRepository
from ra_aid.llm import initialize_llm
from ra_aid.prompts.key_facts_gc_prompts import KEY_FACTS_GC_PROMPT
from ra_aid.tools.memory import log_work_event, _global_memory


console = Console()
human_input_repository = HumanInputRepository()


@tool
def delete_key_facts(fact_ids: List[int]) -> str:
    """Delete multiple key facts by their IDs.

    Args:
        fact_ids: List of IDs of the key facts to delete
        
    Returns:
        str: Success or failure message
    """
    deleted_facts = []
    not_found_facts = []
    failed_facts = []
    protected_facts = []
    
    # Try to get the current human input to protect its facts
    current_human_input_id = None
    try:
        recent_inputs = human_input_repository.get_recent(1)
        if recent_inputs and len(recent_inputs) > 0:
            current_human_input_id = recent_inputs[0].id
    except Exception as e:
        console.print(f"Warning: Could not retrieve current human input: {str(e)}")
    
    for fact_id in fact_ids:
        try:
            # Get the fact first to display information
            fact = get_key_fact_repository().get(fact_id)
            if fact:
                # Check if this fact is associated with the current human input
                if current_human_input_id is not None and fact.human_input_id == current_human_input_id:
                    protected_facts.append((fact_id, fact.content))
                    continue
                
                # Delete the fact if it's not protected
                was_deleted = get_key_fact_repository().delete(fact_id)
                if was_deleted:
                    deleted_facts.append((fact_id, fact.content))
                    log_work_event(f"Deleted fact {fact_id}.")
                else:
                    failed_facts.append(fact_id)
        except RuntimeError as e:
            logger.error(f"Failed to access key fact repository: {str(e)}")
            failed_facts.append(fact_id)
        except Exception as e:
            # For any other exceptions, log and continue
            logger.error(f"Error processing fact {fact_id}: {str(e)}")
            failed_facts.append(fact_id)
            
    # Prepare result message
    result_parts = []
    if deleted_facts:
        deleted_msg = "Successfully deleted facts:\n" + "\n".join([f"- #{fact_id}: {content}" for fact_id, content in deleted_facts])
        result_parts.append(deleted_msg)
        console.print(
            Panel(Markdown(deleted_msg), title="Facts Deleted", border_style="green")
        )
    
    if protected_facts:
        protected_msg = "Protected facts (associated with current request):\n" + "\n".join([f"- #{fact_id}: {content}" for fact_id, content in protected_facts])
        result_parts.append(protected_msg)
        console.print(
            Panel(Markdown(protected_msg), title="Facts Protected", border_style="blue")
        )
    
    if not_found_facts:
        not_found_msg = f"Facts not found: {', '.join([f'#{fact_id}' for fact_id in not_found_facts])}"
        result_parts.append(not_found_msg)
    
    if failed_facts:
        failed_msg = f"Failed to delete facts: {', '.join([f'#{fact_id}' for fact_id in failed_facts])}"
        result_parts.append(failed_msg)
    
    return "\n".join(result_parts)


def run_key_facts_gc_agent() -> None:
    """Run the key facts gc agent to maintain a reasonable number of key facts.
    
    The agent analyzes all key facts and determines which are the least valuable,
    deleting them to maintain a manageable collection size of high-value facts.
    Facts associated with the current human input are excluded from deletion.
    """
    # Get the count of key facts
    try:
        facts = get_key_fact_repository().get_all()
        fact_count = len(facts)
    except RuntimeError as e:
        logger.error(f"Failed to access key fact repository: {str(e)}")
        console.print(Panel(f"Error: {str(e)}", title="🗑 GC Error", border_style="red"))
        return  # Exit the function if we can't access the repository
    
    # Display status panel with fact count included
    console.print(Panel(f"Gathering my thoughts...\nCurrent number of key facts: {fact_count}", title="🗑 Garbage Collection"))
    
    # Only run the agent if we actually have facts to clean
    if fact_count > 0:
        # Try to get the current human input ID to exclude its facts
        current_human_input_id = None
        try:
            recent_inputs = human_input_repository.get_recent(1)
            if recent_inputs and len(recent_inputs) > 0:
                current_human_input_id = recent_inputs[0].id
        except Exception as e:
            console.print(f"Warning: Could not retrieve current human input: {str(e)}")
        
        # Get all facts that are not associated with the current human input
        eligible_facts = []
        protected_facts = []
        for fact in facts:
            if current_human_input_id is not None and fact.human_input_id == current_human_input_id:
                protected_facts.append(fact)
            else:
                eligible_facts.append(fact)
        
        # Only process if we have facts that can be deleted
        if eligible_facts:
            # Format facts as a dictionary for the prompt
            facts_dict = {fact.id: fact.content for fact in eligible_facts}
            formatted_facts = "\n".join([f"Fact #{k}: {v}" for k, v in facts_dict.items()])
            
            # Retrieve configuration
            llm_config = _global_memory.get("config", {})

            # Initialize the LLM model
            model = initialize_llm(
                llm_config.get("provider", "anthropic"),
                llm_config.get("model", "claude-3-7-sonnet-20250219"),
                temperature=llm_config.get("temperature")
            )
            
            # Create the agent with the delete_key_facts tool
            agent = create_agent(model, [delete_key_facts])
            
            # Format the prompt with the eligible facts
            prompt = KEY_FACTS_GC_PROMPT.format(key_facts=formatted_facts)
            
            # Set up the agent configuration
            agent_config = {
                "recursion_limit": 50  # Set a reasonable recursion limit
            }
            
            # Run the agent
            run_agent_with_retry(agent, prompt, agent_config)
            
            # Get updated count
            try:
                updated_facts = get_key_fact_repository().get_all()
                updated_count = len(updated_facts)
            except RuntimeError as e:
                logger.error(f"Failed to access key fact repository for update count: {str(e)}")
                updated_count = "unknown"
            
            # Show info panel with updated count and protected facts count
            protected_count = len(protected_facts)
            if protected_count > 0:
                console.print(
                    Panel(
                        f"Cleaned key facts: {fact_count} → {updated_count}\nProtected facts (associated with current request): {protected_count}",
                        title="🗑 GC Complete"
                    )
                )
            else:
                console.print(
                    Panel(
                        f"Cleaned key facts: {fact_count} → {updated_count}",
                        title="🗑 GC Complete"
                    )
                )
        else:
            console.print(Panel(f"All {len(protected_facts)} facts are associated with the current request and protected from deletion.", title="🗑 GC Info"))
    else:
        console.print(Panel("No key facts to clean.", title="🗑 GC Info"))