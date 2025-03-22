import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class HealerJob(Job):
    """
    Healer job responsible for tending to injured or sick agents.
    Healers gather herbs, create potions, and treat wounds and illnesses.
    """
    
    def __init__(self):
        """Initialize the healer job with appropriate skills and data"""
        super().__init__("healer", "Treats injuries and illnesses, creates healing potions")
        
        # Set skill modifiers - healers get bonuses to these skills
        self.skill_modifiers = {
            "healing": 0.7,      # Major boost to healing
            "perception": 0.3,   # Moderate boost to perception (finding herbs)
            "crafting": 0.2      # Minor boost to crafting (making potions)
        }
        
        # Job-specific data
        self.job_specific_data = {
            "known_herb_locations": [],  # Coordinates of known herb locations
            "current_herb_location": None,  # Current herb location being harvested
            "herb_stockpile": 0.0,  # Temporary herbs being carried
            "max_carry_capacity": 30.0,  # Maximum herbs that can be carried
            "infirmary_position": None,  # Location of the infirmary
            "current_patient": None,  # Agent currently being treated
            "patients_treated": 0,  # Number of patients treated
            "potions_created": 0  # Number of potions created
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next healing action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Set up infirmary position if not set
        if not self.job_specific_data["infirmary_position"]:
            # For now, just use the agent's home or center of village
            if agent.home_position:
                self.job_specific_data["infirmary_position"] = agent.home_position
            else:
                self.job_specific_data["infirmary_position"] = (world.width // 2, world.height // 2)
        
        # First priority: check for injured agents needing immediate care
        injured_agents = [a for a in world.agents if a.health < 70.0 and a != agent]
        if injured_agents:
            # Find the most severely injured agent
            patient = min(injured_agents, key=lambda a: a.health)
            self.job_specific_data["current_patient"] = patient.id
            
            # Check if we're at the same location as the patient
            if agent.position == patient.position:
                agent._set_action("treat_patient", patient.id)
            else:
                agent._set_action("go_to_patient", patient.position)
            return
        
        # Second priority: create potions if we have herbs
        resources = world.resource_manager.get_village_resources()
        herbs = resources.get(ResourceType.HERB, 0.0)
        
        if herbs >= 5.0 and agent.position == self.job_specific_data["infirmary_position"]:
            # We have herbs and are at the infirmary, make potions
            agent._set_action("create_potion", None)
            return
        elif herbs >= 5.0:
            # We have herbs but need to go to the infirmary
            agent._set_action("go_to_infirmary", None)
            return
        
        # Third priority: if carrying herbs, return to infirmary
        if self.job_specific_data["herb_stockpile"] > 0:
            agent._set_action("return_with_herbs", None)
            return
        
        # Fourth priority: find and gather herbs
        if self.job_specific_data["current_herb_location"]:
            # We have a herb location assigned
            herb_pos = self.job_specific_data["current_herb_location"]
            
            # Check if we're at the herb location
            if agent.position != herb_pos:
                agent._set_action("go_to_herbs", herb_pos)
            else:
                agent._set_action("gather_herbs", herb_pos)
            return
        
        # Need to find herbs
        agent._set_action("find_herbs", None)
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a healing action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "find_herbs":
            return self._progress_find_herbs(agent, world, time_delta)
        elif action == "go_to_herbs":
            return self._progress_go_to_herbs(agent, world, time_delta)
        elif action == "gather_herbs":
            return self._progress_gather_herbs(agent, world, time_delta)
        elif action == "return_with_herbs":
            return self._progress_return_with_herbs(agent, world, time_delta)
        elif action == "go_to_infirmary":
            return self._progress_go_to_infirmary(agent, world, time_delta)
        elif action == "create_potion":
            return self._progress_create_potion(agent, world, time_delta)
        elif action == "go_to_patient":
            return self._progress_go_to_patient(agent, world, time_delta)
        elif action == "treat_patient":
            return self._progress_treat_patient(agent, world, time_delta)
        
        return None
    
    def _progress_find_herbs(self, agent, world, time_delta: float):
        """Find herbs to harvest"""
        # If we already know herb locations, pick one
        if self.job_specific_data["known_herb_locations"]:
            # Assign a known herb location
            herb_pos = random.choice(self.job_specific_data["known_herb_locations"])
            self.job_specific_data["current_herb_location"] = herb_pos
            agent._set_action("go_to_herbs", herb_pos)
            return {"agent": agent.name, "action": "assigned_herb_location", "location": herb_pos}
        
        # Look for potential herb locations nearby
        x, y = agent.position
        neighbors = world.get_neighboring_cells(x, y, 5)  # Search in a larger radius
        
        # Check for suitable locations
        potential_herbs = []
        for nx, ny in neighbors:
            resources = world.resource_manager.get_resources_at(nx, ny)
            
            # Look for herb resources
            has_herbs = any(r.resource_type == ResourceType.HERB for r in resources)
            
            if has_herbs:
                potential_herbs.append((nx, ny))
        
        if potential_herbs:
            # Found herbs
            herb_pos = random.choice(potential_herbs)
            self.job_specific_data["known_herb_locations"].append(herb_pos)
            self.job_specific_data["current_herb_location"] = herb_pos
            agent._set_action("go_to_herbs", herb_pos)
            
            # Add herbs to memory
            if "herb_location" not in agent.known_locations:
                agent.known_locations["herb_location"] = []
            if herb_pos not in agent.known_locations["herb_location"]:
                agent.known_locations["herb_location"].append(herb_pos)
                
            return {"agent": agent.name, "action": "found_herbs", "location": herb_pos}
        
        # No herbs found, wander and look more
        agent._progress_wander(world, time_delta)
        agent.action_progress = 0.5  # Still looking
        return None
    
    def _progress_go_to_herbs(self, agent, world, time_delta: float):
        """Go to the herb location"""
        herb_pos = agent.action_target
        if not herb_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = herb_pos
        
        # Already at herb location
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_herbs", "location": herb_pos}
        
        # Move towards herb location
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
    
    def _progress_gather_herbs(self, agent, world, time_delta: float):
        """Gather herbs from a location"""
        # Check if we're at the herb location
        herb_pos = agent.action_target
        if agent.position != herb_pos:
            agent._set_action("go_to_herbs", herb_pos)
            return None
        
        # Get herb resources at location
        resources = world.resource_manager.get_resources_at(*herb_pos)
        herb_resources = [r for r in resources if r.resource_type == ResourceType.HERB]
        
        if not herb_resources:
            # No herbs here anymore
            agent.action_progress = 1.0
            
            # Remove from known herb locations
            if herb_pos in self.job_specific_data["known_herb_locations"]:
                self.job_specific_data["known_herb_locations"].remove(herb_pos)
                
            self.job_specific_data["current_herb_location"] = None
            return {"agent": agent.name, "action": "herbs_depleted", "location": herb_pos}
        
        # Gather herbs
        if agent.action_progress < 0.9:
            # Still gathering
            perception_skill = agent.skills["perception"]
            progress_amount = 0.15 + perception_skill * 0.15
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "perception", 0.006)
            self.improve_skills(agent, "healing", 0.003)
            
            return None
        else:
            # Gathering complete - harvest herbs
            agent.action_progress = 1.0
            
            # Determine amount of herbs harvested based on skill
            perception_skill = agent.skills["perception"]
            herb_amount = 5.0 + perception_skill * 10.0  # 5-15 units based on skill
            
            # Add to stockpile
            self.job_specific_data["herb_stockpile"] += herb_amount
            
            # Remove some of the herb resource
            herb = herb_resources[0]
            herb.quantity -= 1
            
            if herb.quantity <= 0:
                # Herbs depleted
                world.resource_manager.remove_resource(herb)
                
                # Remove from known herb locations
                if herb_pos in self.job_specific_data["known_herb_locations"]:
                    self.job_specific_data["known_herb_locations"].remove(herb_pos)
                    
                self.job_specific_data["current_herb_location"] = None
            
            # If we've reached capacity, head back to village
            if self.job_specific_data["herb_stockpile"] >= self.job_specific_data["max_carry_capacity"]:
                agent._set_action("return_with_herbs", None)
            
            return {
                "agent": agent.name, 
                "action": "gathered_herbs", 
                "amount": herb_amount,
                "total_carried": self.job_specific_data["herb_stockpile"]
            }
    
    def _progress_return_with_herbs(self, agent, world, time_delta: float):
        """Return to infirmary with harvested herbs"""
        target = self.job_specific_data["infirmary_position"]
        
        if not target:
            # No infirmary, go to center of map
            target = (world.width // 2, world.height // 2)
            self.job_specific_data["infirmary_position"] = target
        
        current_x, current_y = agent.position
        target_x, target_y = target
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            # Deposit the herbs in village storage
            herb_amount = self.job_specific_data["herb_stockpile"]
            
            # Add to village resources
            world.resource_manager.add_to_village_storage(ResourceType.HERB, herb_amount)
            
            # Reset stockpile
            self.job_specific_data["herb_stockpile"] = 0.0
            
            agent.action_progress = 1.0
            return {
                "agent": agent.name, 
                "action": "deposited_herbs", 
                "amount": herb_amount,
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
    
    def _progress_go_to_infirmary(self, agent, world, time_delta: float):
        """Go to the infirmary"""
        target = self.job_specific_data["infirmary_position"]
        
        if not target:
            # No infirmary, go to center of map
            target = (world.width // 2, world.height // 2)
            self.job_specific_data["infirmary_position"] = target
        
        current_x, current_y = agent.position
        target_x, target_y = target
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_infirmary", "location": agent.position}
        
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
    
    def _progress_create_potion(self, agent, world, time_delta: float):
        """Create a healing potion from herbs"""
        # Check if we're at the infirmary
        infirmary_pos = self.job_specific_data["infirmary_position"]
        if agent.position != infirmary_pos:
            agent._set_action("go_to_infirmary", None)
            return None
        
        # Check if we have enough herbs
        resources = world.resource_manager.get_village_resources()
        herbs = resources.get(ResourceType.HERB, 0.0)
        
        if herbs < 5.0:  # Minimum herbs needed
            # Not enough herbs
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "potion_creation_failed", "reason": "not_enough_herbs"}
        
        # Create potion
        if agent.action_progress < 0.9:
            # Still creating
            healing_skill = agent.skills["healing"]
            progress_amount = 0.15 + healing_skill * 0.15
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "healing", 0.007)
            self.improve_skills(agent, "crafting", 0.005)
            
            return None
        else:
            # Creation complete
            agent.action_progress = 1.0
            
            # Consume herbs
            herbs_used = 5.0
            world.resource_manager.take_from_village_storage(ResourceType.HERB, herbs_used)
            
            # Determine potion quality based on skill
            healing_skill = agent.skills["healing"]
            potion_quality = 1.0 + healing_skill * 0.5  # 1.0-1.5 quality
            
            # Create potion
            world.resource_manager.add_to_village_storage(ResourceType.POTION, potion_quality)
            
            # Update statistics
            self.job_specific_data["potions_created"] += 1
            
            return {
                "agent": agent.name, 
                "action": "created_potion", 
                "quality": potion_quality,
                "herbs_used": herbs_used
            }
    
    def _progress_go_to_patient(self, agent, world, time_delta: float):
        """Go to a patient needing treatment"""
        patient_pos = agent.action_target
        if not patient_pos:
            agent.action_progress = 1.0
            self.job_specific_data["current_patient"] = None
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = patient_pos
        
        # Already at patient location
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_patient", "location": patient_pos}
        
        # Move towards patient
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
    
    def _progress_treat_patient(self, agent, world, time_delta: float):
        """Treat an injured patient"""
        patient_id = agent.action_target
        
        # Find the patient
        patient = None
        for a in world.agents:
            if a.id == patient_id:
                patient = a
                break
                
        if not patient or patient.health >= 100.0:
            # Patient not found or already healed
            agent.action_progress = 1.0
            self.job_specific_data["current_patient"] = None
            return {"agent": agent.name, "action": "treatment_complete", "reason": "patient_healthy"}
        
        # Check if we're at the same location
        if agent.position != patient.position:
            agent._set_action("go_to_patient", patient.position)
            return None
        
        # Check if we have potions
        resources = world.resource_manager.get_village_resources()
        potions = resources.get(ResourceType.POTION, 0.0)
        has_potions = potions >= 1.0
        
        # Treat patient
        if agent.action_progress < 0.9:
            # Still treating
            healing_skill = agent.skills["healing"]
            progress_amount = 0.15 + healing_skill * 0.1
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "healing", 0.01)
            
            return None
        else:
            # Treatment complete
            agent.action_progress = 1.0
            
            # Determine healing amount based on skill and potions
            healing_skill = agent.skills["healing"]
            base_healing = 10.0 + healing_skill * 20.0  # 10-30 points of healing
            
            if has_potions:
                # Use a potion for extra healing
                potion_quality = 1.0
                world.resource_manager.take_from_village_storage(ResourceType.POTION, 1.0)
                total_healing = base_healing * (1.0 + potion_quality * 0.5)
            else:
                total_healing = base_healing
            
            # Apply healing to patient
            old_health = patient.health
            patient.health = min(100.0, patient.health + total_healing)
            
            # Update statistics
            self.job_specific_data["patients_treated"] += 1
            self.job_specific_data["current_patient"] = None
            
            return {
                "agent": agent.name, 
                "action": "treated_patient", 
                "patient": patient.name,
                "old_health": old_health,
                "new_health": patient.health,
                "used_potion": has_potions
            }
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling healer-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # If carrying herbs, drop them
        herbs_carried = self.job_specific_data.get("herb_stockpile", 0.0)
        if herbs_carried > 0:
            # In a more complete system, would drop herbs at agent's location
            # For now, just lose them
            self.job_specific_data["herb_stockpile"] = 0.0
        
        # Clear current patient
        self.job_specific_data["current_patient"] = None
        
        # Call parent remove method
        super().remove_from_agent(agent) 