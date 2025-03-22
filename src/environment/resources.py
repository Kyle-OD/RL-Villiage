import numpy as np
from typing import Dict, List, Tuple, Optional
import pygame
import random
from enum import Enum, auto

from src.utils.config import Config
from src.environment.time_system import TimeSystem

class ResourceType(Enum):
    """Enumeration of different resource types in the world"""
    WOOD = auto()
    STONE = auto()
    IRON = auto()
    FOOD_BERRY = auto()
    FOOD_FISH = auto()
    FOOD_WHEAT = auto()
    WATER = auto()
    CLAY = auto()
    
    @classmethod
    def get_color(cls, resource_type):
        """Get color for visualization purposes"""
        colors = {
            cls.WOOD: (139, 69, 19),      # Brown
            cls.STONE: (169, 169, 169),   # Grey
            cls.IRON: (105, 105, 105),    # Dark Grey
            cls.FOOD_BERRY: (255, 0, 0),  # Red
            cls.FOOD_FISH: (70, 130, 180), # Steel Blue
            cls.FOOD_WHEAT: (218, 165, 32), # Golden
            cls.WATER: (0, 0, 255),       # Blue
            cls.CLAY: (205, 133, 63),     # Peru
        }
        return colors.get(resource_type, (0, 0, 0))

class Resource:
    """Represents a resource node in the world"""
    
    def __init__(self, resource_type: ResourceType, position: Tuple[int, int], quantity: float, 
                 max_quantity: float, regrowth_rate: float):
        """
        Initialize a resource.
        
        Args:
            resource_type: Type of the resource
            position: (x, y) position in the world grid
            quantity: Current available quantity
            max_quantity: Maximum capacity of this resource node
            regrowth_rate: Rate at which the resource regenerates
        """
        self.resource_type = resource_type
        self.position = position
        self.quantity = quantity
        self.max_quantity = max_quantity
        self.regrowth_rate = regrowth_rate
        self.depleted = False
    
    def extract(self, amount: float) -> float:
        """
        Extract some amount of the resource.
        
        Args:
            amount: Amount to try to extract
            
        Returns:
            Amount actually extracted
        """
        if self.depleted:
            return 0.0
            
        extractable = min(amount, self.quantity)
        self.quantity -= extractable
        
        if self.quantity <= 0:
            self.depleted = True
            self.quantity = 0
            
        return extractable
    
    def regrow(self, delta_time: float, season_modifier: float = 1.0):
        """
        Regrow the resource based on time passed and season.
        
        Args:
            delta_time: Time passed
            season_modifier: Modifier based on current season (e.g., spring might have higher regrowth)
        """
        if self.depleted and random.random() < 0.05:  # Small chance to un-deplete
            self.depleted = False
            self.quantity = self.max_quantity * 0.1  # Start with 10% filled
            
        if not self.depleted and self.quantity < self.max_quantity:
            growth = self.regrowth_rate * delta_time * season_modifier
            self.quantity = min(self.quantity + growth, self.max_quantity)
    
    def render(self, surface: pygame.Surface, cell_size: int):
        """Render the resource on a surface"""
        x, y = self.position
        if self.depleted:
            color = (100, 100, 100)  # Gray for depleted resources
        else:
            color = ResourceType.get_color(self.resource_type)
            
        # Scale size based on quantity
        size_factor = self.quantity / self.max_quantity if self.max_quantity > 0 else 0
        radius = int(cell_size * 0.3 * (0.5 + 0.5 * size_factor))
        
        pygame.draw.circle(
            surface, 
            color, 
            (x * cell_size + cell_size // 2, y * cell_size + cell_size // 2),
            radius
        )

class ResourceManager:
    """Manages all resources in the world"""
    
    def __init__(self, world, config: Config):
        """
        Initialize the resource manager.
        
        Args:
            world: Reference to the world
            config: Configuration parameters
        """
        self.world = world
        self.config = config
        self.resources: List[Resource] = []
        self.resource_grid = {}  # (x,y) -> List[Resource]
    
    def generate_initial_resources(self):
        """Generate initial resources throughout the world"""
        # Generate resource clusters based on configuration
        for resource_type in ResourceType:
            self._generate_resource_clusters(resource_type)
    
    def _generate_resource_clusters(self, resource_type: ResourceType):
        """
        Generate clusters of a specific resource type.
        
        Args:
            resource_type: Type of resource to generate
        """
        # Resource type specific parameters (should come from config in a real implementation)
        config = {
            ResourceType.WOOD: {
                'clusters': 5,
                'density': 0.7,
                'max_quantity': 100,
                'regrowth_rate': 0.5
            },
            ResourceType.STONE: {
                'clusters': 3,
                'density': 0.6,
                'max_quantity': 200,
                'regrowth_rate': 0.1
            },
            ResourceType.IRON: {
                'clusters': 2,
                'density': 0.4,
                'max_quantity': 150,
                'regrowth_rate': 0.05
            },
            ResourceType.FOOD_BERRY: {
                'clusters': 6,
                'density': 0.5,
                'max_quantity': 50,
                'regrowth_rate': 0.8
            },
            ResourceType.FOOD_FISH: {
                'clusters': 2,
                'density': 0.6,
                'max_quantity': 80,
                'regrowth_rate': 0.6
            },
            ResourceType.FOOD_WHEAT: {
                'clusters': 4,
                'density': 0.8,
                'max_quantity': 120,
                'regrowth_rate': 0.3
            },
            ResourceType.WATER: {
                'clusters': 1,
                'density': 0.9,
                'max_quantity': 500,
                'regrowth_rate': 1.0
            },
            ResourceType.CLAY: {
                'clusters': 3,
                'density': 0.5,
                'max_quantity': 100,
                'regrowth_rate': 0.2
            }
        }
        
        resource_config = config.get(resource_type, {
            'clusters': 2,
            'density': 0.5,
            'max_quantity': 100,
            'regrowth_rate': 0.3
        })
        
        # Create clusters
        for _ in range(resource_config['clusters']):
            # Choose a random center for the cluster
            center_x = random.randint(0, self.world.width - 1)
            center_y = random.randint(0, self.world.height - 1)
            
            # Determine cluster size
            cluster_size = random.randint(3, 7)
            
            # Add resources around the center based on density
            for dx in range(-cluster_size, cluster_size + 1):
                for dy in range(-cluster_size, cluster_size + 1):
                    x, y = center_x + dx, center_y + dy
                    
                    # Check if within bounds and random chance based on density
                    if (0 <= x < self.world.width and 
                        0 <= y < self.world.height and 
                        random.random() < resource_config['density'] * (1 - (abs(dx) + abs(dy)) / (2 * cluster_size))):
                        
                        # Vary the quantity based on distance from center
                        distance_factor = 1 - (abs(dx) + abs(dy)) / (2 * cluster_size)
                        max_quantity = resource_config['max_quantity'] * (0.5 + 0.5 * distance_factor)
                        initial_quantity = max_quantity * random.uniform(0.6, 1.0)
                        
                        # Create and add the resource
                        resource = Resource(
                            resource_type=resource_type,
                            position=(x, y),
                            quantity=initial_quantity,
                            max_quantity=max_quantity,
                            regrowth_rate=resource_config['regrowth_rate']
                        )
                        
                        self.add_resource(resource)
    
    def add_resource(self, resource: Resource):
        """Add a resource to the world"""
        self.resources.append(resource)
        
        x, y = resource.position
        if (x, y) not in self.resource_grid:
            self.resource_grid[(x, y)] = []
            
        self.resource_grid[(x, y)].append(resource)
    
    def get_resources_at(self, x: int, y: int) -> List[Resource]:
        """Get all resources at a specific position"""
        return self.resource_grid.get((x, y), [])
    
    def step(self, time_system: TimeSystem):
        """
        Update all resources for one time step.
        
        Args:
            time_system: The world's time system for seasonal effects
        """
        # Get season modifier (will be expanded in future with more seasonal effects)
        season_modifier = {
            'spring': 1.5,
            'summer': 1.0,
            'autumn': 0.8,
            'winter': 0.3
        }.get(time_system.get_season(), 1.0)
        
        # Update each resource
        for resource in self.resources:
            resource.regrow(1.0, season_modifier)  # 1.0 = one time step
    
    def render(self, surface: pygame.Surface):
        """Render all resources on the surface"""
        # Simple implementation - will be improved in visualization module
        cell_size = min(
            surface.get_width() // self.world.width,
            surface.get_height() // self.world.height
        )
        
        for resource in self.resources:
            resource.render(surface, cell_size) 