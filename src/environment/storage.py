import random
from typing import Dict, List, Tuple, Optional
import pygame

from src.environment.resources import ResourceType

class StorageFacility:
    """Base class for all storage facilities"""
    
    def __init__(self, position: Tuple[int, int], capacity: float = 1000.0, name: str = "Storage"):
        """
        Initialize a storage facility.
        
        Args:
            position: (x, y) position in the world grid
            capacity: Maximum storage capacity
            name: Name of the facility
        """
        self.position = position
        self.capacity = capacity
        self.name = name
        self.resources = {}  # ResourceType -> quantity
        self.condition = 100.0  # Building condition (0-100)
        self.last_repair = 0  # Game day of last repair
        self.size = (1, 1)  # Size in grid cells (width, height)
        self.id = random.randint(1000, 9999)
        self.color = (139, 69, 19)  # Brown by default
    
    def add_resource(self, resource_type: ResourceType, amount: float) -> float:
        """
        Add resources to storage.
        
        Args:
            resource_type: Type of resource to add
            amount: Amount to add
            
        Returns:
            Amount actually added (limited by available capacity)
        """
        # Calculate total current storage use
        current_total = sum(self.resources.values())
        available_space = max(0.0, self.capacity - current_total)
        
        # Determine how much can be added
        can_add = min(amount, available_space)
        
        # Update storage
        if resource_type not in self.resources:
            self.resources[resource_type] = 0.0
            
        self.resources[resource_type] += can_add
        
        return can_add
    
    def remove_resource(self, resource_type: ResourceType, amount: float) -> float:
        """
        Remove resources from storage.
        
        Args:
            resource_type: Type of resource to remove
            amount: Amount to remove
            
        Returns:
            Amount actually removed (limited by available amount)
        """
        available = self.resources.get(resource_type, 0.0)
        can_remove = min(amount, available)
        
        if can_remove > 0:
            self.resources[resource_type] = available - can_remove
            
            # Clean up zero entries
            if self.resources[resource_type] <= 0:
                del self.resources[resource_type]
                
        return can_remove
    
    def get_available_capacity(self) -> float:
        """Get remaining storage capacity"""
        current_total = sum(self.resources.values())
        return max(0.0, self.capacity - current_total)
    
    def get_fullness_percentage(self) -> float:
        """Get percentage of capacity used (0-100)"""
        current_total = sum(self.resources.values())
        if self.capacity <= 0:
            return 100.0
        return (current_total / self.capacity) * 100.0
    
    def damage(self, amount: float) -> float:
        """
        Apply damage to the facility.
        
        Args:
            amount: Amount of damage to apply
            
        Returns:
            Amount of damage actually applied
        """
        damage_taken = min(amount, self.condition)
        self.condition -= damage_taken
        
        # If severely damaged, resources might be lost
        if self.condition < 30.0 and random.random() < 0.3:
            self._lose_resources_from_damage(damage_taken / 100.0)
            
        return damage_taken
    
    def repair(self, amount: float, day: int) -> float:
        """
        Repair the facility.
        
        Args:
            amount: Amount of repair to apply
            day: Current game day for tracking
            
        Returns:
            Amount of repair actually applied
        """
        if self.condition >= 100.0:
            return 0.0
            
        repair_amount = min(amount, 100.0 - self.condition)
        self.condition += repair_amount
        self.last_repair = day
        
        return repair_amount
    
    def _lose_resources_from_damage(self, percentage: float):
        """
        Lose some resources due to damage.
        
        Args:
            percentage: Percentage of resources to lose (0-1)
        """
        for resource_type in list(self.resources.keys()):
            amount = self.resources[resource_type]
            loss = amount * percentage * random.uniform(0.5, 1.0)  # Random loss amount
            self.resources[resource_type] -= loss
            
            # Clean up zero entries
            if self.resources[resource_type] <= 0:
                del self.resources[resource_type]
    
    def render(self, surface: pygame.Surface):
        """Render the storage facility on the given surface"""
        # Get cell size from config (assuming 32 as default)
        cell_size = 32
        
        x, y = self.position
        
        # Draw a rectangle for the storage building
        rect = pygame.Rect(
            x * cell_size, 
            y * cell_size,
            cell_size * self.size[0],
            cell_size * self.size[1]
        )
        pygame.draw.rect(surface, self.color, rect)
        
        # Draw outline
        pygame.draw.rect(surface, (0, 0, 0), rect, 2)
        
        # Draw condition indicator
        condition_color = (0, 255, 0) if self.condition > 70 else (255, 255, 0) if self.condition > 30 else (255, 0, 0)
        condition_width = int((self.condition / 100.0) * cell_size * 0.8)
        pygame.draw.rect(
            surface,
            condition_color,
            (x * cell_size + cell_size * 0.1, y * cell_size + cell_size * 0.9, condition_width, cell_size * 0.1)
        )
        
        # Draw fullness indicator
        fullness = self.get_fullness_percentage()
        fullness_color = (0, 0, 255) if fullness < 70 else (0, 0, 128) if fullness < 90 else (75, 0, 130)
        fullness_width = int((fullness / 100.0) * cell_size * 0.8)
        pygame.draw.rect(
            surface,
            fullness_color,
            (x * cell_size + cell_size * 0.1, y * cell_size + cell_size * 0.8, fullness_width, cell_size * 0.1)
        )

class Warehouse(StorageFacility):
    """General purpose storage for all resource types"""
    
    def __init__(self, position: Tuple[int, int], capacity: float = 2000.0):
        """Initialize a general warehouse"""
        super().__init__(position, capacity, "Warehouse")
        self.size = (2, 2)  # Larger building
        self.color = (101, 67, 33)  # Dark brown

class Granary(StorageFacility):
    """Specialized storage for food resources"""
    
    def __init__(self, position: Tuple[int, int], capacity: float = 1500.0):
        """Initialize a granary"""
        super().__init__(position, capacity, "Granary")
        self.size = (2, 1)  # Medium building
        self.color = (218, 165, 32)  # Golden brown
    
    def add_resource(self, resource_type: ResourceType, amount: float) -> float:
        """Only allow food resources in granary"""
        if resource_type not in [ResourceType.FOOD_WHEAT, ResourceType.FOOD_BERRY, ResourceType.FOOD_FISH]:
            return 0.0
        return super().add_resource(resource_type, amount)

class Stockpile(StorageFacility):
    """Basic outdoor storage for raw materials"""
    
    def __init__(self, position: Tuple[int, int], capacity: float = 800.0):
        """Initialize a stockpile"""
        super().__init__(position, capacity, "Stockpile")
        self.size = (1, 1)  # Small area
        self.color = (169, 169, 169)  # Gray
    
    def add_resource(self, resource_type: ResourceType, amount: float) -> float:
        """Only allow raw materials in stockpile"""
        if not ResourceType.is_raw_resource(resource_type):
            return 0.0
        return super().add_resource(resource_type, amount)

class Armory(StorageFacility):
    """Specialized storage for weapons and tools"""
    
    def __init__(self, position: Tuple[int, int], capacity: float = 500.0):
        """Initialize an armory"""
        super().__init__(position, capacity, "Armory")
        self.size = (1, 1)  # Small building
        self.color = (178, 34, 34)  # Firebrick red
    
    def add_resource(self, resource_type: ResourceType, amount: float) -> float:
        """Only allow weapons and tools in armory"""
        if resource_type not in [ResourceType.WEAPONS, ResourceType.BASIC_TOOLS, ResourceType.ADVANCED_TOOLS]:
            return 0.0
        return super().add_resource(resource_type, amount)

class StorageManager:
    """Manages all storage facilities in the village"""
    
    def __init__(self, world):
        """
        Initialize the storage manager.
        
        Args:
            world: Reference to the world
        """
        self.world = world
        self.storage_facilities = []
        self.resource_map = {}  # ResourceType -> List[StorageFacility]
    
    def add_facility(self, facility: StorageFacility) -> bool:
        """
        Add a storage facility to the manager.
        
        Args:
            facility: Storage facility to add
            
        Returns:
            True if added successfully, False otherwise
        """
        # Check if the position is valid in the world
        if self.world.add_building(facility, *facility.position):
            self.storage_facilities.append(facility)
            return True
        return False
    
    def remove_facility(self, facility_id: int) -> bool:
        """
        Remove a storage facility from the manager.
        
        Args:
            facility_id: ID of the facility to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        facility = self.get_facility_by_id(facility_id)
        if not facility:
            return False
            
        # Remove from world's buildings list if it exists there
        if facility in self.world.buildings:
            self.world.buildings.remove(facility)
            
        # Remove from our list
        self.storage_facilities.remove(facility)
        
        # Remove from resource_map
        for facilities in self.resource_map.values():
            if facility in facilities:
                facilities.remove(facility)
                
        return True
    
    def get_facility_by_id(self, facility_id: int) -> Optional[StorageFacility]:
        """Find a facility by its ID"""
        for facility in self.storage_facilities:
            if facility.id == facility_id:
                return facility
        return None
    
    def get_facilities_for_resource(self, resource_type: ResourceType) -> List[StorageFacility]:
        """Get all facilities that can store a specific resource type"""
        # Update resource map if needed
        if resource_type not in self.resource_map:
            self._update_resource_map(resource_type)
            
        return self.resource_map.get(resource_type, [])
    
    def add_resource(self, resource_type: ResourceType, amount: float) -> float:
        """
        Add resources to storage, distributing optimally across facilities.
        
        Args:
            resource_type: Type of resource to add
            amount: Amount to add
            
        Returns:
            Amount actually added
        """
        facilities = self.get_facilities_for_resource(resource_type)
        
        # If no facilities can store this resource, nothing can be added
        if not facilities:
            return 0.0
            
        # Sort facilities by available capacity (most to least)
        facilities.sort(key=lambda f: f.get_available_capacity(), reverse=True)
        
        # Distribute the resources
        remaining = amount
        total_added = 0.0
        
        for facility in facilities:
            if remaining <= 0:
                break
                
            added = facility.add_resource(resource_type, remaining)
            total_added += added
            remaining -= added
            
        return total_added
    
    def remove_resource(self, resource_type: ResourceType, amount: float) -> float:
        """
        Remove resources from storage.
        
        Args:
            resource_type: Type of resource to remove
            amount: Amount to remove
            
        Returns:
            Amount actually removed
        """
        facilities = self.get_facilities_for_resource(resource_type)
        
        # Sort facilities by available amount of this resource (most to least)
        facilities.sort(key=lambda f: f.resources.get(resource_type, 0.0), reverse=True)
        
        # Take resources from facilities
        remaining = amount
        total_removed = 0.0
        
        for facility in facilities:
            if remaining <= 0:
                break
                
            removed = facility.remove_resource(resource_type, remaining)
            total_removed += removed
            remaining -= removed
            
        return total_removed
    
    def get_total_resource_amount(self, resource_type: ResourceType) -> float:
        """Get the total amount of a resource type across all storage facilities"""
        total = 0.0
        for facility in self.storage_facilities:
            total += facility.resources.get(resource_type, 0.0)
        return total
    
    def get_total_storage_capacity(self) -> float:
        """Get the total storage capacity across all facilities"""
        return sum(facility.capacity for facility in self.storage_facilities)
    
    def get_available_capacity(self) -> float:
        """Get the total available capacity across all facilities"""
        return sum(facility.get_available_capacity() for facility in self.storage_facilities)
    
    def _update_resource_map(self, resource_type: ResourceType):
        """Update the map of which facilities can store which resources"""
        eligible_facilities = []
        
        for facility in self.storage_facilities:
            # Check if this facility can store this resource type
            if isinstance(facility, Warehouse):
                # Warehouse can store anything
                eligible_facilities.append(facility)
            elif isinstance(facility, Granary) and resource_type in [ResourceType.FOOD_WHEAT, ResourceType.FOOD_BERRY, ResourceType.FOOD_FISH]:
                # Granary for food
                eligible_facilities.append(facility)
            elif isinstance(facility, Stockpile) and ResourceType.is_raw_resource(resource_type):
                # Stockpile for raw resources
                eligible_facilities.append(facility)
            elif isinstance(facility, Armory) and resource_type in [ResourceType.WEAPONS, ResourceType.BASIC_TOOLS, ResourceType.ADVANCED_TOOLS]:
                # Armory for weapons and tools
                eligible_facilities.append(facility)
                
        self.resource_map[resource_type] = eligible_facilities
    
    def get_facilities_near(self, position: Tuple[int, int], distance: int) -> List[StorageFacility]:
        """Get storage facilities within a certain distance of a position"""
        x, y = position
        nearby = []
        
        for facility in self.storage_facilities:
            fx, fy = facility.position
            if abs(fx - x) <= distance and abs(fy - y) <= distance:
                nearby.append(facility)
                
        return nearby
    
    def render(self, surface: pygame.Surface):
        """Render all storage facilities"""
        for facility in self.storage_facilities:
            facility.render(surface) 