import random
from typing import Dict, List, Tuple, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType
from src.environment.threats import Threat, ThreatType, ThreatStatus

class GuardJob(Job):
    """
    Guard job responsible for village security, patrolling, and combat.
    Guards detect and engage threats to protect the village.
    """
    
    def __init__(self):
        """Initialize the guard job with appropriate skills and data"""
        super().__init__("guard", "Protects the village from threats and maintains security")
        
        # Set skill modifiers - guards get bonuses to these skills
        self.skill_modifiers = {
            "combat": 0.6,      # Major boost to combat
            "perception": 0.3,  # Moderate boost to perception
            "strength": 0.3     # Moderate boost to strength
        }
        
        # Job-specific data
        self.job_specific_data = {
            "patrol_points": [],         # Points to patrol between
            "current_patrol_point": 0,   # Index of current patrol point
            "village_center": None,      # Reference point for patrols
            "current_threat": None,      # Current threat being engaged
            "threat_level": 0.0,         # Perceived threat level (0-10)
            "combat_equipment": {        # Equipment modifiers
                "has_weapon": False,      # Has a proper weapon
                "has_armor": False,       # Has protective gear
                "weapon_quality": 0.0,    # Quality of weapon (0-1)
                "armor_quality": 0.0      # Quality of armor (0-1)
            },
            "threats_defeated": 0        # Career statistic
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next security action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Ensure we have patrol points set up
        if not self.job_specific_data["patrol_points"]:
            self._setup_patrol_points(agent, world)
            
        # Set village center
        if not self.job_specific_data["village_center"]:
            self.job_specific_data["village_center"] = world.village_center
        
        # Check for active threat - highest priority
        current_threat = self.job_specific_data["current_threat"]
        if current_threat and current_threat.status == ThreatStatus.ATTACKING:
            # If not at threat, go to it
            if agent.position != current_threat.position:
                agent._set_action("go_to_threat", current_threat)
            else:
                # At threat, engage it
                agent._set_action("engage_threat", current_threat)
            return
        
        # Check for nearby threats if not already engaged
        if not current_threat:
            threats = self._detect_threats(agent, world)
            if threats:
                # Prioritize and engage the most significant threat
                priority_threat = self._prioritize_threats(threats)
                self.job_specific_data["current_threat"] = priority_threat
                agent._set_action("go_to_threat", priority_threat)
                return
        
        # Regular patrol if no immediate threats
        if agent.needs["energy"] < 30.0:
            # Need to rest if energy is low
            if agent.position == agent.home_position or agent.position == self.job_specific_data["village_center"]:
                # Already at a good rest place
                agent._set_action("rest", None)
            else:
                # Go to a rest location
                rest_pos = agent.home_position if agent.home_position else self.job_specific_data["village_center"]
                agent._set_action("go_to_rest", rest_pos)
        else:
            # Continue patrolling
            next_point = self.job_specific_data["patrol_points"][self.job_specific_data["current_patrol_point"]]
            agent._set_action("patrol_to", next_point)
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a guard action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "patrol_to":
            return self._progress_patrol_to(agent, world, time_delta)
        elif action == "rest":
            return self._progress_rest(agent, world, time_delta)
        elif action == "go_to_rest":
            return self._progress_go_to_rest(agent, world, time_delta)
        elif action == "go_to_threat":
            return self._progress_go_to_threat(agent, world, time_delta)
        elif action == "engage_threat":
            return self._progress_engage_threat(agent, world, time_delta)
        
        return None
    
    def detect_threat(self, agent, threat):
        """
        Directly set a threat for this guard to respond to.
        
        Args:
            agent: The agent responding
            threat: The threat to respond to
        """
        self.job_specific_data["current_threat"] = threat
        agent._set_action("go_to_threat", threat)
        agent.action_progress = 0.0
    
    def _setup_patrol_points(self, agent, world):
        """Set up patrol points around the village"""
        # Get village center
        center_x, center_y = world.village_center
        
        # Create patrol circuit around center with some randomness
        num_points = random.randint(3, 6)
        radius = random.randint(5, 15)  # Distance from center
        
        patrol_points = []
        for i in range(num_points):
            angle = (2 * 3.14159 * i) / num_points  # Radians
            
            # Calculate point with some randomness
            px = center_x + int(radius * 1.5 * (0.8 + 0.4 * random.random()) * (random.random() - 0.5 + 2 * (angle % 3.14159)))
            py = center_y + int(radius * (0.8 + 0.4 * random.random()) * (random.random() - 0.5 + 2 * ((angle + 1.57) % 3.14159)))
            
            # Ensure within world bounds
            px = max(0, min(world.width - 1, px))
            py = max(0, min(world.height - 1, py))
            
            patrol_points.append((px, py))
        
        self.job_specific_data["patrol_points"] = patrol_points
        self.job_specific_data["current_patrol_point"] = 0
        self.job_specific_data["village_center"] = (center_x, center_y)
    
    def _detect_threats(self, agent, world):
        """
        Detect threats in the vicinity.
        
        Args:
            agent: The agent doing the detecting
            world: Reference to the world
            
        Returns:
            List of detected threats
        """
        # Use perception skill to determine detection range
        detection_range = 5 + int(agent.skills["perception"] * 10)  # 5-15 cells
        
        # Get threats within range
        threats = world.get_threats_in_range(agent.position, detection_range)
        
        # Only attacking threats are relevant
        return [t for t in threats if t.status == ThreatStatus.ATTACKING]
    
    def _prioritize_threats(self, threats):
        """
        Prioritize which threat to engage first.
        
        Args:
            threats: List of threats
            
        Returns:
            Highest priority threat
        """
        if not threats:
            return None
            
        # For now, just take the first one
        # In future, could prioritize based on threat type, distance to village center, etc.
        return threats[0]
    
    def _progress_patrol_to(self, agent, world, time_delta: float):
        """Progress patrolling to the next point"""
        patrol_target = agent.action_target
        if not patrol_target:
            # If no target, use village center
            patrol_target = self.job_specific_data["village_center"]
        
        current_x, current_y = agent.position
        target_x, target_y = patrol_target
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            # Move to next patrol point
            self.job_specific_data["current_patrol_point"] = (
                self.job_specific_data["current_patrol_point"] + 1
            ) % len(self.job_specific_data["patrol_points"])
            
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "patrol_checkpoint_reached"}
        
        # Move towards target
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        # Slight chance to pause and look around
        if random.random() < 0.2:
            # Perception skill check - might detect threats
            perception_check = random.random() < agent.skills["perception"] * 0.3
            if perception_check:
                threats = self._detect_threats(agent, world)
                if threats:
                    priority_threat = self._prioritize_threats(threats)
                    self.job_specific_data["current_threat"] = priority_threat
                    agent._set_action("go_to_threat", priority_threat)
                    return {"agent": agent.name, "action": "threat_detected", "threat": priority_threat.threat_type.name}
            
            # Just pause briefly
            agent.action_progress = 0.5
            return {"agent": agent.name, "action": "patrolling_pause"}
        
        # Move agent
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent.action_progress = 1.0
        else:
            agent.action_progress = 0.5  # Still in progress
            
        # Skill improvements from practice
        self.improve_skills(agent, "perception", 0.002)
            
        return None
    
    def _progress_rest(self, agent, world, time_delta: float):
        """Rest to regain energy"""
        if agent.action_progress < 1.0:
            # Recovery based on time passed
            recovery_amount = 10.0 * time_delta
            agent.needs["energy"] = min(100.0, agent.needs["energy"] + recovery_amount)
            
            # Progress the rest action
            agent.action_progress += 0.2
            
            if agent.needs["energy"] >= 80.0:
                # Sufficiently rested
                agent.action_progress = 1.0
                
            return None
        
        # Rest complete
        return {"agent": agent.name, "action": "rest_complete"}
    
    def _progress_go_to_rest(self, agent, world, time_delta: float):
        """Go to a rest location"""
        rest_pos = agent.action_target
        if not rest_pos:
            # Default to village center
            rest_pos = self.job_specific_data["village_center"]
            
        current_x, current_y = agent.position
        target_x, target_y = rest_pos
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            agent._set_action("rest", None)
            agent.action_progress = 0.0
            return {"agent": agent.name, "action": "arrived_at_rest"}
        
        # Move towards target
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent._set_action("rest", None)
            agent.action_progress = 0.0
        else:
            agent.action_progress = 0.5  # Still in progress
            
        return None
    
    def _progress_go_to_threat(self, agent, world, time_delta: float):
        """Move toward a detected threat"""
        threat = agent.action_target
        
        # Ensure threat is still valid
        if not threat or threat.status != ThreatStatus.ATTACKING:
            # Threat no longer active
            self.job_specific_data["current_threat"] = None
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "threat_neutralized"}
        
        current_x, current_y = agent.position
        target_x, target_y = threat.position
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            agent._set_action("engage_threat", threat)
            agent.action_progress = 0.0
            return {"agent": agent.name, "action": "arrived_at_threat"}
        
        # Move towards target (faster than normal movement)
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent._set_action("engage_threat", threat)
            agent.action_progress = 0.0
        else:
            agent.action_progress = 0.5  # Still in progress
            
        return None
    
    def _progress_engage_threat(self, agent, world, time_delta: float):
        """Engage in combat with a threat"""
        threat = agent.action_target
        
        # Ensure threat is still valid
        if not threat or threat.status != ThreatStatus.ATTACKING:
            # Threat no longer active
            self.job_specific_data["current_threat"] = None
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "threat_neutralized"}
        
        # Check if at threat position
        if agent.position != threat.position:
            agent._set_action("go_to_threat", threat)
            return {"agent": agent.name, "action": "pursuing_threat"}
        
        # Combat logic
        if agent.action_progress < 0.95:
            # Calculate combat effectiveness
            combat_skill = agent.skills["combat"]
            strength = agent.skills["strength"]
            
            # Equipment bonuses
            equipment = self.job_specific_data["combat_equipment"]
            weapon_bonus = 1.0 + (equipment["weapon_quality"] * 0.5) if equipment["has_weapon"] else 0.5
            armor_bonus = 1.0 + (equipment["armor_quality"] * 0.5) if equipment["has_armor"] else 0.5
            
            # Check for weapons in village resources
            village_resources = world.resource_manager.get_village_resources()
            weapons_available = village_resources.get(ResourceType.WEAPONS, 0)
            
            # If we don't have a weapon but village has some, acquire one
            if not equipment["has_weapon"] and weapons_available > 0:
                took = world.resource_manager.take_from_village_storage(ResourceType.WEAPONS, 1)
                if took > 0:
                    equipment["has_weapon"] = True
                    equipment["weapon_quality"] = 0.7 + (random.random() * 0.3)  # 0.7-1.0 quality
                    weapon_bonus = 1.0 + (equipment["weapon_quality"] * 0.5)
            
            # Calculate damage done to threat
            base_damage = (combat_skill * 3.0 + strength * 2.0) * weapon_bonus * time_delta
            
            # Apply damage to threat
            threat_defeated = world.threat_manager.damage_threat(threat.id, base_damage)
            
            # Calculate damage received (if any)
            if random.random() < 0.3:  # 30% chance to be hit
                damage_received = threat.base_strength * threat.strength * 0.1 * time_delta / armor_bonus
                agent.health -= damage_received
                
                # Critical condition check
                if agent.health < 30.0:
                    # Chance to retreat if badly injured
                    if random.random() < 0.3:
                        # Retreat to village center
                        self.job_specific_data["current_threat"] = None
                        agent._set_action("go_to_rest", self.job_specific_data["village_center"])
                        return {"agent": agent.name, "action": "retreating", "health": agent.health}
            
            # Skill improvements from combat
            self.improve_skills(agent, "combat", 0.005)
            self.improve_skills(agent, "strength", 0.003)
            
            # Progress the combat action
            progress_rate = 0.1 + (combat_skill * 0.1)  # Higher skill = faster resolution
            agent.action_progress += progress_rate
            
            # Energy cost of combat
            agent.needs["energy"] -= 2.0 * time_delta
            
            # Check if threat was defeated
            if threat_defeated:
                self.job_specific_data["threats_defeated"] += 1
                self.job_specific_data["current_threat"] = None
                agent.action_progress = 1.0
                return {
                    "agent": agent.name, 
                    "action": "threat_defeated", 
                    "threat_type": threat.threat_type.name,
                    "threats_defeated": self.job_specific_data["threats_defeated"]
                }
                
            return None
        else:
            # Combat complete but threat not defeated
            # Likely the threat fled or was already defeated by others
            self.job_specific_data["current_threat"] = None
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "combat_complete"}
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling guard-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # Clear current threat
        self.job_specific_data["current_threat"] = None
        
        # Return equipment to village if any
        equipment = self.job_specific_data["combat_equipment"]
        if equipment["has_weapon"]:
            # Would add weapon back to village storage in a complete system
            pass
        
        # Call parent remove method
        super().remove_from_agent(agent) 