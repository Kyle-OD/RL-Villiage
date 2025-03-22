import random
from typing import Dict, List, Optional, Any

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
            name="Farmer",
            description="Grows and harvests crops to provide food for the village."
        )
        
        # Set skill modifiers for this job
        self.skill_modifiers = {
            "farming": 0.5,      # 50% boost to farming skill
            "woodcutting": 0.2,  # 20% boost to woodcutting (for clearing fields)
            "cooking": 0.2       # 20% boost to cooking (for food preparation)
        }
        
        # Job-specific data
        self.job_specific_data = {
            "known_fields": [],  # List of known farming locations
            "current_field": None,  # Currently assigned field
            "planted_crops": {}  # Position -> (crop_type, growth_stage, plant_time)
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
        if not self.job_specific_data["current_field"]:
            # Find a field to work on
            agent._set_action("find_field", None)
            return
        
        # Check if agent is at their assigned field
        field_pos = self.job_specific_data["current_field"]
        if agent.position != field_pos:
            # Go to field
            agent._set_action("go_to_field", field_pos)
            return
        
        # At the field, decide what to do based on season and crop state
        field_key = f"{field_pos[0]},{field_pos[1]}"
        if field_key in self.job_specific_data["planted_crops"]:
            # Field has a crop
            crop_data = self.job_specific_data["planted_crops"][field_key]
            crop_type, growth_stage, plant_time = crop_data
            
            # Check if crop is ready to harvest (growth_stage >= 1.0)
            if growth_stage >= 1.0:
                agent._set_action("harvest_crop", field_pos)
            else:
                # Tend to the crop
                agent._set_action("tend_crop", field_pos)
        else:
            # Field has no crop
            if season in ["spring", "summer"]:
                # Good seasons for planting
                agent._set_action("plant_crop", field_pos)
            else:
                # Off-season, prepare the field
                agent._set_action("prepare_field", field_pos)
    
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
        
        if action == "find_field":
            return self._progress_find_field(agent, world, time_delta)
        elif action == "go_to_field":
            return self._progress_go_to_field(agent, world, time_delta)
        elif action == "plant_crop":
            return self._progress_plant_crop(agent, world, time_delta)
        elif action == "tend_crop":
            return self._progress_tend_crop(agent, world, time_delta)
        elif action == "harvest_crop":
            return self._progress_harvest_crop(agent, world, time_delta)
        elif action == "prepare_field":
            return self._progress_prepare_field(agent, world, time_delta)
        
        return None
    
    def _progress_find_field(self, agent, world, time_delta: float):
        """Find a field to work on"""
        # If we already know fields, pick one
        if self.job_specific_data["known_fields"]:
            # Assign a known field
            field_pos = random.choice(self.job_specific_data["known_fields"])
            self.job_specific_data["current_field"] = field_pos
            agent._set_action("go_to_field", field_pos)
            return {"agent": agent.name, "action": "assigned_field", "location": field_pos}
        
        # Look for potential farming spots nearby
        x, y = agent.position
        neighbors = world.get_neighboring_cells(x, y, 3)
        
        # Check for suitable locations
        potential_fields = []
        for nx, ny in neighbors:
            resources = world.resource_manager.get_resources_at(nx, ny)
            
            # Farmland is good near water but not on resource nodes
            has_water_nearby = any(
                r.resource_type == ResourceType.WATER 
                for cx, cy in world.get_neighboring_cells(nx, ny, 2)
                for r in world.resource_manager.get_resources_at(cx, cy)
            )
            
            # Good place if near water but not on existing resources
            if has_water_nearby and not resources:
                potential_fields.append((nx, ny))
        
        if potential_fields:
            # Found a good field
            field_pos = random.choice(potential_fields)
            self.job_specific_data["known_fields"].append(field_pos)
            self.job_specific_data["current_field"] = field_pos
            agent._set_action("go_to_field", field_pos)
            return {"agent": agent.name, "action": "found_field", "location": field_pos}
        
        # No good spot found, wander and look more
        agent._progress_wander(world, time_delta)
        agent.action_progress = 0.5  # Still looking
        return None
    
    def _progress_go_to_field(self, agent, world, time_delta: float):
        """Go to the assigned field"""
        # Similar to agent's go_home but with field as target
        field_pos = agent.action_target
        if not field_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = field_pos
        
        # Already at field
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_field", "location": field_pos}
        
        # Move towards field
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
    
    def _progress_plant_crop(self, agent, world, time_delta: float):
        """Plant a crop in the field"""
        # Check if we're at the field
        field_pos = agent.action_target
        if agent.position != field_pos:
            agent._set_action("go_to_field", field_pos)
            return None
        
        # Determine crop type based on season
        season = world.time_system.get_season()
        if season == "spring":
            crop_type = "wheat"
        elif season == "summer":
            crop_type = "corn"
        else:
            crop_type = "wheat"  # Default
        
        # Progress the planting
        if agent.action_progress < 0.8:
            # Still working on planting
            farming_skill = agent.skills["farming"]
            progress_amount = 0.1 + farming_skill * 0.2  # Skilled farmers plant faster
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "farming", 0.01)
            
            return None
        else:
            # Planting complete
            agent.action_progress = 1.0
            
            # Register the planted crop
            field_key = f"{field_pos[0]},{field_pos[1]}"
            self.job_specific_data["planted_crops"][field_key] = (
                crop_type,
                0.0,  # Initial growth stage
                world.time_system.get_tick()  # Plant time
            )
            
            return {
                "agent": agent.name, 
                "action": "planted_crop", 
                "crop_type": crop_type,
                "location": field_pos
            }
    
    def _progress_tend_crop(self, agent, world, time_delta: float):
        """Tend to a growing crop"""
        # Check if we're at the field
        field_pos = agent.action_target
        if agent.position != field_pos:
            agent._set_action("go_to_field", field_pos)
            return None
        
        # Get the crop data
        field_key = f"{field_pos[0]},{field_pos[1]}"
        if field_key not in self.job_specific_data["planted_crops"]:
            # No crop here anymore
            agent.action_progress = 1.0
            return None
            
        crop_data = self.job_specific_data["planted_crops"][field_key]
        crop_type, growth_stage, plant_time = crop_data
        
        # Tend to the crop (water, weed, etc.)
        if agent.action_progress < 0.9:
            # Still tending
            farming_skill = agent.skills["farming"]
            progress_amount = 0.2 + farming_skill * 0.2
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "farming", 0.005)
            
            # Improved growth from tending
            growth_boost = 0.05 + farming_skill * 0.05
            new_growth = min(1.0, growth_stage + growth_boost)
            
            # Update crop data
            self.job_specific_data["planted_crops"][field_key] = (
                crop_type,
                new_growth,
                plant_time
            )
            
            return None
        else:
            # Tending complete
            agent.action_progress = 1.0
            return {
                "agent": agent.name, 
                "action": "tended_crop", 
                "crop_type": crop_type,
                "growth": self.job_specific_data["planted_crops"][field_key][1]
            }
    
    def _progress_harvest_crop(self, agent, world, time_delta: float):
        """Harvest a mature crop"""
        # Check if we're at the field
        field_pos = agent.action_target
        if agent.position != field_pos:
            agent._set_action("go_to_field", field_pos)
            return None
        
        # Get the crop data
        field_key = f"{field_pos[0]},{field_pos[1]}"
        if field_key not in self.job_specific_data["planted_crops"]:
            # No crop here anymore
            agent.action_progress = 1.0
            return None
            
        crop_data = self.job_specific_data["planted_crops"][field_key]
        crop_type, growth_stage, plant_time = crop_data
        
        # Harvest the crop
        if agent.action_progress < 0.7:
            # Still harvesting
            farming_skill = agent.skills["farming"]
            progress_amount = 0.15 + farming_skill * 0.15
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "farming", 0.02)
            
            return None
        else:
            # Harvesting complete
            agent.action_progress = 1.0
            
            # Determine harvest amount based on crop type and skill
            farming_skill = agent.skills["farming"]
            base_amount = {
                "wheat": 20.0,
                "corn": 25.0
            }.get(crop_type, 15.0)
            
            # Skilled farmers get more yield
            harvest_amount = base_amount * (0.8 + 0.4 * farming_skill) * growth_stage
            
            # Add to inventory
            food_type = f"food_{crop_type}"
            agent.inventory[food_type] = agent.inventory.get(food_type, 0) + harvest_amount
            
            # Clear the field
            del self.job_specific_data["planted_crops"][field_key]
            
            return {
                "agent": agent.name, 
                "action": "harvested_crop", 
                "crop_type": crop_type,
                "amount": harvest_amount
            }
    
    def _progress_prepare_field(self, agent, world, time_delta: float):
        """Prepare a field for future planting"""
        # Check if we're at the field
        field_pos = agent.action_target
        if agent.position != field_pos:
            agent._set_action("go_to_field", field_pos)
            return None
        
        # Prepare the field
        if agent.action_progress < 0.85:
            # Still preparing
            farming_skill = agent.skills["farming"]
            progress_amount = 0.12 + farming_skill * 0.1
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "farming", 0.008)
            
            return None
        else:
            # Preparation complete
            agent.action_progress = 1.0
            
            # Mark field as prepared (could add a state to the field in a more complex implementation)
            return {
                "agent": agent.name, 
                "action": "prepared_field", 
                "location": field_pos
            }
    
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
        for field_key, crop_data in list(self.job_specific_data["planted_crops"].items()):
            crop_type, growth_stage, plant_time = crop_data
            
            # Growth rate depends on crop type
            base_growth_rate = {
                "wheat": 0.01,
                "corn": 0.008
            }.get(crop_type, 0.01)
            
            # Apply modifiers
            growth_rate = base_growth_rate * season_modifier * weather_modifier
            
            # Update growth
            new_growth = min(1.0, growth_stage + growth_rate)
            
            # Update crop data
            self.job_specific_data["planted_crops"][field_key] = (
                crop_type,
                new_growth,
                plant_time
            ) 