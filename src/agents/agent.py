import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import pygame
import random
import uuid

from src.utils.config import Config

class NeedType:
    """Types of needs an agent can have"""
    FOOD = "food"
    WATER = "water"
    REST = "rest"
    SHELTER = "shelter"
    SOCIAL = "social"
    
    @staticmethod
    def get_all_needs():
        """Get all available need types"""
        return [NeedType.FOOD, NeedType.WATER, NeedType.REST, 
                NeedType.SHELTER, NeedType.SOCIAL]

class Agent:
    """
    Base class for agents in the medieval village simulation.
    Each agent has needs, skills, and the ability to perform actions.
    """
    
    def __init__(self, config: Config, name: Optional[str] = None):
        """
        Initialize a new agent.
        
        Args:
            config: Configuration object
            name: Optional name for the agent, randomly generated if not provided
        """
        self.config = config
        self.id = str(uuid.uuid4())
        self.name = name or self._generate_name()
        
        # Physical attributes
        self.age = random.randint(18, 50)  # Start as an adult
        self.gender = random.choice(["male", "female"])
        self.health = 100.0  # Max health
        self.position = (0, 0)  # Will be set when added to world
        self.home_position = None  # Will be set later
        self.inventory = {}  # What the agent is carrying
        self.carrying_capacity = 100.0
        
        # Needs system
        self.needs = {
            NeedType.FOOD: 100.0,  # 0 = starving, 100 = full
            NeedType.WATER: 100.0,  # 0 = dehydrated, 100 = hydrated
            NeedType.REST: 100.0,   # 0 = exhausted, 100 = well-rested
            NeedType.SHELTER: 100.0,  # 0 = exposed, 100 = sheltered
            NeedType.SOCIAL: 100.0,   # 0 = lonely, 100 = socially fulfilled
        }
        
        self.need_decay_rates = {
            NeedType.FOOD: 1.0,      # Units per hour
            NeedType.WATER: 2.0,     # Units per hour
            NeedType.REST: 1.5,      # Units per hour when awake
            NeedType.SHELTER: 0.5,   # Units per hour when exposed
            NeedType.SOCIAL: 0.3,    # Units per hour when alone
        }
        
        # Current action/state
        self.current_action = None
        self.action_progress = 0.0
        self.action_target = None
        
        # Job and skills
        self.job = None  # Will be assigned later
        self.skills = {
            "farming": random.uniform(0.1, 0.3),
            "mining": random.uniform(0.1, 0.3),
            "woodcutting": random.uniform(0.1, 0.3),
            "building": random.uniform(0.1, 0.3),
            "crafting": random.uniform(0.1, 0.3),
            "trading": random.uniform(0.1, 0.3),
            "cooking": random.uniform(0.1, 0.3),
        }
        
        # Relationships with other agents
        self.relationships = {}  # agent_id -> relationship value (-100 to 100)
        
        # Memory
        self.memory = []  # List of important events/information
        self.known_locations = {}  # type -> list of positions
    
    def _generate_name(self) -> str:
        """Generate a random name for the agent"""
        first_names_male = ["John", "William", "Robert", "Thomas", "Edward", "Henry", 
                           "Richard", "Walter", "Hugh", "Simon", "Peter", "Geoffrey"]
        first_names_female = ["Alice", "Emma", "Matilda", "Isabella", "Margaret", "Joan",
                             "Agnes", "Eleanor", "Catherine", "Cecily", "Anne", "Elizabeth"]
        surnames = ["Smith", "Miller", "Baker", "Carpenter", "Wright", "Fletcher", "Cook",
                   "Taylor", "Carter", "Shepherd", "Cooper", "Fisher", "Hunter", "Farmer"]
        
        gender = random.choice(["male", "female"])
        if gender == "male":
            first_name = random.choice(first_names_male)
        else:
            first_name = random.choice(first_names_female)
            
        surname = random.choice(surnames)
        return f"{first_name} {surname}"
    
    def step(self, world, time_delta: float):
        """
        Process one time step for the agent.
        
        Args:
            world: Reference to the world
            time_delta: Time elapsed since last step
        
        Returns:
            Action result if any
        """
        # Update needs based on time passed
        self._update_needs(world, time_delta)
        
        # Check if current action is complete
        if self.current_action and self._is_action_complete():
            self._complete_action(world)
            self.current_action = None
            self.action_target = None
            self.action_progress = 0.0
        
        # If no current action, decide what to do next
        if not self.current_action:
            self._decide_next_action(world)
        
        # Progress current action if there is one
        if self.current_action:
            result = self._progress_action(world, time_delta)
            return result
        
        return None
    
    def _update_needs(self, world, time_delta: float):
        """
        Update agent needs based on time passed and current conditions.
        
        Args:
            world: Reference to the world
            time_delta: Time elapsed since last step
        """
        # Time delta is in ticks, convert to hours for need decay
        hours = time_delta / world.time_system.ticks_per_hour
        
        # Decay needs based on time and conditions
        for need_type, current_value in self.needs.items():
            decay_rate = self.need_decay_rates[need_type]
            
            # Modify decay rate based on conditions
            if need_type == NeedType.REST and self.current_action == "sleeping":
                # Resting improves rest need
                self.needs[need_type] = min(100.0, current_value + 10.0 * hours)
                continue
                
            if need_type == NeedType.SHELTER:
                # Only decay shelter need if not in a shelter
                if self._is_in_shelter(world):
                    continue
            
            # Apply decay
            new_value = max(0.0, current_value - decay_rate * hours)
            self.needs[need_type] = new_value
        
        # Update health based on needs
        self._update_health()
    
    def _is_in_shelter(self, world) -> bool:
        """Check if the agent is currently in a shelter"""
        # Simple implementation - will be expanded with actual building checks
        return self.home_position is not None and self.position == self.home_position
    
    def _update_health(self):
        """Update agent health based on current needs"""
        # If any need is critically low, health starts to decrease
        critical_needs = sum(1 for need, value in self.needs.items() 
                            if value < 20.0)
        
        if critical_needs > 0:
            health_loss = 0.5 * critical_needs  # Health points lost per hour with critical needs
            self.health = max(0.0, self.health - health_loss)
        elif self.health < 100.0 and all(value > 50.0 for value in self.needs.values()):
            # Recover health slowly if all needs are moderately satisfied
            self.health = min(100.0, self.health + 0.2)
    
    def _decide_next_action(self, world):
        """
        Decide the next action for the agent based on their current needs and situation.
        
        Args:
            world: Reference to the world
        """
        # Simple decision making - prioritize the lowest need
        lowest_need = min(self.needs.items(), key=lambda x: x[1])
        need_type, need_value = lowest_need
        
        # If any need is below threshold, address it
        if need_value < 30.0:
            if need_type == NeedType.FOOD:
                self._set_action("find_food", None)
            elif need_type == NeedType.WATER:
                self._set_action("find_water", None)
            elif need_type == NeedType.REST:
                if self.home_position:
                    self._set_action("go_home", self.home_position)
                else:
                    self._set_action("find_shelter", None)
            elif need_type == NeedType.SHELTER:
                if self.home_position:
                    self._set_action("go_home", self.home_position)
                else:
                    self._set_action("find_shelter", None)
            elif need_type == NeedType.SOCIAL:
                self._set_action("socialize", None)
        else:
            # If all needs are satisfied, perform job-related activities
            if self.job:
                self.job.decide_action(self, world)
            else:
                # Wander around if no job
                self._set_action("wander", None)
    
    def _set_action(self, action: str, target: Any):
        """
        Set the current action for the agent.
        
        Args:
            action: Action type
            target: Target for the action, if any
        """
        self.current_action = action
        self.action_target = target
        self.action_progress = 0.0
    
    def _is_action_complete(self) -> bool:
        """Check if the current action is complete"""
        return self.action_progress >= 1.0
    
    def _complete_action(self, world):
        """
        Complete the current action and apply its effects.
        
        Args:
            world: Reference to the world
        """
        # Apply effects based on action type
        if self.current_action == "find_food" and self.action_target:
            self._consume_food()
        elif self.current_action == "find_water" and self.action_target:
            self._consume_water()
        elif self.current_action == "sleeping":
            # Rest need is already updated during the action
            pass
    
    def _progress_action(self, world, time_delta: float):
        """
        Progress the current action.
        
        Args:
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of progressing the action
        """
        # Action specific logic
        if self.current_action == "wander":
            return self._progress_wander(world, time_delta)
        elif self.current_action == "go_home":
            return self._progress_go_home(world, time_delta)
        elif self.current_action == "find_food":
            return self._progress_find_food(world, time_delta)
        elif self.current_action == "find_water":
            return self._progress_find_water(world, time_delta)
        elif self.current_action == "sleeping":
            return self._progress_sleeping(world, time_delta)
        elif self.current_action == "find_shelter":
            return self._progress_find_shelter(world, time_delta)
        elif self.current_action == "socialize":
            return self._progress_socialize(world, time_delta)
        
        # For job-specific actions, delegate to the job
        if self.job:
            return self.job.progress_action(self, world, time_delta)
            
        return None
    
    def _progress_wander(self, world, time_delta: float):
        """Progress the wandering action"""
        # Simple random movement
        current_x, current_y = self.position
        
        # Pick a random direction
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        
        # Try to move
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(self, new_x, new_y)
        
        # Wandering is always "in progress" until interrupted
        self.action_progress = 0.5
        return None
    
    def _progress_go_home(self, world, time_delta: float):
        """Progress the go home action"""
        if self.home_position is None:
            # Can't go home if we don't have one
            self.action_progress = 1.0
            return None
            
        current_x, current_y = self.position
        target_x, target_y = self.home_position
        
        # Already at home
        if current_x == target_x and current_y == target_y:
            self.action_progress = 1.0
            # Start sleeping when we get home if we're tired
            if self.needs[NeedType.REST] < 50.0:
                self._set_action("sleeping", None)
            return None
        
        # Move towards home
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(self, new_x, new_y)
        
        # Check if we've arrived
        if new_x == target_x and new_y == target_y:
            self.action_progress = 1.0
        else:
            self.action_progress = 0.5  # Still in progress
            
        return None
    
    def _progress_find_food(self, world, time_delta: float):
        """Progress the find food action"""
        # Check if we already have food in inventory
        if "food" in self.inventory and self.inventory["food"] > 0:
            self._consume_food()
            self.action_progress = 1.0
            return None
        
        # Look for food resources in the current location
        x, y = self.position
        resources = world.resource_manager.get_resources_at(x, y)
        
        food_resources = [r for r in resources if "FOOD" in r.resource_type.name]
        if food_resources:
            # Found food, extract and consume it
            food = food_resources[0]
            amount = food.extract(10.0)  # Extract some food
            
            if amount > 0:
                self.inventory["food"] = self.inventory.get("food", 0) + amount
                self._consume_food()
                self.action_progress = 1.0
                return {"agent": self.name, "action": "gathered_food", "amount": amount}
        
        # No food here, wander to look for food
        self._progress_wander(world, time_delta)
        return None
    
    def _progress_find_water(self, world, time_delta: float):
        """Progress the find water action"""
        # Check if we already have water in inventory
        if "water" in self.inventory and self.inventory["water"] > 0:
            self._consume_water()
            self.action_progress = 1.0
            return None
        
        # Look for water resources in the current location
        x, y = self.position
        resources = world.resource_manager.get_resources_at(x, y)
        
        water_resources = [r for r in resources if r.resource_type.name == "WATER"]
        if water_resources:
            # Found water, extract and consume it
            water = water_resources[0]
            amount = water.extract(10.0)  # Extract some water
            
            if amount > 0:
                self.inventory["water"] = self.inventory.get("water", 0) + amount
                self._consume_water()
                self.action_progress = 1.0
                return {"agent": self.name, "action": "gathered_water", "amount": amount}
        
        # No water here, wander to look for water
        self._progress_wander(world, time_delta)
        return None
    
    def _progress_sleeping(self, world, time_delta: float):
        """Progress the sleeping action"""
        # Ensure we're at home
        if self.position != self.home_position:
            self._set_action("go_home", self.home_position)
            return None
        
        # Convert time_delta to hours for rest improvement
        hours = time_delta / world.time_system.ticks_per_hour
        
        # Rest need is already updated in _update_needs, but we can add logic here if needed
        
        # Complete sleeping if fully rested
        if self.needs[NeedType.REST] >= 95.0:
            self.action_progress = 1.0
        else:
            self.action_progress = 0.5  # Still sleeping
            
        return None
    
    def _progress_find_shelter(self, world, time_delta: float):
        """Progress the find shelter action"""
        # This is a simplified implementation
        # In a more complex simulation, the agent would look for actual buildings
        
        # For now, just find a random "home" position if we don't have one
        if self.home_position is None:
            # Pick a random position for now
            self.home_position = (
                random.randint(0, world.width - 1),
                random.randint(0, world.height - 1)
            )
            
        # Now go home
        self._set_action("go_home", self.home_position)
        return None
    
    def _progress_socialize(self, world, time_delta: float):
        """Progress the socialize action"""
        # Look for other agents nearby
        x, y = self.position
        neighbors = world.get_neighboring_cells(x, y, 2)
        
        other_agents = []
        for nx, ny in neighbors:
            entities = world.get_entities_at(nx, ny)
            agents = [e for e in entities if isinstance(e, Agent) and e != self]
            other_agents.extend(agents)
        
        if other_agents:
            # Found someone to socialize with
            other = random.choice(other_agents)
            
            # Socialize (update relationships and social need)
            self._socialize_with(other)
            self.action_progress = 1.0
            
            return {"agent": self.name, "action": "socialized", "with": other.name}
        else:
            # No one to socialize with, wander to find someone
            self._progress_wander(world, time_delta)
            return None
    
    def _socialize_with(self, other_agent):
        """
        Socialize with another agent.
        
        Args:
            other_agent: The agent to socialize with
        """
        # Update social need
        social_gain = 20.0
        self.needs[NeedType.SOCIAL] = min(100.0, self.needs[NeedType.SOCIAL] + social_gain)
        
        # Update relationship
        other_id = other_agent.id
        if other_id not in self.relationships:
            # First meeting, start with a slightly positive or negative bias
            initial_opinion = random.uniform(-10, 10)
            self.relationships[other_id] = initial_opinion
        
        # Improve relationship slightly (more complex social dynamics will be added later)
        relationship_change = random.uniform(0.5, 2.0)
        self.relationships[other_id] = min(100.0, self.relationships[other_id] + relationship_change)
    
    def _consume_food(self):
        """Consume food from inventory to satisfy hunger"""
        if "food" in self.inventory and self.inventory["food"] > 0:
            amount_to_consume = min(10.0, self.inventory["food"])
            self.inventory["food"] -= amount_to_consume
            
            # Food effectiveness based on quality (simplified)
            food_effectiveness = 5.0  # Points of need satisfied per unit of food
            
            # Improve food need
            self.needs[NeedType.FOOD] = min(100.0, self.needs[NeedType.FOOD] + amount_to_consume * food_effectiveness)
            
            # Remove from inventory if depleted
            if self.inventory["food"] <= 0:
                del self.inventory["food"]
    
    def _consume_water(self):
        """Consume water from inventory to satisfy thirst"""
        if "water" in self.inventory and self.inventory["water"] > 0:
            amount_to_consume = min(10.0, self.inventory["water"])
            self.inventory["water"] -= amount_to_consume
            
            # Water effectiveness
            water_effectiveness = 8.0  # Points of need satisfied per unit of water
            
            # Improve water need
            self.needs[NeedType.WATER] = min(100.0, self.needs[NeedType.WATER] + amount_to_consume * water_effectiveness)
            
            # Remove from inventory if depleted
            if self.inventory["water"] <= 0:
                del self.inventory["water"]
    
    def get_state(self) -> Dict:
        """
        Get the current state of the agent for observation.
        
        Returns:
            Dictionary with the agent's current state
        """
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "health": self.health,
            "needs": self.needs.copy(),
            "action": self.current_action,
            "inventory": self.inventory.copy(),
            "skills": self.skills.copy()
        }
    
    def render(self, surface: pygame.Surface):
        """Render the agent on a pygame surface"""
        # Get agent position
        x, y = self.position
        
        # Get cell size (assuming it's calculated elsewhere)
        cell_size = 20  # Placeholder
        
        # Determine agent color based on job or gender
        if self.job:
            # Color by job (will be implemented when jobs are implemented)
            color = (0, 0, 255)  # Default blue
        else:
            # Color by gender
            color = (0, 0, 255) if self.gender == "male" else (255, 0, 255)
        
        # Draw agent
        pygame.draw.circle(
            surface, 
            color,
            (x * cell_size + cell_size // 2, y * cell_size + cell_size // 2),
            cell_size // 3
        )
        
        # Draw health indicator
        health_width = int(cell_size * (self.health / 100.0))
        pygame.draw.rect(
            surface,
            (0, 255, 0),  # Green for health
            (x * cell_size, y * cell_size - 2, health_width, 2)
        ) 