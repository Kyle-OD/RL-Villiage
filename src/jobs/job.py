from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

class Job(ABC):
    """
    Base class for all jobs in the simulation.
    Jobs define specialized behaviors and skills for agents.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a job.
        
        Args:
            name: Name of the job
            description: Description of what the job does
        """
        self.name = name
        self.description = description
        self.skill_modifiers = {}  # Skill name -> modifier
        self.job_specific_data = {}  # Additional data specific to this job
    
    @abstractmethod
    def decide_action(self, agent, world):
        """
        Decide the next job-specific action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        pass
    
    @abstractmethod
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a job-specific action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        pass
    
    def assign_to_agent(self, agent):
        """
        Assign this job to an agent.
        
        Args:
            agent: The agent to assign the job to
        """
        # If agent already has a job, remove it first
        if agent.job:
            agent.job.remove_from_agent(agent)
            
        agent.job = self
        
        # Apply skill modifiers
        for skill_name, modifier in self.skill_modifiers.items():
            if skill_name in agent.skills:
                # Existing skills get boosted
                agent.skills[skill_name] *= (1.0 + modifier)
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent.
        
        Args:
            agent: The agent to remove the job from
        """
        if agent.job != self:
            return
            
        # Remove skill modifiers
        for skill_name, modifier in self.skill_modifiers.items():
            if skill_name in agent.skills:
                # Reverse the skill boost
                agent.skills[skill_name] /= (1.0 + modifier)
        
        # Clear job-specific state
        # Each job subclass can override this method to clear additional state
        agent.job = None
        
        # Reset job-specific actions
        if agent.current_action and not agent.current_action in ["wander", "go_home", "find_food", 
                                                               "find_water", "sleeping", "find_shelter", "socialize"]:
            agent.current_action = None
            agent.action_target = None
            agent.action_progress = 0.0
    
    def improve_skills(self, agent, skill_name: str, amount: float):
        """
        Improve an agent's skill based on job experience.
        
        Args:
            agent: The agent whose skill to improve
            skill_name: Name of the skill to improve
            amount: Amount to improve the skill by
        """
        if skill_name in agent.skills:
            # Skills improve more slowly as they get higher
            skill_level = agent.skills[skill_name]
            improvement = amount * (1.0 - skill_level * 0.5)  # Diminishing returns
            agent.skills[skill_name] = min(1.0, skill_level + improvement)
    
    def get_info(self) -> Dict:
        """
        Get information about this job.
        
        Returns:
            Dictionary with job information
        """
        return {
            "name": self.name,
            "description": self.description,
            "skill_modifiers": self.skill_modifiers.copy()
        } 