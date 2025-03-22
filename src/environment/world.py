import numpy as np
from typing import Dict, List, Tuple, Optional
from gymnasium import spaces
import pygame

from src.utils.config import Config
from src.environment.resources import ResourceManager
from src.environment.time_system import TimeSystem
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
        
        # Entity tracking
        self.agents = []
        self.buildings = []
        
        # Initialize resources on the map
        self._initialize_resources()
    
    def _initialize_resources(self):
        """Initialize resources throughout the world based on config"""
        self.resource_manager.generate_initial_resources()
    
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