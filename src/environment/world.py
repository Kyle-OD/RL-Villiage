import numpy as np
from typing import Dict, List, Tuple, Optional
from gymnasium import spaces
import pygame

from src.utils.config import Config
from src.environment.resources import ResourceManager
from src.environment.time_system import TimeSystem
from src.environment.threats import ThreatManager
from src.environment.storage import StorageManager, Warehouse, Granary, Stockpile, Armory
from src.jobs.job_manager import JobManager

class World:
    """
    The main world environment for the medieval village simulation.
    Implements a 2D grid-based world with resources and agents.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the world with configuration parameters.
        
        Args:
            config: Configuration object containing world parameters
        """
        self.config = config
        self.width = config.world_width
        self.height = config.world_height
        
        # Initialize grid - each cell can contain multiple entities
        self.grid = [[[] for _ in range(self.height)] for _ in range(self.width)]
        
        # Initialize systems
        self.time_system = TimeSystem(config)
        self.resource_manager = ResourceManager(self, config)
        self.job_manager = JobManager(config)
        self.threat_manager = ThreatManager(self, config)
        self.storage_manager = StorageManager(self)
        
        # Entity tracking
        self.agents = []
        self.buildings = []
        
        # Village center location
        self.village_center = (self.width // 2, self.height // 2)
        
        # Initialize resources on the map
        self._initialize_resources()
        
        # Set up initial village structures
        self._initialize_village()
    
    def _initialize_resources(self):
        """Initialize resources throughout the world based on config"""
        self.resource_manager.generate_initial_resources()
    
    def _initialize_village(self):
        """Initialize the basic village layout with some starting buildings"""
        # Place a central warehouse at village center
        center_x, center_y = self.village_center
        
        # Create initial storage buildings
        warehouse = Warehouse((center_x, center_y))
        self.storage_manager.add_facility(warehouse)
        
        # Add a granary nearby
        granary_pos = (center_x + 3, center_y)
        granary = Granary(granary_pos)
        self.storage_manager.add_facility(granary)
        
        # Add a stockpile
        stockpile_pos = (center_x - 3, center_y)
        stockpile = Stockpile(stockpile_pos)
        self.storage_manager.add_facility(stockpile)
        
        # Distribute initial resources to appropriate storage
        self._distribute_initial_resources()
    
    def _distribute_initial_resources(self):
        """Distribute the initial resources from village storage to physical storage facilities"""
        initial_resources = self.resource_manager.village_resources.copy()
        
        # Clear village resources (we'll add back anything that can't be stored)
        self.resource_manager.village_resources = {}
        
        # Add to storage facilities
        for resource_type, amount in initial_resources.items():
            added = self.storage_manager.add_resource(resource_type, amount)
            
            # If not all could be added, keep remainder in village resources
            if added < amount:
                self.resource_manager.add_to_village_storage(resource_type, amount - added)
    
    def step(self):
        """
        Advance the world by one time step.
        Updates time, resources, and allows agents to take actions.
        """
        # Update time
        self.time_system.step()
        
        # Update resources (growth, depletion)
        self.resource_manager.step(self.time_system)
        
        # Process environmental effects (weather, seasons)
        self._process_environmental_effects()
        
        # Process threats
        self._process_threats()
        
        # Update village job needs - do this once per in-game hour
        if self.time_system.get_tick() % self.time_system.ticks_per_hour == 0:
            self.job_manager.update_village_needs(self)
            
            # Evaluate job changes - once per day, at dawn
            if self.time_system.get_hour() == 6:
                self._evaluate_job_changes()
    
    def _evaluate_job_changes(self):
        """Evaluate whether agents should change jobs based on village needs"""
        for agent in self.agents:
            if self.job_manager.should_change_job(agent, self):
                self.job_manager.assign_new_job(agent, self)
    
    def _process_environmental_effects(self):
        """Process environmental effects based on season and weather"""
        # Will be implemented in future phases
        pass
    
    def _process_threats(self):
        """Process threats to the village"""
        # Calculate time delta in hours
        hours_passed = 1.0 / self.time_system.ticks_per_hour
        
        # Update threats
        self.threat_manager.step(hours_passed)
        
        # Process guard response to threats
        active_threats = self.threat_manager.get_active_threats()
        if active_threats:
            self._mobilize_guards(active_threats)
    
    def _mobilize_guards(self, threats):
        """
        Direct guards to respond to threats.
        
        Args:
            threats: List of active threats
        """
        # Find all guard agents
        guard_agents = [agent for agent in self.agents 
                       if agent.job and agent.job.name == "guard"]
        
        if not guard_agents:
            return  # No guards to mobilize
            
        # Assign guards to threats based on proximity
        for guard in guard_agents:
            # Check if guard is already engaged with a threat
            if guard.current_action == "engage_threat":
                continue
                
            # Find closest threat
            closest_threat = None
            min_distance = float('inf')
            
            for threat in threats:
                if threat.status != ThreatStatus.ATTACKING:
                    continue
                    
                gx, gy = guard.position
                tx, ty = threat.position
                distance = abs(gx - tx) + abs(gy - ty)  # Manhattan distance
                
                if distance < min_distance:
                    min_distance = distance
                    closest_threat = threat
            
            # If a threat is found, direct guard to it
            if closest_threat:
                # Use the guard's job's action system
                if hasattr(guard.job, 'detect_threat'):
                    guard.job.detect_threat(guard, closest_threat)
    
    def add_agent(self, agent, x: int, y: int):
        """Add an agent to the world at the specified position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[x][y].append(agent)
            self.agents.append(agent)
            agent.position = (x, y)
            
            # Register agent with job manager if they have a job
            if agent.job:
                self.job_manager.register_agent(agent)
                
            return True
        return False
    
    def add_building(self, building, x: int, y: int):
        """Add a building to the world at the specified position"""
        # Check if building can be placed (size considerations)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[x][y].append(building)
            self.buildings.append(building)
            building.position = (x, y)
            return True
        return False
    
    def move_agent(self, agent, new_x: int, new_y: int):
        """Move an agent from current position to a new position"""
        old_x, old_y = agent.position
        
        # Validate new position
        if not (0 <= new_x < self.width and 0 <= new_y < self.height):
            return False
        
        # Remove from old position
        if agent in self.grid[old_x][old_y]:
            self.grid[old_x][old_y].remove(agent)
        
        # Add to new position
        self.grid[new_x][new_y].append(agent)
        agent.position = (new_x, new_y)
        return True
    
    def get_entities_at(self, x: int, y: int) -> List:
        """Get all entities at a specific position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return []
    
    def get_neighboring_cells(self, x: int, y: int, distance: int = 1) -> List[Tuple[int, int]]:
        """Get coordinates of neighboring cells within a certain distance"""
        neighbors = []
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                nx, ny = x + dx, y + dy
                if (dx != 0 or dy != 0) and 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))
        return neighbors
    
    def get_threats_in_range(self, position: Tuple[int, int], detection_range: int = 10) -> List:
        """
        Get threats within a detection range of a position.
        
        Args:
            position: (x, y) position to search from
            detection_range: Range to search within
            
        Returns:
            List of threats within range
        """
        return self.threat_manager.get_threats_near(position, detection_range)
    
    def get_storage_facilities_in_range(self, position: Tuple[int, int], range_distance: int = 5) -> List:
        """
        Get storage facilities within a certain range of a position.
        
        Args:
            position: (x, y) position to search from
            range_distance: Range to search within
            
        Returns:
            List of storage facilities within range
        """
        return self.storage_manager.get_facilities_near(position, range_distance)
    
    def add_resource_to_storage(self, resource_type, amount: float) -> float:
        """
        Add resources to storage facilities.
        
        Args:
            resource_type: Type of resource to add
            amount: Amount to add
            
        Returns:
            Amount actually added
        """
        # First try to add to storage facilities
        added = self.storage_manager.add_resource(resource_type, amount)
        
        # If not all could be added (or no facilities), add remainder to virtual storage
        if added < amount:
            remaining = amount - added
            self.resource_manager.add_to_village_storage(resource_type, remaining)
            added = amount  # All was added, just not all to physical storage
            
        return added
    
    def take_resource_from_storage(self, resource_type, amount: float) -> float:
        """
        Take resources from storage facilities.
        
        Args:
            resource_type: Type of resource to take
            amount: Amount to take
            
        Returns:
            Amount actually taken
        """
        # First try to take from storage facilities
        taken = self.storage_manager.remove_resource(resource_type, amount)
        
        # If not enough in facilities, take remaining from virtual storage
        if taken < amount:
            remaining = amount - taken
            taken_from_virtual = self.resource_manager.take_from_village_storage(resource_type, remaining)
            taken += taken_from_virtual
            
        return taken
    
    def get_total_resource_amount(self, resource_type) -> float:
        """
        Get total amount of a resource across all storage.
        
        Args:
            resource_type: Type of resource to check
            
        Returns:
            Total amount available
        """
        physical_storage = self.storage_manager.get_total_resource_amount(resource_type)
        virtual_storage = self.resource_manager.village_resources.get(resource_type, 0.0)
        return physical_storage + virtual_storage
    
    def render(self, surface: Optional[pygame.Surface] = None):
        """Render the world onto a pygame surface"""
        # Basic rendering implementation - will be expanded in visualization module
        if surface is None:
            return
            
        # Clear the surface
        surface.fill((50, 120, 50))  # Green background for grass
        
        # Render resources
        self.resource_manager.render(surface)
        
        # Render buildings and agents
        for building in self.buildings:
            building.render(surface)
            
        for agent in self.agents:
            agent.render(surface)
            
        # Render threats
        self.threat_manager.render(surface)
        
        # Render storage facilities
        self.storage_manager.render(surface) 