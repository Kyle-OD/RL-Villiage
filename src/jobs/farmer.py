import random
from typing import Dict, List, Tuple, Any, Optional
import pygame
import math

from src.jobs.job import Job
from src.environment.resources import ResourceType

class FarmerJob(Job):
    """
    The Farmer job specializes in growing and harvesting food resources.
    Farmers manage fields, plant crops, and harvest them when ready.
    """
    
    def __init__(self):
        """Initialize the Farmer job"""
        super().__init__(
            name="farmer",
            description="Grows and harvests crops to provide food for the village."
        )
        
        # Set skill modifiers for this job
        self.skill_modifiers = {
            "farming": 1.5,
            "endurance": 1.2,
            "perception": 1.0
        }
        
        # Job-specific data
        self.job_specific_data = {
            "crop_fields": [],            # List of fields the farmer manages
            "current_field_index": 0,     # Index of the current field being worked
            "planting_progress": 0.0,     # Progress in planting (0-100)
            "tending_progress": 0.0,      # Progress in tending (0-100)
            "harvesting_progress": 0.0,   # Progress in harvesting (0-100)
            "crop_growth_stages": {},     # Dict mapping field to growth stage
            "food_harvested": 0.0,        # Amount of food harvested so far
            "nearest_granary": None,      # Nearest granary for storing food
            "carrying_food": 0.0,         # Amount of food currently carrying
            "max_carry_capacity": 20.0,   # Max amount the farmer can carry
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next farming action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Get the current season
        season = world.time_system.get_season()
        
        # Check if agent has a field assigned
        if not self.job_specific_data["crop_fields"]:
            # No fields available, wander and rest
            return "rest"
        
        # Get current field
        current_field_idx = self.job_specific_data["current_field_index"]
        if current_field_idx >= len(self.job_specific_data["crop_fields"]):
            current_field_idx = 0
            self.job_specific_data["current_field_index"] = 0
        
        current_field = self.job_specific_data["crop_fields"][current_field_idx]
        
        # Check crop growth stage
        growth_stage = self.job_specific_data["crop_growth_stages"].get(str(current_field), "unplanted")
        
        # Prioritize actions based on crop stage
        if growth_stage == "unplanted":
            if agent.position != current_field:
                return "go_to_field"
            else:
                return "plant_crops"
        elif growth_stage == "growing":
            if agent.position != current_field:
                return "go_to_field"
            else:
                return "tend_crops"
        elif growth_stage == "ready_to_harvest":
            if agent.position != current_field:
                return "go_to_field"
            else:
                return "harvest_crops"
        else:
            # Move to next field if current one is harvested
            self.job_specific_data["current_field_index"] = (current_field_idx + 1) % len(self.job_specific_data["crop_fields"])
            return "go_to_field"
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a farming action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "go_to_field":
            return self._progress_go_to_field(agent, world, time_delta)
        elif action == "plant_crops":
            return self._progress_plant_crops(agent, world, time_delta)
        elif action == "tend_crops":
            return self._progress_tend_crops(agent, world, time_delta)
        elif action == "harvest_crops":
            return self._progress_harvest_crops(agent, world, time_delta)
        elif action == "deliver_to_granary":
            return self._progress_deliver_to_granary(agent, world, time_delta)
        elif action == "rest":
            return self._progress_rest(agent, world, time_delta)
        
        return None
    
    def _progress_go_to_field(self, agent, world, time_delta: float):
        """Go to the assigned field"""
        # Similar to agent's go_home but with field as target
        job_data = agent.job_data
        
        if not job_data["crop_fields"]:
            return None
            
        current_field_idx = job_data["current_field_index"]
        if current_field_idx >= len(job_data["crop_fields"]):
            current_field_idx = 0
            job_data["current_field_index"] = 0
            
        target_field = job_data["crop_fields"][current_field_idx]
        
        # Simple pathfinding - move toward target
        self._move_toward_position(agent, world, target_field)
        
        # Check if we've reached the field
        if agent.position == target_field:
            # Update action based on field state
            growth_stage = job_data["crop_growth_stages"].get(str(target_field), "unplanted")
            if growth_stage == "unplanted":
                agent.current_action = "plant_crops"
            elif growth_stage == "growing":
                agent.current_action = "tend_crops"
            elif growth_stage == "ready_to_harvest":
                agent.current_action = "harvest_crops"
    
    def _progress_plant_crops(self, agent, world, time_delta: float):
        """Plant a crop in the field"""
        # Check if we're at the field
        job_data = agent.job_data
        
        # Get current field
        current_field_idx = job_data["current_field_index"]
        current_field = job_data["crop_fields"][current_field_idx]
        
        # Increase planting progress based on farming skill
        farming_skill = agent.skills.get("farming", 0)
        job_data["planting_progress"] += 5 + (farming_skill * 0.5)
        
        # If planting is complete
        if job_data["planting_progress"] >= 100:
            # Mark as planted and reset progress
            job_data["crop_growth_stages"][str(current_field)] = "growing"
            job_data["planting_progress"] = 0
            
            # Move to next field
            job_data["current_field_index"] = (current_field_idx + 1) % len(job_data["crop_fields"])
            agent.current_action = "go_to_field"
            
            # Animation or visual feedback
            # Here we could add visual indicators of planting
    
    def _progress_tend_crops(self, agent, world, time_delta: float):
        """Tend to a growing crop"""
        # Check if we're at the field
        job_data = agent.job_data
        
        # Get current field
        current_field_idx = job_data["current_field_index"]
        current_field = job_data["crop_fields"][current_field_idx]
        
        # Increase tending progress based on farming skill
        farming_skill = agent.skills.get("farming", 0)
        job_data["tending_progress"] += 3 + (farming_skill * 0.3)
        
        # Advance crop growth based on tending - this is simplified
        if job_data["tending_progress"] >= 100:
            # Crop advances to ready to harvest after sufficient tending
            job_data["crop_growth_stages"][str(current_field)] = "ready_to_harvest"
            job_data["tending_progress"] = 0
            
            # Move to next field
            job_data["current_field_index"] = (current_field_idx + 1) % len(job_data["crop_fields"])
            agent.current_action = "go_to_field"
    
    def _progress_harvest_crops(self, agent, world, time_delta: float):
        """Harvest a mature crop"""
        # Check if we're at the field
        job_data = agent.job_data
        
        # Get current field
        current_field_idx = job_data["current_field_index"]
        current_field = job_data["crop_fields"][current_field_idx]
        
        # Increase harvesting progress based on farming skill
        farming_skill = agent.skills.get("farming", 0)
        job_data["harvesting_progress"] += 4 + (farming_skill * 0.4)
        
        # If harvesting is complete
        if job_data["harvesting_progress"] >= 100:
            # Calculate harvest yield based on farming skill and apply any modifiers
            base_yield = random.uniform(10, 15)
            skill_bonus = farming_skill * 0.2
            total_yield = base_yield + skill_bonus
            
            # Add to carrying amount
            job_data["carrying_food"] += total_yield
            job_data["food_harvested"] += total_yield
            
            # Mark field as harvested
            job_data["crop_growth_stages"][str(current_field)] = "harvested"
            job_data["harvesting_progress"] = 0
            
            # If carrying capacity reached, deliver to storage
            if job_data["carrying_food"] >= job_data["max_carry_capacity"]:
                agent.current_action = "deliver_to_granary"
            else:
                # Move to next field
                job_data["current_field_index"] = (current_field_idx + 1) % len(job_data["crop_fields"])
                agent.current_action = "go_to_field"
    
    def _progress_deliver_to_granary(self, agent, world, time_delta: float):
        """Progress towards delivering harvested food to a granary"""
        job_data = agent.job_data
        
        # If we don't have a granary, try to find one
        if job_data["nearest_granary"] is None:
            storage_facilities = world.storage_manager.get_facilities_by_type("Granary")
            if storage_facilities:
                # Find the closest granary
                agent_pos = agent.position
                closest_granary = min(storage_facilities, 
                                    key=lambda f: abs(f.position[0] - agent_pos[0]) + 
                                                abs(f.position[1] - agent_pos[1]))
                job_data["nearest_granary"] = closest_granary
        
        # If we have a granary, move toward it
        if job_data["nearest_granary"]:
            granary = job_data["nearest_granary"]
            granary_pos = granary.position
            
            # Move toward granary
            self._move_toward_position(agent, world, granary_pos)
            
            # If we reached the granary, deposit food
            if agent.position == granary_pos or (
                abs(agent.position[0] - granary_pos[0]) <= 1 and 
                abs(agent.position[1] - granary_pos[1]) <= 1):
                
                # Store the food in the granary
                food_amount = job_data["carrying_food"]
                # Assuming food is stored as "food" resource type - adjust as needed
                added_amount = granary.add_resource("food", food_amount)
                
                # If not all food was added to the granary (it might be full)
                if added_amount < food_amount:
                    # Add remainder to village storage
                    remaining = food_amount - added_amount
                    world.resource_manager.add_to_village_storage("food", remaining)
                
                # Reset carrying amount
                job_data["carrying_food"] = 0.0
                
                # Go back to field work
                agent.current_action = "go_to_field"
        else:
            # No granary found, add to village storage directly
            world.resource_manager.add_to_village_storage("food", job_data["carrying_food"])
            job_data["carrying_food"] = 0.0
            agent.current_action = "go_to_field"
    
    def _progress_rest(self, agent, world, time_delta: float):
        """Rest when no other tasks are available"""
        # Simple implementation - just idle and occasionally move around
        if random.random() < 0.2:  # 20% chance to move each tick when resting
            # Get neighboring cells
            neighbors = world.get_neighboring_cells(agent.position[0], agent.position[1])
            if neighbors:
                # Move to a random neighboring cell
                new_pos = random.choice(neighbors)
                world.move_agent(agent, new_pos[0], new_pos[1])
    
    def _move_toward_position(self, agent, world, target_pos: Tuple[int, int]):
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
    
    def update_crops(self, world):
        """
        Update all planted crops - called by the world on each step.
        
        Args:
            world: Reference to the world
        """
        # Get season modifier for growth
        season = world.time_system.get_season()
        season_modifier = {
            "spring": 1.2,
            "summer": 1.5,
            "autumn": 0.8,
            "winter": 0.2
        }.get(season, 1.0)
        
        # Get weather modifier
        weather = world.time_system.get_weather()
        weather_modifier = {
            "clear": 1.0,
            "rain": 1.3,
            "fog": 0.8,
            "storm": 0.6,
            "snow": 0.1
        }.get(weather, 1.0)
        
        # Update each planted crop
        for field_key, crop_data in list(self.job_specific_data["crop_growth_stages"].items()):
            if crop_data == "growing":
                # Get the field position
                field_pos = tuple(map(int, field_key.split(',')))
                
                # Growth rate depends on crop type
                base_growth_rate = {
                    "wheat": 0.01,
                    "corn": 0.008
                }.get(field_pos[2], 0.01)
                
                # Apply modifiers
                growth_rate = base_growth_rate * season_modifier * weather_modifier
                
                # Update growth
                new_growth = min(1.0, self.job_specific_data["tending_progress"] / 100 + growth_rate)
                
                # Update crop data
                self.job_specific_data["crop_growth_stages"][field_key] = new_growth
                
                # Check if crop is ready to harvest
                if new_growth >= 1.0:
                    self.job_specific_data["crop_growth_stages"][field_key] = "ready_to_harvest"
                    self.job_specific_data["tending_progress"] = 0
                    self.job_specific_data["harvesting_progress"] = 0
                    self.job_specific_data["carrying_food"] = 0
                    self.job_specific_data["food_harvested"] += 20  # Assuming a default harvest amount
                    self.job_specific_data["crop_growth_stages"][field_key] = "harvested"
                    world.resource_manager.add_to_village_storage("food", 20)
            elif crop_data == "ready_to_harvest":
                # Check if crop is ready to harvest
                if self.job_specific_data["harvesting_progress"] >= 100:
                    self.job_specific_data["crop_growth_stages"][field_key] = "harvested"
                    self.job_specific_data["harvesting_progress"] = 0
                    self.job_specific_data["carrying_food"] = 0
                    self.job_specific_data["food_harvested"] += 20  # Assuming a default harvest amount
                    world.resource_manager.add_to_village_storage("food", 20)
            elif crop_data == "harvested":
                # Remove harvested crop from growth stages
                self.job_specific_data["crop_growth_stages"].pop(field_key)

    def remove_from_agent(self, agent):
        """
        Handle cleanup when job is removed from an agent.
        
        Args:
            agent: The agent to remove this job from
        """
        # Deliver any carried food to storage
        job_data = agent.job_data
        if job_data.get("carrying_food", 0) > 0:
            # Try to find the world object through the agent
            if hasattr(agent, "world") and agent.world:
                agent.world.resource_manager.add_to_village_storage("food", job_data["carrying_food"])
        
        super().remove_from_agent(agent) 