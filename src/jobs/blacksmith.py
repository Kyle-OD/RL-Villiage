import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class BlacksmithJob(Job):
    """
    Blacksmith job responsible for processing raw materials into tools and equipment.
    Blacksmiths smelt ore, forge tools, and repair equipment.
    """
    
    def __init__(self):
        """Initialize the blacksmith job with appropriate skills and data"""
        super().__init__("blacksmith", "Processes raw materials into tools and equipment")
        
        # Set skill modifiers - blacksmiths get bonuses to these skills
        self.skill_modifiers = {
            "crafting": 0.6,     # Major boost to crafting
            "strength": 0.3,     # Moderate boost to strength
            "building": 0.2      # Minor boost to building
        }
        
        # Job-specific data
        self.job_specific_data = {
            "forge_position": None,  # Location of the forge/smithy
            "current_project": None,  # Current item being crafted (type, progress)
            "projects_completed": {},  # Type -> count of items created
            "forge_fuel": 0.0      # Current fuel in the forge
        }
        
        # Tool/equipment types and their requirements
        self.crafting_recipes = {
            "basic_tools": {
                "iron": 5.0,
                "wood": 2.0,
                "time": 1.0,
                "skill_factor": "crafting"
            },
            "weapons": {
                "iron": 8.0,
                "wood": 3.0,
                "time": 1.5,
                "skill_factor": "crafting"
            },
            "advanced_tools": {
                "iron": 10.0,
                "wood": 5.0,
                "time": 2.0,
                "skill_factor": "crafting"
            },
            "iron_ingot": {
                "iron_ore": 2.0,
                "wood": 0.5,  # Fuel
                "time": 0.5,
                "skill_factor": "crafting"
            }
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next smithing action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Check if we have a forge position
        if not self.job_specific_data["forge_position"]:
            # For now, just use the agent's home or center of village
            if agent.home_position:
                self.job_specific_data["forge_position"] = agent.home_position
            else:
                self.job_specific_data["forge_position"] = (world.width // 2, world.height // 2)
        
        # Check if we're at the forge
        forge_pos = self.job_specific_data["forge_position"]
        if agent.position != forge_pos:
            # Go to forge
            agent._set_action("go_to_forge", forge_pos)
            return
        
        # At the forge, decide what to work on
        if self.job_specific_data["current_project"]:
            # Continue working on current project
            project_type, progress = self.job_specific_data["current_project"]
            agent._set_action("craft_item", project_type)
            return
        
        # No current project, decide what to make
        # First check forge fuel
        if self.job_specific_data["forge_fuel"] < 10.0:
            # Need to add fuel to the forge
            agent._set_action("fuel_forge", None)
            return
        
        # Check village resources to see what we can make
        resources = world.resource_manager.get_village_resources()
        
        # Prioritize making iron ingots if we have ore
        iron_ore = resources.get(ResourceType.IRON_ORE, 0.0)
        wood = resources.get(ResourceType.WOOD, 0.0)
        
        if iron_ore >= self.crafting_recipes["iron_ingot"]["iron_ore"] and wood >= self.crafting_recipes["iron_ingot"]["wood"]:
            # Smelt iron ore into ingots
            self.job_specific_data["current_project"] = ("iron_ingot", 0.0)
            agent._set_action("craft_item", "iron_ingot")
            return
        
        # Check if we have iron ingots to make tools
        iron = resources.get(ResourceType.IRON_INGOT, 0.0)
        if iron >= self.crafting_recipes["basic_tools"]["iron"] and wood >= self.crafting_recipes["basic_tools"]["wood"]:
            # Make basic tools
            self.job_specific_data["current_project"] = ("basic_tools", 0.0)
            agent._set_action("craft_item", "basic_tools")
            return
        
        # Not enough resources, wait for materials
        agent._set_action("wait_for_materials", None)
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a blacksmithing action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "go_to_forge":
            return self._progress_go_to_forge(agent, world, time_delta)
        elif action == "fuel_forge":
            return self._progress_fuel_forge(agent, world, time_delta)
        elif action == "craft_item":
            return self._progress_craft_item(agent, world, time_delta)
        elif action == "wait_for_materials":
            return self._progress_wait_for_materials(agent, world, time_delta)
        
        return None
    
    def _progress_go_to_forge(self, agent, world, time_delta: float):
        """Go to the forge/smithy"""
        forge_pos = agent.action_target
        if not forge_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = forge_pos
        
        # Already at forge
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_forge", "location": forge_pos}
        
        # Move towards forge
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
    
    def _progress_fuel_forge(self, agent, world, time_delta: float):
        """Add fuel to the forge"""
        # Check if we're at the forge
        forge_pos = self.job_specific_data["forge_position"]
        if agent.position != forge_pos:
            agent._set_action("go_to_forge", forge_pos)
            return None
        
        # Check for available wood in village resources
        resources = world.resource_manager.get_village_resources()
        wood = resources.get(ResourceType.WOOD, 0.0)
        
        if wood < 5.0:  # Minimum wood needed
            # Not enough wood
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "forge_fuel_failed", "reason": "not_enough_wood"}
        
        # Add fuel
        if agent.action_progress < 0.9:
            # Still adding fuel
            progress_amount = 0.2 + agent.skills["crafting"] * 0.1
            agent.action_progress += progress_amount
            
            return None
        else:
            # Fueling complete
            agent.action_progress = 1.0
            
            # Take wood from village resources
            fuel_added = min(wood, 20.0)  # Add up to 20 units of fuel
            world.resource_manager.take_from_village_storage(ResourceType.WOOD, fuel_added)
            
            # Add to forge fuel
            self.job_specific_data["forge_fuel"] += fuel_added
            
            return {
                "agent": agent.name, 
                "action": "forge_fueled", 
                "amount": fuel_added,
                "total_fuel": self.job_specific_data["forge_fuel"]
            }
    
    def _progress_craft_item(self, agent, world, time_delta: float):
        """Craft an item at the forge"""
        # Check if we're at the forge
        forge_pos = self.job_specific_data["forge_position"]
        if agent.position != forge_pos:
            agent._set_action("go_to_forge", forge_pos)
            return None
        
        # Get the item type being crafted
        item_type = agent.action_target
        if not item_type or item_type not in self.crafting_recipes:
            # Invalid item type
            self.job_specific_data["current_project"] = None
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "crafting_failed", "reason": "invalid_item"}
        
        # Check if we have enough resources to craft
        resources = world.resource_manager.get_village_resources()
        recipe = self.crafting_recipes[item_type]
        
        # Check for each required resource
        for resource_name, amount in recipe.items():
            if resource_name in ["time", "skill_factor"]:
                continue  # Skip non-material requirements
                
            resource_type = self._resource_name_to_type(resource_name)
            available = resources.get(resource_type, 0.0)
            
            if available < amount:
                # Not enough resources
                self.job_specific_data["current_project"] = None
                agent.action_progress = 1.0
                return {
                    "agent": agent.name, 
                    "action": "crafting_failed", 
                    "reason": f"not_enough_{resource_name}",
                    "item_type": item_type
                }
        
        # Check forge fuel
        if item_type != "iron_ingot" and self.job_specific_data["forge_fuel"] < 1.0:
            # Need more fuel
            self.job_specific_data["current_project"] = None
            agent._set_action("fuel_forge", None)
            return {"agent": agent.name, "action": "need_more_fuel"}
        
        # Continue crafting
        if agent.action_progress < 0.95:
            # Still crafting
            skill_name = recipe.get("skill_factor", "crafting")
            skill_level = agent.skills[skill_name]
            
            # Time factor - higher skill = faster crafting
            time_factor = recipe.get("time", 1.0)
            progress_amount = (0.1 / time_factor) + (skill_level * 0.1)
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "crafting", 0.008)
            
            # Use up some fuel
            if item_type != "iron_ingot":
                self.job_specific_data["forge_fuel"] -= 0.1
            
            return None
        else:
            # Crafting complete
            agent.action_progress = 1.0
            
            # Consume resources
            for resource_name, amount in recipe.items():
                if resource_name in ["time", "skill_factor"]:
                    continue  # Skip non-material requirements
                    
                resource_type = self._resource_name_to_type(resource_name)
                world.resource_manager.take_from_village_storage(resource_type, amount)
            
            # Add crafted item to village resources
            output_type = self._output_type_for_item(item_type)
            quality = 1.0 + (agent.skills["crafting"] * 0.5)  # Quality based on skill (1.0-1.5)
            
            # Store project completion
            if item_type not in self.job_specific_data["projects_completed"]:
                self.job_specific_data["projects_completed"][item_type] = 0
            self.job_specific_data["projects_completed"][item_type] += 1
            
            # Clear current project
            self.job_specific_data["current_project"] = None
            
            # Add item to village resources
            world.resource_manager.add_to_village_storage(output_type, quality)
            
            return {
                "agent": agent.name, 
                "action": "crafted_item", 
                "item_type": item_type,
                "quality": quality
            }
    
    def _progress_wait_for_materials(self, agent, world, time_delta: float):
        """Wait for materials to become available"""
        # Just wait a bit, then try again
        if agent.action_progress < 1.0:
            agent.action_progress += 0.2
            return None
        else:
            # Done waiting, check again
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "waiting_complete"}
    
    def _resource_name_to_type(self, resource_name: str) -> ResourceType:
        """Convert recipe resource name to ResourceType"""
        if resource_name == "iron":
            return ResourceType.IRON_INGOT
        elif resource_name == "iron_ore":
            return ResourceType.IRON_ORE
        elif resource_name == "wood":
            return ResourceType.WOOD
        elif resource_name == "stone":
            return ResourceType.STONE
        else:
            return ResourceType.IRON_INGOT  # Default
    
    def _output_type_for_item(self, item_type: str) -> ResourceType:
        """Get the output ResourceType for a crafted item"""
        if item_type == "iron_ingot":
            return ResourceType.IRON_INGOT
        elif item_type == "basic_tools":
            return ResourceType.BASIC_TOOLS
        elif item_type == "weapons":
            return ResourceType.WEAPONS
        elif item_type == "advanced_tools":
            return ResourceType.ADVANCED_TOOLS
        else:
            return ResourceType.IRON_INGOT  # Default
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling blacksmith-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # Clear current project
        self.job_specific_data["current_project"] = None
        
        # Call parent remove method
        super().remove_from_agent(agent) 