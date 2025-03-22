import random
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

class ThreatType(Enum):
    """Types of threats that can endanger the village"""
    RAIDERS = 1        # Bandits or hostile human groups
    WOLVES = 2         # Pack of wolves
    BEAR = 3           # Large predator
    ORC_PARTY = 4      # Small group of orcs
    ORC_RAIDING_PARTY = 5  # Larger group of orcs
    TROLL = 6          # Single strong monster
    DRAGON = 7         # Extremely dangerous

    @classmethod
    def get_difficulty(cls, threat_type):
        """Get difficulty rating for a threat type (1-10 scale)"""
        difficulty_map = {
            cls.RAIDERS: 3,
            cls.WOLVES: 2,
            cls.BEAR: 4,
            cls.ORC_PARTY: 5,
            cls.ORC_RAIDING_PARTY: 7,
            cls.TROLL: 6,
            cls.DRAGON: 10
        }
        return difficulty_map.get(threat_type, 1)
    
    @classmethod
    def get_resource_targets(cls, threat_type):
        """Get the resources this threat type tends to target"""
        target_map = {
            cls.RAIDERS: ["FOOD_WHEAT", "IRON_INGOT", "BASIC_TOOLS", "WEAPONS"],
            cls.WOLVES: ["FOOD_WHEAT"],
            cls.BEAR: ["FOOD_WHEAT", "FOOD_BERRY"],
            cls.ORC_PARTY: ["FOOD_WHEAT", "WEAPONS"],
            cls.ORC_RAIDING_PARTY: ["FOOD_WHEAT", "IRON_INGOT", "WEAPONS", "ADVANCED_TOOLS"],
            cls.TROLL: ["FOOD_WHEAT", "STONE"],
            cls.DRAGON: ["FOOD_WHEAT", "IRON_INGOT", "WEAPONS", "ADVANCED_TOOLS"]
        }
        return target_map.get(threat_type, ["FOOD_WHEAT"])

class ThreatStatus(Enum):
    """Status of a threat"""
    APPROACHING = 1    # Detected but not yet arrived
    ATTACKING = 2      # Currently attacking the village
    DEFEATED = 3       # Has been eliminated
    FLED = 4           # Has been driven away
    VICTORIOUS = 5     # Has successfully raided and left

class Threat:
    """Represents a threat to the village"""
    
    def __init__(self, threat_type: ThreatType, position: Tuple[int, int], strength: float = 1.0):
        """
        Initialize a threat.
        
        Args:
            threat_type: Type of the threat
            position: (x, y) position in the world grid
            strength: Strength multiplier (1.0 is baseline)
        """
        self.threat_type = threat_type
        self.position = position
        self.strength = strength
        self.status = ThreatStatus.APPROACHING
        self.target_position = None  # Target within village
        self.approach_time = random.randint(3, 12)  # Hours until arrival
        self.aggression = 0.5 + (random.random() * 0.5)  # 0.5-1.0, higher = more aggressive
        self.loot = {}  # Resources stolen
        self.health = 100.0 * strength
        self.damage_done = 0.0
        self.id = random.randint(1000, 9999)
        
        # Calculated properties
        self.base_strength = self._calculate_base_strength()
        self.size = self._calculate_size()
        
    def _calculate_base_strength(self) -> float:
        """Calculate the base strength value based on threat type"""
        difficulty = ThreatType.get_difficulty(self.threat_type)
        return difficulty * 10.0  # 10-100 base strength
    
    def _calculate_size(self) -> int:
        """Calculate the size of the threat (number of individual units)"""
        if self.threat_type in [ThreatType.BEAR, ThreatType.TROLL, ThreatType.DRAGON]:
            return 1  # Single large creature
        elif self.threat_type == ThreatType.WOLVES:
            return random.randint(3, 8)  # Pack of wolves
        elif self.threat_type == ThreatType.RAIDERS:
            return random.randint(4, 10)  # Group of raiders
        elif self.threat_type == ThreatType.ORC_PARTY:
            return random.randint(3, 6)  # Small orc group
        elif self.threat_type == ThreatType.ORC_RAIDING_PARTY:
            return random.randint(8, 15)  # Large orc group
        return 1
    
    def approach(self, time_delta: float) -> bool:
        """
        Progress the approach of the threat toward the village.
        
        Args:
            time_delta: Time elapsed in hours
            
        Returns:
            True if the threat has arrived, False otherwise
        """
        if self.status != ThreatStatus.APPROACHING:
            return False
            
        self.approach_time -= time_delta
        
        if self.approach_time <= 0:
            self.status = ThreatStatus.ATTACKING
            return True
            
        return False
    
    def take_damage(self, damage: float) -> bool:
        """
        Apply damage to the threat.
        
        Args:
            damage: Amount of damage to apply
            
        Returns:
            True if the threat is defeated, False otherwise
        """
        self.health -= damage
        
        # Check if we should flee
        if self.health <= self.base_strength * 0.3 and random.random() > self.aggression:
            self.status = ThreatStatus.FLED
            return True
            
        # Check if defeated
        if self.health <= 0:
            self.status = ThreatStatus.DEFEATED
            self.health = 0
            return True
            
        return False
    
    def attack_village(self, world, time_delta: float) -> Dict[str, Any]:
        """
        Process an attack on the village.
        
        Args:
            world: Reference to the world
            time_delta: Time elapsed in hours
            
        Returns:
            Dictionary with attack results
        """
        if self.status != ThreatStatus.ATTACKING:
            return {"status": "not_attacking"}
            
        # Determine damage output based on strength
        damage_potential = self.base_strength * self.strength * time_delta
        
        # Target buildings or resources
        if not self.target_position:
            self._select_target(world)
            
        # If we have a target, move toward it
        if self.target_position:
            self._move_toward_target(world)
            
        # Check if at target position
        at_target = self.position == self.target_position
        
        # Process looting
        loot_results = {}
        if at_target:
            loot_results = self._process_looting(world, damage_potential)
            
            # Select a new target
            self.target_position = None
            self._select_target(world)
        
        # Return attack results
        return {
            "status": "attacking",
            "position": self.position,
            "damage_done": self.damage_done,
            "loot": loot_results
        }
    
    def _select_target(self, world):
        """Select a target position within the village"""
        # Priority targets: resource storage, food, buildings
        
        # First, check if there are buildings
        if world.buildings:
            # 70% chance to target a building
            if random.random() < 0.7:
                target_building = random.choice(world.buildings)
                self.target_position = target_building.position
                return
        
        # Otherwise, target the center of the village or a random position
        if hasattr(world, 'village_center'):
            self.target_position = world.village_center
        else:
            # Default to center of map
            self.target_position = (world.width // 2, world.height // 2)
    
    def _move_toward_target(self, world):
        """Move toward the target position"""
        current_x, current_y = self.position
        target_x, target_y = self.target_position
        
        # Move toward target
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        
        # Ensure we're within world bounds
        new_x = max(0, min(world.width - 1, new_x))
        new_y = max(0, min(world.height - 1, new_y))
        
        self.position = (new_x, new_y)
    
    def _process_looting(self, world, damage_potential: float) -> Dict[str, float]:
        """
        Process resource looting and building damage.
        
        Args:
            world: Reference to the world
            damage_potential: Potential damage that can be done
            
        Returns:
            Dictionary of resources looted
        """
        loot_results = {}
        
        # Check if there's a building at this location
        buildings_at_location = [b for b in world.buildings if b.position == self.position]
        
        if buildings_at_location:
            # Damage building
            building = buildings_at_location[0]
            damage = min(damage_potential, building.condition)
            building.condition -= damage
            self.damage_done += damage
            
            # If building destroyed, potentially loot resources
            if building.condition <= 0:
                # Building destroyed - loot some resources
                resources_to_loot = ThreatType.get_resource_targets(self.threat_type)
                
                for resource_name in resources_to_loot:
                    # Try to convert string to ResourceType enum
                    try:
                        from src.environment.resources import ResourceType
                        resource_type = getattr(ResourceType, resource_name)
                        
                        # Take some resources
                        amount = min(
                            world.resource_manager.village_resources.get(resource_type, 0),
                            random.randint(5, 20) * self.strength
                        )
                        
                        if amount > 0:
                            taken = world.resource_manager.take_from_village_storage(resource_type, amount)
                            if taken > 0:
                                if resource_type not in self.loot:
                                    self.loot[resource_type] = 0
                                self.loot[resource_type] += taken
                                loot_results[resource_name] = taken
                    except (AttributeError, ImportError):
                        continue
        else:
            # No building, just try to loot resources
            resources_to_loot = ThreatType.get_resource_targets(self.threat_type)
            
            for resource_name in resources_to_loot:
                # Try to convert string to ResourceType enum
                try:
                    from src.environment.resources import ResourceType
                    resource_type = getattr(ResourceType, resource_name)
                    
                    # Take some resources
                    amount = min(
                        world.resource_manager.village_resources.get(resource_type, 0),
                        random.randint(3, 10) * self.strength
                    )
                    
                    if amount > 0:
                        taken = world.resource_manager.take_from_village_storage(resource_type, amount)
                        if taken > 0:
                            if resource_type not in self.loot:
                                self.loot[resource_type] = 0
                            self.loot[resource_type] += taken
                            loot_results[resource_name] = taken
                except (AttributeError, ImportError):
                    continue
        
        # Check if we've looted enough and should leave
        total_loot = sum(self.loot.values())
        if total_loot > self.base_strength * 5 * self.strength:
            self.status = ThreatStatus.VICTORIOUS
            
        return loot_results
    
    def render(self, surface, cell_size: int):
        """Render the threat on the given surface"""
        import pygame
        
        x, y = self.position
        
        # Different colors for different threat types
        color_map = {
            ThreatType.RAIDERS: (139, 0, 0),      # Dark red
            ThreatType.WOLVES: (105, 105, 105),   # Gray
            ThreatType.BEAR: (101, 67, 33),       # Brown
            ThreatType.ORC_PARTY: (0, 100, 0),    # Dark green
            ThreatType.ORC_RAIDING_PARTY: (0, 128, 0),  # Green
            ThreatType.TROLL: (72, 61, 139),      # Dark slate blue
            ThreatType.DRAGON: (255, 0, 0)        # Red
        }
        
        color = color_map.get(self.threat_type, (255, 0, 0))
        
        # Draw threat icon - size based on difficulty
        difficulty = ThreatType.get_difficulty(self.threat_type)
        size = int(cell_size * (0.3 + (difficulty / 20)))
        
        pygame.draw.polygon(
            surface, 
            color,
            [
                (x * cell_size + cell_size // 2, y * cell_size + cell_size // 2 - size),
                (x * cell_size + cell_size // 2 - size, y * cell_size + cell_size // 2 + size // 2),
                (x * cell_size + cell_size // 2 + size, y * cell_size + cell_size // 2 + size // 2)
            ]
        )
        
        # Draw health bar
        health_percent = self.health / (self.base_strength * self.strength)
        if health_percent < 1.0:
            bar_width = int(cell_size * 0.8 * health_percent)
            pygame.draw.rect(
                surface,
                (255, 0, 0),
                (x * cell_size + cell_size // 10, y * cell_size, bar_width, cell_size // 10)
            )

class ThreatManager:
    """Manages threats to the village"""
    
    def __init__(self, world, config):
        """
        Initialize the threat manager.
        
        Args:
            world: Reference to the world
            config: Configuration parameters
        """
        self.world = world
        self.config = config
        self.threats = []
        self.defeated_threats = []
        self.active_threats = []
        
        # Threat generation parameters
        self.base_threat_chance = config.get('base_threat_chance', 0.01)  # Chance per day
        self.threat_scaling_factor = config.get('threat_scaling_factor', 0.02)  # Increases with village size
        self.last_threat_day = 0
        
        # Min days between threats (to avoid overwhelming the village)
        self.min_days_between_threats = config.get('min_days_between_threats', 10)
        
        # Seasonal modifiers
        self.seasonal_threat_modifiers = {
            "spring": 0.8,   # Lower threat chance
            "summer": 1.0,   # Normal
            "autumn": 1.2,   # Higher chance
            "winter": 1.5    # Highest chance (food scarcity)
        }
    
    def step(self, time_delta: float):
        """
        Process a time step for all threats.
        
        Args:
            time_delta: Time elapsed in hours
        """
        # Check for new threats - once per day at midnight
        if (self.world.time_system.get_hour() == 0 and 
            self.world.time_system.get_minute() == 0):
            self._check_for_new_threats()
        
        # Update existing threats
        for threat in list(self.threats):
            if threat.status == ThreatStatus.APPROACHING:
                # Check if threat has arrived
                if threat.approach(time_delta):
                    # Alert village
                    self.active_threats.append(threat)
                    print(f"Alert! {threat.threat_type.name} approaching from the {self._get_direction_name(threat.position)}!")
            
            elif threat.status == ThreatStatus.ATTACKING:
                # Process attack
                attack_results = threat.attack_village(self.world, time_delta)
                
                # Check for status changes
                if threat.status in [ThreatStatus.DEFEATED, ThreatStatus.FLED, ThreatStatus.VICTORIOUS]:
                    self.active_threats.remove(threat)
                    self.defeated_threats.append(threat)
                    self.threats.remove(threat)
                    
                    status_message = "was defeated!" if threat.status == ThreatStatus.DEFEATED else \
                                    "has fled!" if threat.status == ThreatStatus.FLED else \
                                    "has successfully raided the village!"
                    
                    print(f"The {threat.threat_type.name} {status_message}")
            
            elif threat.status in [ThreatStatus.DEFEATED, ThreatStatus.FLED, ThreatStatus.VICTORIOUS]:
                # Remove from active threats
                if threat in self.active_threats:
                    self.active_threats.remove(threat)
                if threat not in self.defeated_threats:
                    self.defeated_threats.append(threat)
                if threat in self.threats:
                    self.threats.remove(threat)
    
    def _check_for_new_threats(self):
        """Check for and potentially generate new threats"""
        current_day = self.world.time_system.get_total_day()
        
        # Don't generate threats too frequently
        if current_day - self.last_threat_day < self.min_days_between_threats:
            return
            
        # Base chance adjusted by season and village size
        season = self.world.time_system.get_season()
        season_modifier = self.seasonal_threat_modifiers.get(season, 1.0)
        
        # Increases with village size/value
        village_size_factor = min(3.0, 1.0 + (len(self.world.agents) * self.threat_scaling_factor))
        
        # Calculate final threat chance
        threat_chance = self.base_threat_chance * season_modifier * village_size_factor
        
        # Check if a threat occurs
        if random.random() < threat_chance:
            self._generate_threat()
            self.last_threat_day = current_day
    
    def _generate_threat(self):
        """Generate a new threat based on village size and progress"""
        # Select a threat type based on village progression
        village_strength = self._estimate_village_strength()
        possible_threats = self._get_possible_threats(village_strength)
        
        threat_type = random.choice(possible_threats)
        
        # Determine threat position - on the edge of the map
        position = self._generate_edge_position()
        
        # Create the threat with appropriate strength scaling
        strength_factor = 0.7 + (random.random() * 0.6)  # 0.7-1.3 random factor
        adjusted_strength = max(0.5, min(2.0, strength_factor * (village_strength / 50.0)))
        
        threat = Threat(threat_type, position, adjusted_strength)
        self.threats.append(threat)
        
        print(f"Warning! Scouts report a {threat.threat_type.name} approaching from the {self._get_direction_name(position)}!")
        
        return threat
    
    def _estimate_village_strength(self) -> float:
        """Estimate the village's overall strength for threat scaling"""
        # Base on number of guards, weapons, defenses
        guard_count = sum(1 for agent in self.world.agents if agent.job and agent.job.name == "guard")
        
        # Check for weapons and tools
        village_resources = self.world.resource_manager.get_village_resources()
        from src.environment.resources import ResourceType
        weapons = village_resources.get(ResourceType.WEAPONS, 0)
        tools = village_resources.get(ResourceType.BASIC_TOOLS, 0) + village_resources.get(ResourceType.ADVANCED_TOOLS, 0)
        
        # Calculate strength
        base_strength = 10.0 + (len(self.world.agents) * 2.0)  # Base strength from population
        guard_strength = guard_count * 15.0  # Significant bonus from guards
        weapon_strength = weapons * 5.0  # Bonus from weapons
        tool_strength = tools * 1.0  # Minor bonus from tools that can be used as weapons
        
        return base_strength + guard_strength + weapon_strength + tool_strength
    
    def _get_possible_threats(self, village_strength: float) -> List[ThreatType]:
        """Determine which threat types are appropriate for the village's strength"""
        possible_threats = []
        
        # Early village (strength < 50)
        if village_strength < 50:
            possible_threats.extend([ThreatType.WOLVES, ThreatType.RAIDERS])
            
        # Developing village (strength 50-100)
        if 50 <= village_strength < 100:
            possible_threats.extend([ThreatType.WOLVES, ThreatType.RAIDERS, ThreatType.BEAR])
            
        # Established village (strength 100-200)
        if 100 <= village_strength < 200:
            possible_threats.extend([ThreatType.RAIDERS, ThreatType.BEAR, ThreatType.ORC_PARTY])
            
        # Strong village (strength 200-300)
        if 200 <= village_strength < 300:
            possible_threats.extend([ThreatType.ORC_PARTY, ThreatType.TROLL])
            
        # Powerful village (strength 300+)
        if village_strength >= 300:
            possible_threats.extend([ThreatType.ORC_RAIDING_PARTY, ThreatType.TROLL, ThreatType.DRAGON])
        
        # Ensure we always have at least one type
        if not possible_threats:
            possible_threats = [ThreatType.WOLVES]
            
        return possible_threats
    
    def _generate_edge_position(self) -> Tuple[int, int]:
        """Generate a position on the edge of the map"""
        edge = random.choice(["north", "east", "south", "west"])
        
        if edge == "north":
            return (random.randint(0, self.world.width - 1), 0)
        elif edge == "east":
            return (self.world.width - 1, random.randint(0, self.world.height - 1))
        elif edge == "south":
            return (random.randint(0, self.world.width - 1), self.world.height - 1)
        else:  # west
            return (0, random.randint(0, self.world.height - 1))
    
    def _get_direction_name(self, position: Tuple[int, int]) -> str:
        """Get a cardinal direction name based on position relative to village center"""
        x, y = position
        center_x, center_y = self.world.width // 2, self.world.height // 2
        
        dx, dy = x - center_x, y - center_y
        
        # Determine predominant direction
        if abs(dx) > abs(dy):
            # East-West predominant
            return "east" if dx > 0 else "west"
        else:
            # North-South predominant
            return "north" if dy < 0 else "south"
    
    def get_active_threats(self) -> List[Threat]:
        """Get all active threats"""
        return self.active_threats
    
    def get_threat_by_id(self, threat_id: int) -> Optional[Threat]:
        """Find a threat by its ID"""
        for threat in self.threats + self.defeated_threats:
            if threat.id == threat_id:
                return threat
        return None
    
    def get_threats_near(self, position: Tuple[int, int], radius: int) -> List[Threat]:
        """Get threats within a certain radius of a position"""
        x, y = position
        nearby_threats = []
        
        for threat in self.threats:
            tx, ty = threat.position
            if abs(tx - x) <= radius and abs(ty - y) <= radius:
                nearby_threats.append(threat)
                
        return nearby_threats
    
    def damage_threat(self, threat_id: int, damage: float) -> bool:
        """
        Apply damage to a specific threat.
        
        Args:
            threat_id: ID of the threat to damage
            damage: Amount of damage to apply
            
        Returns:
            True if the threat was defeated, False otherwise
        """
        threat = self.get_threat_by_id(threat_id)
        if not threat:
            return False
            
        return threat.take_damage(damage)
    
    def render(self, surface):
        """Render all active threats"""
        cell_size = self.config.cell_size
        
        for threat in self.threats:
            if threat.status in [ThreatStatus.APPROACHING, ThreatStatus.ATTACKING]:
                threat.render(surface, cell_size) 