import random
from typing import Dict, List, Tuple, Any, Optional
import math
import pygame

from src.jobs.job import Job
from src.environment.resources import ResourceType

class BlacksmithJob(Job):
    """
    Blacksmith job class. Responsible for crafting tools, weapons, and processing raw materials.
    Manages metal refinement, tool crafting, and weapon production.
    """
    
    def __init__(self):
        """Initialize the blacksmith job with skill modifiers and job-specific data"""
        super().__init__("blacksmith", "Crafts tools, weapons, and metal items from raw materials")
        
        # Skill modifiers for this job
        self.skill_modifiers = {
            "crafting": 1.5,
            "strength": 1.2,
            "perception": 1.0
        }
        
        # Job-specific data
        self.job_specific_data = {
            "forge_position": None,         # Position of the blacksmith's forge
            "nearest_stockpile": None,      # Nearest stockpile for raw materials
            "nearest_armory": None,         # Nearest armory for finished products
            "crafting_progress": 0.0,       # Progress in current crafting task (0-100)
            "smelting_progress": 0.0,       # Progress in smelting ore (0-100)
            "current_recipe": None,         # Current recipe being crafted
            "items_crafted": {},            # Count of different item types crafted
            "resource_inventory": {         # Temporary inventory for crafting
                "wood": 0.0,
                "stone": 0.0,
                "iron_ore": 0.0,
                "copper_ore": 0.0,
                "iron_ingot": 0.0,
                "copper_ingot": 0.0
            },
            "product_inventory": {          # Inventory of created items
                "tools": 0,
                "weapons": 0
            },
            "max_carry_capacity": 30.0,     # Maximum weight of resources that can be carried
            "crafting_recipes": {           # Recipes for different items
                "iron_ingot": {"iron_ore": 2.0, "wood": 0.5},  # Smelting recipe
                "copper_ingot": {"copper_ore": 2.0, "wood": 0.5},  # Smelting recipe
                "tools": {"iron_ingot": 1.0, "wood": 2.0},  # Basic tools
                "weapons": {"iron_ingot": 2.0, "wood": 1.0}  # Basic weapons
            },
            "production_queue": [],         # Queue of items to produce
            "fatigue": 0.0                  # Fatigue level (0-100)
        }
    
    def decide_action(self, agent: Any, world: Any) -> str:
        """
        Decide the next action for the agent based on current situation.
        
        Args:
            agent: The agent performing the job
            world: The world environment
            
        Returns:
            The action to perform next
        """
        job_data = agent.job_data
        
        # Setup forge position if not set
        if job_data["forge_position"] is None:
            # Set forge near village center
            village_center = world.village_center
            # Offset slightly to avoid other buildings
            forge_x = village_center[0] + 5
            forge_y = village_center[1] - 3
            job_data["forge_position"] = (forge_x, forge_y)
        
        # Find the nearest stockpile if not known
        if job_data["nearest_stockpile"] is None:
            storage_facilities = world.storage_manager.get_facilities_by_type("Stockpile")
            if storage_facilities:
                agent_pos = agent.position
                closest_stockpile = min(storage_facilities, 
                                     key=lambda f: abs(f.position[0] - agent_pos[0]) + 
                                                 abs(f.position[1] - agent_pos[1]))
                job_data["nearest_stockpile"] = closest_stockpile
        
        # Find the nearest armory if not known
        if job_data["nearest_armory"] is None:
            armories = world.storage_manager.get_facilities_by_type("Armory")
            if armories:
                agent_pos = agent.position
                closest_armory = min(armories, 
                                   key=lambda f: abs(f.position[0] - agent_pos[0]) + 
                                               abs(f.position[1] - agent_pos[1]))
                job_data["nearest_armory"] = closest_armory
        
        # If fatigue is high, rest
        if job_data["fatigue"] > 80:
            return "rest"
        
        # If we have products to deliver, do that first
        if job_data["product_inventory"]["tools"] > 0 or job_data["product_inventory"]["weapons"] > 0:
            return "deliver_products"
        
        # If at forge, decide what to craft
        if agent.position == job_data["forge_position"]:
            # Update production queue if empty
            if not job_data["production_queue"]:
                self._update_production_queue(agent, world)
            
            # If we have a current recipe, continue crafting
            if job_data["current_recipe"]:
                return "craft_item"
            
            # Start a new recipe if we have one in queue and resources
            if job_data["production_queue"]:
                next_item = job_data["production_queue"][0]
                recipe = job_data["crafting_recipes"].get(next_item)
                
                if recipe and self._has_resources_for_recipe(job_data, recipe):
                    job_data["current_recipe"] = next_item
                    return "craft_item"
                else:
                    # Need more resources
                    return "get_resources"
            else:
                # No production needs
                return "rest"
        else:
            # Not at forge, go there
            return "go_to_forge"
    
    def progress_action(self, agent: Any, world: Any, time_delta: float):
        """
        Progress the current action forward.
        
        Args:
            agent: The agent performing the job
            world: The world environment
            time_delta: Time elapsed since last step
        """
        # Get the current action from the agent
        action_name = agent.current_action
        
        if action_name == "update_production_queue":
            self._update_production_queue(agent, world)
        elif action_name == "go_to_forge":
            self._progress_go_to_forge(agent, world)
        elif action_name == "get_resources":
            self._progress_get_resources(agent, world)
        elif action_name == "craft_item":
            self._progress_craft_item(agent, world)
        elif action_name == "deliver_products":
            self._progress_deliver_products(agent, world)
        elif action_name == "rest":
            self._progress_rest(agent, world)
    
    def _update_production_queue(self, agent: Any, world: Any):
        """
        Update the production queue based on village needs.
        
        Args:
            agent: The agent performing the job
            world: The world environment
        """
        job_data = agent.job_data
        
        # Check village storage for current levels
        village_tools = world.get_total_resource_amount("tools")
        village_weapons = world.get_total_resource_amount("weapons")
        
        # Check available ore
        available_iron_ore = world.get_total_resource_amount("iron_ore")
        available_copper_ore = world.get_total_resource_amount("copper_ore")
        
        # Clear current queue
        job_data["production_queue"] = []
        
        # Add ingots to queue if we have ore
        if available_iron_ore > 5:
            job_data["production_queue"].append("iron_ingot")
        
        if available_copper_ore > 5:
            job_data["production_queue"].append("copper_ingot")
        
        # Prioritize tools if low
        if village_tools < 10:
            # Add multiple tools to the queue
            tools_needed = max(0, 10 - int(village_tools))
            for _ in range(min(tools_needed, 3)):  # Cap at 3 to avoid too long queue
                job_data["production_queue"].append("tools")
        
        # Add weapons if needed (and tools are sufficient)
        if village_weapons < 5 and village_tools >= 5:
            # Add weapons to the queue
            weapons_needed = max(0, 5 - int(village_weapons))
            for _ in range(min(weapons_needed, 2)):  # Cap at 2
                job_data["production_queue"].append("weapons")
        
        # If no pressing needs, add some tools and weapons for stock
        if not job_data["production_queue"]:
            job_data["production_queue"].extend(["tools", "weapons"])
    
    def _has_resources_for_recipe(self, job_data: Dict, recipe: Dict) -> bool:
        """
        Check if we have enough resources for a recipe.
        
        Args:
            job_data: The job-specific data
            recipe: The recipe requirements
            
        Returns:
            True if all resources are available, False otherwise
        """
        for resource, amount in recipe.items():
            if job_data["resource_inventory"].get(resource, 0) < amount:
                return False
        return True
    
    def _progress_go_to_forge(self, agent: Any, world: Any):
        """Progress towards reaching the forge"""
        job_data = agent.job_data
        forge_pos = job_data["forge_position"]
        
        # Move toward forge
        self._move_toward_position(agent, world, forge_pos)
        
        # Slight fatigue from walking
        job_data["fatigue"] += 0.2
    
    def _progress_get_resources(self, agent: Any, world: Any):
        """Gather resources needed for crafting"""
        job_data = agent.job_data
        
        # If we're not at the stockpile, go there
        if job_data["nearest_stockpile"]:
            stockpile = job_data["nearest_stockpile"]
            stockpile_pos = stockpile.position
            
            # If not at stockpile, move towards it
            if agent.position != stockpile_pos and (
                abs(agent.position[0] - stockpile_pos[0]) > 1 or 
                abs(agent.position[1] - stockpile_pos[1]) > 1):
                
                self._move_toward_position(agent, world, stockpile_pos)
                return
            
            # At stockpile, determine what we need
            needed_resources = {}
            
            # Check production queue
            if job_data["production_queue"]:
                next_item = job_data["production_queue"][0]
                recipe = job_data["crafting_recipes"].get(next_item)
                
                if recipe:
                    for resource, amount in recipe.items():
                        current_amount = job_data["resource_inventory"].get(resource, 0)
                        if current_amount < amount:
                            needed_resources[resource] = amount - current_amount
            
            # Try to take resources from stockpile
            for resource, amount in needed_resources.items():
                # Try to take from stockpile
                taken = stockpile.remove_resource(resource, amount)
                
                # If stockpile doesn't have enough, try village storage
                if taken < amount:
                    remaining = amount - taken
                    taken_from_village = world.resource_manager.take_from_village_storage(resource, remaining)
                    taken += taken_from_village
                
                # Update inventory
                if taken > 0:
                    job_data["resource_inventory"][resource] = job_data["resource_inventory"].get(resource, 0) + taken
            
            # Return to forge with resources
            agent.current_action = "go_to_forge"
        else:
            # No stockpile, try to get directly from village storage
            if job_data["production_queue"]:
                next_item = job_data["production_queue"][0]
                recipe = job_data["crafting_recipes"].get(next_item)
                
                if recipe:
                    for resource, amount in recipe.items():
                        current_amount = job_data["resource_inventory"].get(resource, 0)
                        if current_amount < amount:
                            needed = amount - current_amount
                            taken = world.resource_manager.take_from_village_storage(resource, needed)
                            job_data["resource_inventory"][resource] = current_amount + taken
            
            # Return to forge
            agent.current_action = "go_to_forge"
    
    def _progress_craft_item(self, agent: Any, world: Any):
        """
        Progress in crafting the current item.
        """
        job_data = agent.job_data
        current_recipe = job_data["current_recipe"]
        
        # Ensure we have a recipe
        if not current_recipe:
            # No recipe, update queue and decide what to do
            self._update_production_queue(agent, world)
            agent.current_action = "get_resources"
            return
        
        # Check if we're at the forge
        if agent.position != job_data["forge_position"]:
            agent.current_action = "go_to_forge"
            return
        
        # Get recipe for current item
        recipe = job_data["crafting_recipes"].get(current_recipe)
        if not recipe:
            # Invalid recipe
            job_data["current_recipe"] = None
            if job_data["production_queue"] and job_data["production_queue"][0] == current_recipe:
                job_data["production_queue"].pop(0)
            return
        
        # Check if we have all resources
        if not self._has_resources_for_recipe(job_data, recipe):
            # Need more resources
            agent.current_action = "get_resources"
            return
        
        # Progress crafting based on type
        crafting_skill = agent.skills.get("crafting", 0)
        strength_skill = agent.skills.get("strength", 0)
        
        # Different progression rates for different items
        if current_recipe in ["iron_ingot", "copper_ingot"]:
            # Smelting progress
            progress_rate = 2.0 + (crafting_skill * 0.3) + (strength_skill * 0.2)
            job_data["smelting_progress"] += progress_rate
            
            # Increase fatigue from working forge
            job_data["fatigue"] += 1.0
            
            # If smelting is complete
            if job_data["smelting_progress"] >= 100:
                # Consume resources
                for resource, amount in recipe.items():
                    job_data["resource_inventory"][resource] -= amount
                
                # Add the ingot to inventory
                job_data["resource_inventory"][current_recipe] = job_data["resource_inventory"].get(current_recipe, 0) + 1
                
                # Reset progress and update queue
                job_data["smelting_progress"] = 0
                job_data["current_recipe"] = None
                if job_data["production_queue"] and job_data["production_queue"][0] == current_recipe:
                    job_data["production_queue"].pop(0)
        else:
            # Crafting tools or weapons
            progress_rate = 1.5 + (crafting_skill * 0.4) + (strength_skill * 0.1)
            job_data["crafting_progress"] += progress_rate
            
            # Increase fatigue from crafting
            job_data["fatigue"] += 1.2
            
            # If crafting is complete
            if job_data["crafting_progress"] >= 100:
                # Consume resources
                for resource, amount in recipe.items():
                    job_data["resource_inventory"][resource] -= amount
                
                # Add the product to inventory
                job_data["product_inventory"][current_recipe] = job_data["product_inventory"].get(current_recipe, 0) + 1
                
                # Update crafting statistics
                job_data["items_crafted"][current_recipe] = job_data["items_crafted"].get(current_recipe, 0) + 1
                
                # Reset progress and update queue
                job_data["crafting_progress"] = 0
                job_data["current_recipe"] = None
                if job_data["production_queue"] and job_data["production_queue"][0] == current_recipe:
                    job_data["production_queue"].pop(0)
                
                # If we've crafted items, deliver them
                if job_data["product_inventory"]["tools"] > 0 or job_data["product_inventory"]["weapons"] > 0:
                    agent.current_action = "deliver_products"
    
    def _progress_deliver_products(self, agent: Any, world: Any):
        """Deliver crafted products to storage"""
        job_data = agent.job_data
        
        # If we have an armory, deliver weapons and tools there
        if job_data["nearest_armory"]:
            armory = job_data["nearest_armory"]
            armory_pos = armory.position
            
            # If not at armory, move towards it
            if agent.position != armory_pos and (
                abs(agent.position[0] - armory_pos[0]) > 1 or 
                abs(agent.position[1] - armory_pos[1]) > 1):
                
                self._move_toward_position(agent, world, armory_pos)
                return
            
            # At armory, deposit products
            # Deliver tools
            if job_data["product_inventory"]["tools"] > 0:
                tools_amount = job_data["product_inventory"]["tools"]
                added = armory.add_resource("tools", tools_amount)
                
                # If not all added, put in village storage
                if added < tools_amount:
                    remaining = tools_amount - added
                    world.resource_manager.add_to_village_storage("tools", remaining)
                
                job_data["product_inventory"]["tools"] = 0
            
            # Deliver weapons
            if job_data["product_inventory"]["weapons"] > 0:
                weapons_amount = job_data["product_inventory"]["weapons"]
                added = armory.add_resource("weapons", weapons_amount)
                
                # If not all added, put in village storage
                if added < weapons_amount:
                    remaining = weapons_amount - added
                    world.resource_manager.add_to_village_storage("weapons", remaining)
                
                job_data["product_inventory"]["weapons"] = 0
                
            # Return to forge
            agent.current_action = "go_to_forge"
        else:
            # No armory, deliver directly to village storage
            if job_data["product_inventory"]["tools"] > 0:
                world.resource_manager.add_to_village_storage("tools", job_data["product_inventory"]["tools"])
                job_data["product_inventory"]["tools"] = 0
                
            if job_data["product_inventory"]["weapons"] > 0:
                world.resource_manager.add_to_village_storage("weapons", job_data["product_inventory"]["weapons"])
                job_data["product_inventory"]["weapons"] = 0
                
            # Return to forge
            agent.current_action = "go_to_forge"
    
    def _progress_rest(self, agent: Any, world: Any):
        """Rest to reduce fatigue"""
        job_data = agent.job_data
        
        # Reduce fatigue
        fatigue_reduction = 5 + agent.skills.get("endurance", 0) * 0.5
        job_data["fatigue"] = max(0, job_data["fatigue"] - fatigue_reduction)
        
        # If rested enough, go back to work
        if job_data["fatigue"] < 30:
            # Check if we're at forge
            if agent.position == job_data["forge_position"]:
                # Update production queue and continue crafting
                self._update_production_queue(agent, world)
                agent.current_action = "craft_item"
            else:
                agent.current_action = "go_to_forge"
        else:
            # Simple implementation - just idle and occasionally move around
            if random.random() < 0.2:  # 20% chance to move each tick when resting
                # Get neighboring cells
                neighbors = world.get_neighboring_cells(agent.position[0], agent.position[1])
                if neighbors:
                    # Move to a random neighboring cell
                    new_pos = random.choice(neighbors)
                    world.move_agent(agent, new_pos[0], new_pos[1])
    
    def _move_toward_position(self, agent: Any, world: Any, target_pos: Tuple[int, int]):
        """
        Move the agent toward a target position.
        
        Args:
            agent: The agent to move
            world: The world environment
            target_pos: The position to move toward
        """
        # Simple pathfinding - move toward target
        current_x, current_y = agent.position
        target_x, target_y = target_pos
        
        # Calculate direction to move (simplified)
        dx = 0
        dy = 0
        
        if current_x < target_x:
            dx = 1
        elif current_x > target_x:
            dx = -1
            
        if current_y < target_y:
            dy = 1
        elif current_y > target_y:
            dy = -1
        
        # Attempt to move (first try diagonal, then cardinal directions)
        if dx != 0 and dy != 0:
            # Try diagonal move
            new_x, new_y = current_x + dx, current_y + dy
            
            # Check if position is valid and not occupied
            entities = world.get_entities_at(new_x, new_y)
            if any(entity != agent and hasattr(entity, 'blocks_movement') and entity.blocks_movement 
                  for entity in entities):
                # If diagonal blocked, try cardinal directions
                if world.move_agent(agent, current_x + dx, current_y):
                    pass  # Moved horizontally
                elif world.move_agent(agent, current_x, current_y + dy):
                    pass  # Moved vertically
            else:
                world.move_agent(agent, new_x, new_y)  # Moved diagonally
        
        elif dx != 0:
            # Try horizontal move
            world.move_agent(agent, current_x + dx, current_y)
        elif dy != 0:
            # Try vertical move
            world.move_agent(agent, current_x, current_y + dy)
    
    def remove_from_agent(self, agent: Any):
        """
        Handle cleanup when job is removed from an agent.
        
        Args:
            agent: The agent to remove this job from
        """
        job_data = agent.job_data
        
        # If we have any resources in inventory, return them to storage
        if hasattr(agent, "world") and agent.world:
            world = agent.world
            
            # Return raw materials
            for resource, amount in job_data["resource_inventory"].items():
                if amount > 0:
                    world.resource_manager.add_to_village_storage(resource, amount)
            
            # Return finished products
            for product, amount in job_data["product_inventory"].items():
                if amount > 0:
                    world.resource_manager.add_to_village_storage(product, amount)
        
        super().remove_from_agent(agent) 