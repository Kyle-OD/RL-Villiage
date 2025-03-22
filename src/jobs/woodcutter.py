import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class WoodcutterJob(Job):
    """
    Woodcutter job responsible for harvesting wood from trees.
    Woodcutters locate forest areas, fell trees, and bring lumber back to the village.
    """
    
    def __init__(self):
        """Initialize the woodcutter job with appropriate skills and data"""
        super().__init__("woodcutter", "Harvests wood from forests and processes it into lumber")
        
        # Set skill modifiers - woodcutters get bonuses to these skills
        self.skill_modifiers = {
            "woodcutting": 0.5,  # Major boost to woodcutting
            "strength": 0.3,     # Minor boost to strength
            "survival": 0.2      # Minor boost to survival
        }
        
        # Job-specific data
        self.job_specific_data = {
            "known_forests": [],  # Coordinates of known forest locations
            "current_forest": None,  # Current forest being worked
            "wood_stockpile": 0.0,  # Temporary wood being carried
            "max_carry_capacity": 50.0,  # Maximum wood that can be carried
            "trees_felled": 0  # Career statistic
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next woodcutting action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Check if carrying capacity reached
        if self.job_specific_data["wood_stockpile"] >= self.job_specific_data["max_carry_capacity"]:
            # Return to village/storage
            agent._set_action("return_with_wood", None)
            return
        
        # Check if agent has a forest assigned
        if not self.job_specific_data["current_forest"]:
            # Find a forest to work in
            agent._set_action("find_forest", None)
            return
        
        # Check if agent is at their assigned forest
        forest_pos = self.job_specific_data["current_forest"]
        if agent.position != forest_pos:
            # Go to forest
            agent._set_action("go_to_forest", forest_pos)
            return
        
        # At the forest, check if there are trees to cut
        # This would use resource manager to check for tree resources
        resources = world.resource_manager.get_resources_at(*forest_pos)
        has_trees = any(r.resource_type == ResourceType.TREE for r in resources)
        
        if has_trees:
            # Chop trees
            agent._set_action("chop_wood", forest_pos)
        else:
            # No trees left, find a new forest
            self.job_specific_data["current_forest"] = None
            agent._set_action("find_forest", None)
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a woodcutting action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "find_forest":
            return self._progress_find_forest(agent, world, time_delta)
        elif action == "go_to_forest":
            return self._progress_go_to_forest(agent, world, time_delta)
        elif action == "chop_wood":
            return self._progress_chop_wood(agent, world, time_delta)
        elif action == "return_with_wood":
            return self._progress_return_with_wood(agent, world, time_delta)
        
        return None
    
    def _progress_find_forest(self, agent, world, time_delta: float):
        """Find a forest area to work in"""
        # If we already know forest locations, pick one
        if self.job_specific_data["known_forests"]:
            # Assign a known forest
            forest_pos = random.choice(self.job_specific_data["known_forests"])
            self.job_specific_data["current_forest"] = forest_pos
            agent._set_action("go_to_forest", forest_pos)
            return {"agent": agent.name, "action": "assigned_forest", "location": forest_pos}
        
        # Look for potential forest areas nearby
        x, y = agent.position
        neighbors = world.get_neighboring_cells(x, y, 5)  # Search in a larger radius
        
        # Check for suitable forest locations
        potential_forests = []
        for nx, ny in neighbors:
            resources = world.resource_manager.get_resources_at(nx, ny)
            
            # Look for tree resources
            has_trees = any(r.resource_type == ResourceType.TREE for r in resources)
            
            if has_trees:
                potential_forests.append((nx, ny))
        
        if potential_forests:
            # Found a forest
            forest_pos = random.choice(potential_forests)
            self.job_specific_data["known_forests"].append(forest_pos)
            self.job_specific_data["current_forest"] = forest_pos
            agent._set_action("go_to_forest", forest_pos)
            
            # Add forest to memory
            if "forest" not in agent.known_locations:
                agent.known_locations["forest"] = []
            if forest_pos not in agent.known_locations["forest"]:
                agent.known_locations["forest"].append(forest_pos)
                
            return {"agent": agent.name, "action": "found_forest", "location": forest_pos}
        
        # No good spot found, wander and look more
        agent._progress_wander(world, time_delta)
        agent.action_progress = 0.5  # Still looking
        return None
    
    def _progress_go_to_forest(self, agent, world, time_delta: float):
        """Go to the assigned forest"""
        forest_pos = agent.action_target
        if not forest_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = forest_pos
        
        # Already at forest
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_forest", "location": forest_pos}
        
        # Move towards forest
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent.action_progress = 1.0
        else:
            agent.action_progress = 0.5  # Still in progress
            
        return None
    
    def _progress_chop_wood(self, agent, world, time_delta: float):
        """Chop wood from trees"""
        # Check if we're at the forest
        forest_pos = agent.action_target
        if agent.position != forest_pos:
            agent._set_action("go_to_forest", forest_pos)
            return None
        
        # Get tree resources at location
        resources = world.resource_manager.get_resources_at(*forest_pos)
        tree_resources = [r for r in resources if r.resource_type == ResourceType.TREE]
        
        if not tree_resources:
            # No trees here anymore
            agent.action_progress = 1.0
            self.job_specific_data["current_forest"] = None
            return {"agent": agent.name, "action": "forest_depleted", "location": forest_pos}
        
        # Chop wood
        if agent.action_progress < 0.95:
            # Still chopping
            woodcutting_skill = agent.skills["woodcutting"]
            progress_amount = 0.15 + woodcutting_skill * 0.15
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "woodcutting", 0.006)
            self.improve_skills(agent, "strength", 0.003)
            
            return None
        else:
            # Chopping complete - harvest wood from a tree
            agent.action_progress = 1.0
            
            # Determine amount of wood harvested based on skill
            woodcutting_skill = agent.skills["woodcutting"]
            wood_amount = 10.0 + woodcutting_skill * 15.0  # 10-25 units based on skill
            
            # Add to stockpile
            self.job_specific_data["wood_stockpile"] += wood_amount
            
            # Remove some of the tree resource (trees are renewable)
            tree = tree_resources[0]
            tree.quantity -= 1
            
            if tree.quantity <= 0:
                # Tree has been completely felled
                world.resource_manager.remove_resource(tree)
                self.job_specific_data["trees_felled"] += 1
            
            # If we've reached capacity, head back to village
            if self.job_specific_data["wood_stockpile"] >= self.job_specific_data["max_carry_capacity"]:
                agent._set_action("return_with_wood", None)
            
            return {
                "agent": agent.name, 
                "action": "chopped_wood", 
                "amount": wood_amount,
                "total_carried": self.job_specific_data["wood_stockpile"]
            }
    
    def _progress_return_with_wood(self, agent, world, time_delta: float):
        """Return to village with harvested wood"""
        # Ideally would return to a storage building or lumber yard
        # For now, head home or to center of village
        target = agent.home_position
        
        if not target:
            # No home, go to center of map
            target = (world.width // 2, world.height // 2)
        
        current_x, current_y = agent.position
        target_x, target_y = target
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            # Deposit the wood in village storage
            wood_amount = self.job_specific_data["wood_stockpile"]
            
            # Add to village resources - in future, would add to specific storage
            # For now, just count it as deposited
            self.job_specific_data["wood_stockpile"] = 0.0
            
            agent.action_progress = 1.0
            return {
                "agent": agent.name, 
                "action": "deposited_wood", 
                "amount": wood_amount,
                "location": agent.position
            }
        
        # Move towards target
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent.action_progress = 1.0
        else:
            agent.action_progress = 0.5  # Still in progress
            
        return None
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling woodcutter-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # If carrying wood, drop it
        wood_carried = self.job_specific_data.get("wood_stockpile", 0.0)
        if wood_carried > 0:
            # In a more complete system, would drop wood at agent's location
            # For now, just lose it
            self.job_specific_data["wood_stockpile"] = 0.0
        
        # Call parent remove method
        super().remove_from_agent(agent) 