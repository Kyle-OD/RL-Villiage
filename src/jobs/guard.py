import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class GuardJob(Job):
    """
    Guard job responsible for village security.
    Guards patrol, defend against threats, and engage in combat when necessary.
    """
    
    def __init__(self):
        """Initialize the guard job with appropriate skills and data"""
        super().__init__("guard", "Protects the village and its inhabitants")
        
        # Set skill modifiers - guards get bonuses to these skills
        self.skill_modifiers = {
            "combat": 0.8,       # Major boost to combat
            "perception": 0.3,   # Moderate boost to perception
            "strength": 0.5      # Good boost to strength
        }
        
        # Job-specific data
        self.job_specific_data = {
            "patrol_points": [],       # Points for guard to patrol between
            "current_patrol_point": 0, # Index of current patrol point
            "village_center": None,    # Center of the village to defend
            "current_threat": None,    # Current threat being addressed
            "threat_level": 0.0,       # Current threat level (0-100)
            "threats_defeated": 0,     # Number of threats defeated
            "hours_patrolled": 0.0,    # Total hours spent patrolling
            "on_duty": True            # Whether guard is currently on duty
        }
        
        # Combat equipment and stats
        self.job_specific_data["combat"] = {
            "has_weapon": False,      # Whether guard has a weapon
            "weapon_quality": 0.0,    # Quality of weapon if any
            "damage_dealt": 0.0,      # Total damage dealt to threats
            "damage_taken": 0.0       # Total damage taken from threats
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next guard action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Set up village center if not set
        if not self.job_specific_data["village_center"]:
            self.job_specific_data["village_center"] = (world.width // 2, world.height // 2)
        
        # Set up patrol points if none exist
        if not self.job_specific_data["patrol_points"]:
            self._setup_patrol_points(agent, world)
        
        # First priority: handle active threats if any
        if self.job_specific_data["current_threat"]:
            threat = self.job_specific_data["current_threat"]
            
            # Check if we're at the threat location
            if agent.position == threat["position"]:
                agent._set_action("engage_threat", threat)
            else:
                agent._set_action("go_to_threat", threat["position"])
            return
        
        # Second priority: detect threats nearby
        threats = self._detect_threats(agent, world)
        if threats:
            # Choose the highest priority threat
            threat = self._prioritize_threats(threats)
            self.job_specific_data["current_threat"] = threat
            
            # Go to the threat
            agent._set_action("go_to_threat", threat["position"])
            return
        
        # Third priority: patrol if on duty
        if self.job_specific_data["on_duty"]:
            # Get current patrol point
            patrol_idx = self.job_specific_data["current_patrol_point"]
            if patrol_idx >= len(self.job_specific_data["patrol_points"]):
                patrol_idx = 0
                self.job_specific_data["current_patrol_point"] = 0
            
            patrol_point = self.job_specific_data["patrol_points"][patrol_idx]
            
            # Check if we're at the patrol point
            if agent.position == patrol_point:
                # Move to next patrol point
                self.job_specific_data["current_patrol_point"] = (patrol_idx + 1) % len(self.job_specific_data["patrol_points"])
                next_point = self.job_specific_data["patrol_points"][self.job_specific_data["current_patrol_point"]]
                agent._set_action("patrol_to", next_point)
            else:
                agent._set_action("patrol_to", patrol_point)
            return
        
        # Fourth priority: rest at home or village center if off duty
        if not self.job_specific_data["on_duty"]:
            rest_loc = agent.home_position if agent.home_position else self.job_specific_data["village_center"]
            
            if agent.position == rest_loc:
                agent._set_action("rest", None)
            else:
                agent._set_action("go_to_rest", rest_loc)
            return
        
        # Default: patrol village center
        agent._set_action("patrol_to", self.job_specific_data["village_center"])
    
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
    
    def _setup_patrol_points(self, agent, world):
        """Set up patrol points around the village"""
        village_center = self.job_specific_data["village_center"]
        if not village_center:
            village_center = (world.width // 2, world.height // 2)
            self.job_specific_data["village_center"] = village_center
        
        # Create patrol points in a circle around the village center
        cx, cy = village_center
        radius = min(10, min(world.width, world.height) // 4)  # Reasonable patrol radius
        num_points = random.randint(4, 8)  # Number of patrol points
        
        patrol_points = []
        for i in range(num_points):
            angle = (i / num_points) * 2 * 3.14159  # Convert to radians
            px = int(cx + radius * 0.8 * 1.3 * (0.7 + 0.3 * random.random()) * 
                   (1 if random.random() > 0.5 else -1))
            py = int(cy + radius * 0.8 * (0.7 + 0.3 * random.random()) * 
                   (1 if random.random() > 0.5 else -1))
            
            # Ensure within world bounds
            px = max(0, min(world.width - 1, px))
            py = max(0, min(world.height - 1, py))
            
            patrol_points.append((px, py))
        
        # Add village center as a patrol point
        patrol_points.append(village_center)
        
        # Set patrol points and start with a random one
        self.job_specific_data["patrol_points"] = patrol_points
        self.job_specific_data["current_patrol_point"] = random.randint(0, len(patrol_points) - 1)
    
    def _detect_threats(self, agent, world):
        """Detect nearby threats"""
        # In a more developed system, this would detect actual threat entities
        # For now, return placeholder threats for demonstration
        
        # Guard's perception affects threat detection radius
        perception_skill = agent.skills["perception"]
        detection_radius = 5 + int(perception_skill * 5)  # 5-10 cells based on skill
        
        # For simulation, randomly generate threats with low probability
        detected_threats = []
        
        # Only detect threats with 2% chance per step (to avoid constant threats)
        if random.random() < 0.02:
            # Get neighboring cells to check for threats
            x, y = agent.position
            neighbors = world.get_neighboring_cells(x, y, detection_radius)
            
            # Randomly select a cell for a potential threat
            if neighbors and random.random() < 0.3:  # 30% chance if we're checking
                threat_pos = random.choice(neighbors)
                
                # Create a threat object
                threat = {
                    "id": f"threat_{random.randint(1000, 9999)}",
                    "type": random.choice(["bandit", "wolf", "monster"]),
                    "position": threat_pos,
                    "health": random.uniform(50.0, 100.0),
                    "strength": random.uniform(0.3, 0.8),
                    "damage": random.uniform(5.0, 15.0),
                    "priority": random.uniform(0.5, 1.0)
                }
                
                detected_threats.append(threat)
        
        return detected_threats
    
    def _prioritize_threats(self, threats):
        """Prioritize threats based on their danger level"""
        if not threats:
            return None
        
        # Sort threats by priority (higher is more dangerous)
        sorted_threats = sorted(threats, key=lambda t: t["priority"], reverse=True)
        return sorted_threats[0]
    
    def _progress_patrol_to(self, agent, world, time_delta: float):
        """Progress movement towards a patrol point"""
        patrol_pos = agent.action_target
        if not patrol_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = patrol_pos
        
        # Already at patrol position
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            
            # Update patrol stats
            self.job_specific_data["hours_patrolled"] += time_delta
            
            # Skill improvement from practice
            self.improve_skills(agent, "perception", 0.004)
            
            return {"agent": agent.name, "action": "patrol_checkpoint_reached", "location": patrol_pos}
        
        # Move towards patrol position
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Update patrol stats (partial credit for moving)
        self.job_specific_data["hours_patrolled"] += time_delta * 0.5
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            agent.action_progress = 1.0
        else:
            agent.action_progress = 0.5  # Still in progress
            
        return None
    
    def _progress_rest(self, agent, world, time_delta: float):
        """Rest while off duty"""
        # Resting helps recovery
        agent.health = min(100.0, agent.health + time_delta * 2.0)
        agent.energy = min(100.0, agent.energy + time_delta * 5.0)
        
        # Progress rest action
        agent.action_progress += time_delta * 0.1
        
        # Switch back to on duty after full rest
        if agent.action_progress >= 1.0 or (agent.health > 90.0 and agent.energy > 90.0):
            agent.action_progress = 1.0
            self.job_specific_data["on_duty"] = True
            return {"agent": agent.name, "action": "rest_complete", "status": "back_on_duty"}
        
        return None
    
    def _progress_go_to_rest(self, agent, world, time_delta: float):
        """Go to rest location"""
        rest_pos = agent.action_target
        if not rest_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = rest_pos
        
        # Already at rest position
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            agent._set_action("rest", None)
            return {"agent": agent.name, "action": "arrived_at_rest_location", "location": rest_pos}
        
        # Move towards rest position
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
    
    def _progress_go_to_threat(self, agent, world, time_delta: float):
        """Go to a detected threat"""
        if not self.job_specific_data["current_threat"]:
            agent.action_progress = 1.0
            return None
            
        threat_pos = agent.action_target
        if not threat_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = threat_pos
        
        # Already at threat position
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            agent._set_action("engage_threat", self.job_specific_data["current_threat"])
            return {"agent": agent.name, "action": "arrived_at_threat", "location": threat_pos}
        
        # Move towards threat (faster than normal patrol movement)
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
    
    def _progress_engage_threat(self, agent, world, time_delta: float):
        """Engage in combat with a threat"""
        threat = agent.action_target
        if not threat or not self.job_specific_data["current_threat"]:
            agent.action_progress = 1.0
            self.job_specific_data["current_threat"] = None
            return {"agent": agent.name, "action": "threat_engagement_ended", "reason": "no_threat"}
        
        # In a full implementation, this would have turn-based or real-time combat
        # For now, simulate combat with skill checks
        
        # Combat lasts multiple steps
        if agent.action_progress < 0.9:
            # Calculate combat effectiveness based on skills
            combat_skill = agent.skills["combat"]
            strength_skill = agent.skills["strength"]
            
            # Determine if guard has a weapon
            has_weapon = self.job_specific_data["combat"]["has_weapon"]
            weapon_quality = self.job_specific_data["combat"]["weapon_quality"]
            
            # Combat effectiveness
            guard_effectiveness = 0.3 + (combat_skill * 0.5) + (strength_skill * 0.2)
            if has_weapon:
                guard_effectiveness *= (1.0 + weapon_quality * 0.5)
            
            # Threat effectiveness
            threat_effectiveness = threat["strength"]
            
            # Calculate damage
            damage_to_threat = 10.0 * guard_effectiveness * time_delta * random.uniform(0.8, 1.2)
            damage_to_guard = threat["damage"] * threat_effectiveness * time_delta * random.uniform(0.7, 1.0)
            
            # Apply damage
            threat["health"] -= damage_to_threat
            agent.health -= damage_to_guard
            
            # Log damage for statistics
            self.job_specific_data["combat"]["damage_dealt"] += damage_to_threat
            self.job_specific_data["combat"]["damage_taken"] += damage_to_guard
            
            # Skill improvement from combat
            self.improve_skills(agent, "combat", 0.01)
            self.improve_skills(agent, "strength", 0.005)
            
            # Check if combat is over
            if threat["health"] <= 0:
                # Threat defeated
                agent.action_progress = 1.0
                self.job_specific_data["threats_defeated"] += 1
                self.job_specific_data["current_threat"] = None
                
                return {
                    "agent": agent.name, 
                    "action": "threat_defeated", 
                    "threat_type": threat["type"],
                    "damage_dealt": damage_to_threat,
                    "damage_taken": damage_to_guard
                }
            
            if agent.health <= 20.0:
                # Guard retreating due to low health
                agent.action_progress = 1.0
                self.job_specific_data["on_duty"] = False  # Go off duty to rest
                
                return {
                    "agent": agent.name, 
                    "action": "guard_retreating", 
                    "health": agent.health,
                    "threat_remaining_health": threat["health"]
                }
            
            # Continue combat
            agent.action_progress += time_delta * 0.4
            return {
                "agent": agent.name, 
                "action": "fighting_threat", 
                "damage_dealt": damage_to_threat,
                "damage_taken": damage_to_guard,
                "threat_health": threat["health"]
            }
        else:
            # Combat timeout - threat escapes
            agent.action_progress = 1.0
            self.job_specific_data["current_threat"] = None
            
            return {
                "agent": agent.name, 
                "action": "threat_escaped", 
                "threat_type": threat["type"],
                "remaining_health": threat["health"]
            }
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling guard-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # Clear current threat
        self.job_specific_data["current_threat"] = None
        
        # Call parent remove method
        super().remove_from_agent(agent) 