from typing import Dict, List, Tuple, Optional, Any
import pygame
from abc import ABC, abstractmethod

from src.utils.config import Config

class Building(ABC):
    """
    Base class for all buildings in the simulation.
    Buildings provide functionality and shelter for agents.
    """
    
    def __init__(self, config: Config, building_type: str, position: Tuple[int, int]):
        """
        Initialize a building.
        
        Args:
            config: Configuration object
            building_type: Type of building
            position: (x, y) position in the world
        """
        self.config = config
        self.building_type = building_type
        self.position = position
        self.condition = 100.0  # Building condition (0-100)
        self.capacity = 0  # How many agents can use this building
        self.occupants = []  # List of agent IDs currently in this building
        self.owner = None  # ID of the owner, if any
        self.construction_progress = 1.0  # 0.0-1.0, 1.0 means complete
        self.resources_stored = {}  # Resources stored in this building
        
        # Building-specific properties
        self.properties = {}
    
    @abstractmethod
    def update(self, world):
        """
        Update the building state for each time step.
        
        Args:
            world: Reference to the world
        """
        pass
    
    def is_complete(self) -> bool:
        """Check if construction is complete"""
        return self.construction_progress >= 1.0
    
    def get_remaining_construction_materials(self) -> Dict[str, float]:
        """
        Get materials needed to complete construction.
        
        Returns:
            Dictionary of resource_type -> amount needed
        """
        if self.is_complete():
            return {}
        
        # This would be implemented by specific building types
        return {}
    
    def add_construction_materials(self, resource_type: str, amount: float) -> float:
        """
        Add construction materials to progress the building.
        
        Args:
            resource_type: Type of resource
            amount: Amount of resource to add
            
        Returns:
            Amount of resource actually used
        """
        # This would be implemented by specific building types
        return 0.0
    
    def can_enter(self, agent) -> bool:
        """
        Check if an agent can enter this building.
        
        Args:
            agent: The agent trying to enter
            
        Returns:
            True if agent can enter, False otherwise
        """
        # Check if building is complete
        if not self.is_complete():
            return False
            
        # Check if at capacity
        if self.capacity > 0 and len(self.occupants) >= self.capacity:
            # At capacity, only owner can enter
            return self.owner == agent.id
            
        return True
    
    def enter(self, agent) -> bool:
        """
        Agent enters the building.
        
        Args:
            agent: The agent entering
            
        Returns:
            True if successful, False otherwise
        """
        if not self.can_enter(agent):
            return False
            
        if agent.id not in self.occupants:
            self.occupants.append(agent.id)
        
        return True
    
    def exit(self, agent) -> bool:
        """
        Agent exits the building.
        
        Args:
            agent: The agent exiting
            
        Returns:
            True if successful, False otherwise
        """
        if agent.id in self.occupants:
            self.occupants.remove(agent.id)
            return True
        
        return False
    
    def store_resource(self, resource_type: str, amount: float) -> float:
        """
        Store a resource in this building.
        
        Args:
            resource_type: Type of resource
            amount: Amount to store
            
        Returns:
            Amount actually stored
        """
        # Implement storage capacity logic here
        self.resources_stored[resource_type] = self.resources_stored.get(resource_type, 0) + amount
        return amount
    
    def retrieve_resource(self, resource_type: str, amount: float) -> float:
        """
        Retrieve a resource from this building.
        
        Args:
            resource_type: Type of resource
            amount: Amount to retrieve
            
        Returns:
            Amount actually retrieved
        """
        if resource_type not in self.resources_stored:
            return 0.0
            
        available = self.resources_stored[resource_type]
        retrievable = min(amount, available)
        
        self.resources_stored[resource_type] -= retrievable
        
        # Remove from storage if depleted
        if self.resources_stored[resource_type] <= 0:
            del self.resources_stored[resource_type]
            
        return retrievable
    
    def get_stored_resources(self) -> Dict[str, float]:
        """Get all stored resources"""
        return self.resources_stored.copy()
    
    def deteriorate(self, amount: float):
        """
        Reduce building condition due to deterioration.
        
        Args:
            amount: Amount to reduce condition by
        """
        self.condition = max(0.0, self.condition - amount)
    
    def repair(self, amount: float):
        """
        Repair building condition.
        
        Args:
            amount: Amount to increase condition by
        """
        self.condition = min(100.0, self.condition + amount)
    
    def render(self, surface: pygame.Surface):
        """
        Render the building on a pygame surface.
        
        Args:
            surface: The surface to render on
        """
        # Get building position
        x, y = self.position
        
        # Get cell size (assuming it's calculated elsewhere)
        cell_size = 20  # Placeholder
        
        # Determine building color based on type
        color_map = {
            'house': (150, 75, 0),     # Brown
            'farm': (210, 180, 140),   # Tan
            'mine': (169, 169, 169),   # Gray
            'workshop': (139, 69, 19), # Saddle brown
            'market': (255, 215, 0),   # Gold
            'storage': (160, 82, 45)   # Sienna
        }
        
        color = color_map.get(self.building_type, (100, 100, 100))
        
        # Adjust color based on condition and construction progress
        if not self.is_complete():
            # Under construction - desaturate
            color = tuple(c * 0.7 for c in color)
        elif self.condition < 50:
            # Poor condition - darken
            color = tuple(c * (0.5 + 0.5 * self.condition / 100) for c in color)
        
        # Draw building
        pygame.draw.rect(
            surface,
            color,
            (x * cell_size, y * cell_size, cell_size, cell_size)
        )
        
        # Draw construction progress or condition indicator
        if not self.is_complete():
            # Construction progress bar
            progress_width = int(cell_size * self.construction_progress)
            pygame.draw.rect(
                surface,
                (200, 200, 200),  # Light gray
                (x * cell_size, y * cell_size + cell_size - 3, progress_width, 3)
            )
        else:
            # Condition bar
            condition_width = int(cell_size * (self.condition / 100.0))
            pygame.draw.rect(
                surface,
                (0, 255, 0),  # Green for good condition
                (x * cell_size, y * cell_size + cell_size - 3, condition_width, 3)
            ) 