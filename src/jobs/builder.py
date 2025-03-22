import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class BuilderJob(Job):
    """
    Builder job responsible for constructing and maintaining buildings.
    Builders construct new buildings, repair damaged ones, and maintain village infrastructure.
    """
    
    def __init__(self):
        """Initialize the builder job with appropriate skills and data"""
        super().__init__("builder", "Constructs and maintains buildings")
        
        # Set skill modifiers - builders get bonuses to these skills
        self.skill_modifiers = {
            "building": 0.6,     # Major boost to building
            "strength": 0.3,     # Moderate boost to strength
            "crafting": 0.2      # Minor boost to crafting
        }
        
        # Job-specific data
        self.job_specific_data = {
            "current_project": None,  # Current building project (location, type, progress)
            "projects_completed": {},  # Type -> count of buildings completed
            "repairs_completed": 0,  # Number of repairs completed
            "known_building_sites": [],  # List of building sites
            "build_queue": []  # Queue of buildings to construct
        }
        
        # Building types and their requirements
        self.building_recipes = {
            "house": {
                "wood": 50.0,
                "stone": 30.0,
                "time": 5.0,
                "skill_factor": "building",
                "size": (1, 1)  # width, height
            },
            "farm": {
                "wood": 20.0,
                "stone": 10.0,
                "time": 3.0,
                "skill_factor": "building",
                "size": (2, 2)
            },
            "workshop": {
                "wood": 40.0,
                "stone": 20.0,
                "time": 4.0,
                "skill_factor": "building",
                "size": (1, 1)
            },
            "wall_section": {
                "wood": 10.0,
                "stone": 30.0,
                "time": 2.0,
                "skill_factor": "building",
                "size": (1, 1)
            },
            "watchtower": {
                "wood": 30.0,
                "stone": 40.0,
                "time": 6.0,
                "skill_factor": "building",
                "size": (1, 1)
            }
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next building action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Check if we have a current project
        if self.job_specific_data["current_project"]:
            location, build_type, progress = self.job_specific_data["current_project"]
            
            # Go to the project site if not there
            if agent.position != location:
                agent._set_action("go_to_build_site", location)
                return
            
            # Continue construction
            agent._set_action("build", build_type)
            return
        
        # No current project, check for buildings needing repair
        damaged_buildings = [b for b in world.buildings if b.condition < 80.0]
        if damaged_buildings:
            # Choose the most damaged building
            building = min(damaged_buildings, key=lambda b: b.condition)
            
            # Go to building if not there
            if agent.position != building.position:
                agent._set_action("go_to_repair_site", building.position)
            else:
                # Set up repair project
                self.job_specific_data["current_project"] = (building.position, "repair", 0.0)
                agent._set_action("repair", None)
            return
        
        # Check if we have a build queue
        if self.job_specific_data["build_queue"]:
            build_type, location = self.job_specific_data["build_queue"].pop(0)
            
            # Check if location is still available
            if self._is_buildable(world, location, build_type):
                # Set up new project
                self.job_specific_data["current_project"] = (location, build_type, 0.0)
                
                # Go to build site
                if agent.position != location:
                    agent._set_action("go_to_build_site", location)
                else:
                    agent._set_action("build", build_type)
                return
        
        # Look for new building site
        agent._set_action("find_build_site", None)
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a building action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "go_to_build_site":
            return self._progress_go_to_build_site(agent, world, time_delta)
        elif action == "go_to_repair_site":
            return self._progress_go_to_repair_site(agent, world, time_delta)
        elif action == "build":
            return self._progress_build(agent, world, time_delta)
        elif action == "repair":
            return self._progress_repair(agent, world, time_delta)
        elif action == "find_build_site":
            return self._progress_find_build_site(agent, world, time_delta)
        
        return None
    
    def _progress_go_to_build_site(self, agent, world, time_delta: float):
        """Go to the building site"""
        build_site = agent.action_target
        if not build_site:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = build_site
        
        # Already at build site
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_build_site", "location": build_site}
        
        # Move towards build site
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
    
    def _progress_go_to_repair_site(self, agent, world, time_delta: float):
        """Go to a building that needs repair"""
        repair_site = agent.action_target
        if not repair_site:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = repair_site
        
        # Already at repair site
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_repair_site", "location": repair_site}
        
        # Move towards repair site
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent.action_progress = 1.0
            
            # Set up repair project
            self.job_specific_data["current_project"] = (repair_site, "repair", 0.0)
        else:
            agent.action_progress = 0.5  # Still in progress
            
        return None
    
    def _progress_build(self, agent, world, time_delta: float):
        """Build a structure"""
        # Get project details
        if not self.job_specific_data["current_project"]:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "build_failed", "reason": "no_project"}
            
        location, build_type, progress = self.job_specific_data["current_project"]
        
        # Check if we're at the build site
        if agent.position != location:
            agent._set_action("go_to_build_site", location)
            return None
        
        # Check if this is still a valid build site
        if not self._is_buildable(world, location, build_type) or build_type not in self.building_recipes:
            # Cancel project
            self.job_specific_data["current_project"] = None
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "build_cancelled", "reason": "invalid_site"}
        
        # Check if we have the resources
        resources = world.resource_manager.get_village_resources()
        recipe = self.building_recipes[build_type]
        
        # For initial check only - will consume resources at completion
        required_resources = {
            "wood": recipe.get("wood", 0.0),
            "stone": recipe.get("stone", 0.0)
        }
        
        for resource_name, amount in required_resources.items():
            resource_type = self._resource_name_to_type(resource_name)
            available = resources.get(resource_type, 0.0)
            
            if available < amount:
                # Not enough resources
                self.job_specific_data["current_project"] = None
                agent.action_progress = 1.0
                return {
                    "agent": agent.name, 
                    "action": "build_failed", 
                    "reason": f"not_enough_{resource_name}",
                    "build_type": build_type
                }
        
        # Continue building
        if agent.action_progress < 0.95:
            # Still building
            skill_name = recipe.get("skill_factor", "building")
            skill_level = agent.skills[skill_name]
            
            # Time factor - higher skill = faster building
            time_factor = recipe.get("time", 3.0)
            progress_amount = (0.05 / time_factor) + (skill_level * 0.05)
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "building", 0.01)
            self.improve_skills(agent, "strength", 0.005)
            
            return None
        else:
            # Building complete
            agent.action_progress = 1.0
            
            # Consume resources
            for resource_name, amount in required_resources.items():
                resource_type = self._resource_name_to_type(resource_name)
                world.resource_manager.take_from_village_storage(resource_type, amount)
            
            # Create the building (would need implementation of building classes)
            # For now, just log the completion
            
            # Store project completion
            if build_type not in self.job_specific_data["projects_completed"]:
                self.job_specific_data["projects_completed"][build_type] = 0
            self.job_specific_data["projects_completed"][build_type] += 1
            
            # Clear current project
            self.job_specific_data["current_project"] = None
            
            return {
                "agent": agent.name, 
                "action": "building_completed", 
                "building_type": build_type,
                "location": location
            }
    
    def _progress_repair(self, agent, world, time_delta: float):
        """Repair a damaged building"""
        # Get project details
        if not self.job_specific_data["current_project"]:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "repair_failed", "reason": "no_project"}
            
        location, _, _ = self.job_specific_data["current_project"]
        
        # Check if we're at the repair site
        if agent.position != location:
            agent._set_action("go_to_repair_site", location)
            return None
        
        # Find the building to repair
        building = None
        for b in world.buildings:
            if b.position == location:
                building = b
                break
                
        if not building or building.condition >= 100.0:
            # No building or already fully repaired
            self.job_specific_data["current_project"] = None
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "repair_complete", "location": location}
        
        # Check if we have resources for repair
        resources = world.resource_manager.get_village_resources()
        wood = resources.get(ResourceType.WOOD, 0.0)
        stone = resources.get(ResourceType.STONE, 0.0)
        
        repair_cost = {
            "wood": max(5.0, (100.0 - building.condition) * 0.1),
            "stone": max(3.0, (100.0 - building.condition) * 0.05)
        }
        
        if wood < repair_cost["wood"] or stone < repair_cost["stone"]:
            # Not enough resources
            self.job_specific_data["current_project"] = None
            agent.action_progress = 1.0
            return {
                "agent": agent.name, 
                "action": "repair_failed", 
                "reason": "not_enough_resources",
                "location": location
            }
        
        # Continue repairing
        if agent.action_progress < 0.95:
            # Still repairing
            skill_level = agent.skills["building"]
            
            # Progress based on skill
            progress_amount = 0.1 + (skill_level * 0.1)
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "building", 0.008)
            
            return None
        else:
            # Repair complete
            agent.action_progress = 1.0
            
            # Consume resources
            world.resource_manager.take_from_village_storage(ResourceType.WOOD, repair_cost["wood"])
            world.resource_manager.take_from_village_storage(ResourceType.STONE, repair_cost["stone"])
            
            # Repair amount based on skill
            skill_level = agent.skills["building"]
            repair_amount = 20.0 + (skill_level * 30.0)  # 20-50 points of repair
            
            # Apply repair to building
            old_condition = building.condition
            building.condition = min(100.0, building.condition + repair_amount)
            
            # Update statistics
            self.job_specific_data["repairs_completed"] += 1
            
            # Clear current project
            self.job_specific_data["current_project"] = None
            
            return {
                "agent": agent.name, 
                "action": "building_repaired", 
                "location": location,
                "old_condition": old_condition,
                "new_condition": building.condition
            }
    
    def _progress_find_build_site(self, agent, world, time_delta: float):
        """Find a suitable site for new construction"""
        # First determine what to build based on village needs
        # For now, just alternate between houses and wall sections
        
        # Bias towards houses if few exist
        houses = sum(1 for b in world.buildings if hasattr(b, 'building_type') and b.building_type == 'house')
        walls = sum(1 for b in world.buildings if hasattr(b, 'building_type') and b.building_type == 'wall_section')
        
        if houses < 5 or (houses / max(1, len(world.buildings))) < 0.3:
            build_type = "house"
        elif walls < 10 or (walls / max(1, len(world.buildings))) < 0.2:
            build_type = "wall_section"
        else:
            # Choose randomly among available types
            available_types = list(self.building_recipes.keys())
            build_type = random.choice(available_types)
        
        # Search for suitable location near village center
        village_center = (world.width // 2, world.height // 2)
        x_center, y_center = village_center
        
        # Create a spiral search pattern
        max_radius = min(world.width, world.height) // 2
        search_locations = []
        
        for radius in range(1, max_radius):
            # Top and bottom rows
            for x in range(x_center - radius, x_center + radius + 1):
                if 0 <= x < world.width:
                    if 0 <= y_center - radius < world.height:
                        search_locations.append((x, y_center - radius))
                    if 0 <= y_center + radius < world.height:
                        search_locations.append((x, y_center + radius))
            
            # Left and right columns (excluding corners)
            for y in range(y_center - radius + 1, y_center + radius):
                if 0 <= y < world.height:
                    if 0 <= x_center - radius < world.width:
                        search_locations.append((x_center - radius, y))
                    if 0 <= x_center + radius < world.width:
                        search_locations.append((x_center + radius, y))
        
        # Check each location for suitability
        for location in search_locations:
            if self._is_buildable(world, location, build_type):
                # Found a suitable location
                
                # Add to known building sites
                if location not in self.job_specific_data["known_building_sites"]:
                    self.job_specific_data["known_building_sites"].append(location)
                
                # Add to build queue
                self.job_specific_data["build_queue"].append((build_type, location))
                
                agent.action_progress = 1.0
                return {
                    "agent": agent.name, 
                    "action": "building_site_found", 
                    "location": location,
                    "building_type": build_type
                }
        
        # No suitable location found, just wander
        agent._progress_wander(world, time_delta)
        agent.action_progress = 0.7  # Getting closer to completion even if not successful
        
        return None
    
    def _is_buildable(self, world, location: tuple, build_type: str) -> bool:
        """Check if a location is suitable for building"""
        x, y = location
        
        # Get building size
        recipe = self.building_recipes.get(build_type)
        if not recipe:
            return False
            
        width, height = recipe.get("size", (1, 1))
        
        # Check if within world bounds
        if not (0 <= x < world.width - width + 1 and 0 <= y < world.height - height + 1):
            return False
        
        # Check if space is clear of other buildings and agents
        for dx in range(width):
            for dy in range(height):
                check_x, check_y = x + dx, y + dy
                
                # Check for buildings
                for building in world.buildings:
                    if building.position == (check_x, check_y):
                        return False
                
                # Check for agents
                for agent in world.agents:
                    if agent.position == (check_x, check_y):
                        return False
                
                # Check for resources that shouldn't be built on
                resources = world.resource_manager.get_resources_at(check_x, check_y)
                if any(r.resource_type in [ResourceType.TREE, ResourceType.STONE, ResourceType.IRON_ORE, 
                                         ResourceType.WATER] for r in resources):
                    return False
        
        # Special case for wall sections - should be near other wall sections or near the edge
        if build_type == "wall_section":
            # Check if near another wall
            has_adjacent_wall = False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    check_x, check_y = x + dx, y + dy
                    if 0 <= check_x < world.width and 0 <= check_y < world.height:
                        for building in world.buildings:
                            if building.position == (check_x, check_y) and hasattr(building, 'building_type') and building.building_type == 'wall_section':
                                has_adjacent_wall = True
                                break
            
            # Also consider edges of map as valid for walls
            near_edge = x <= 1 or y <= 1 or x >= world.width - 2 or y >= world.height - 2
            
            if not (has_adjacent_wall or near_edge):
                return False
        
        return True
    
    def _resource_name_to_type(self, resource_name: str) -> ResourceType:
        """Convert recipe resource name to ResourceType"""
        if resource_name == "wood":
            return ResourceType.WOOD
        elif resource_name == "stone":
            return ResourceType.STONE
        elif resource_name == "iron":
            return ResourceType.IRON_INGOT
        else:
            return ResourceType.WOOD  # Default
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling builder-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # Clear current project
        self.job_specific_data["current_project"] = None
        
        # Call parent remove method
        super().remove_from_agent(agent) 