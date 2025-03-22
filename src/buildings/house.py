from typing import Dict, List, Tuple, Optional
import random

from src.buildings.building import Building
from src.utils.config import Config

class House(Building):
    """
    A house provides shelter for agents, allowing them to rest and store their belongings.
    """
    
    def __init__(self, config: Config, position: Tuple[int, int], owner_id: Optional[str] = None):
        """
        Initialize a house.
        
        Args:
            config: Configuration object
            position: (x, y) position in the world
            owner_id: ID of the owner, if any
        """
        super().__init__(config, "house", position)
        
        self.owner = owner_id
        self.capacity = 4  # A house can accommodate up to 4 agents
        
        # House-specific properties
        self.properties = {
            "comfort": random.uniform(0.5, 1.0),  # Affects rest quality
            "security": random.uniform(0.5, 1.0),  # Affects storage security
            "insulation": random.uniform(0.5, 1.0),  # Affects temperature regulation
        }
        
        # Construction requirements if not complete
        self.construction_progress = 0.0  # Start as incomplete
        self.construction_materials = {
            "WOOD": 50.0,
            "STONE": 20.0
        }
        self.materials_provided = {
            "WOOD": 0.0,
            "STONE": 0.0
        }
    
    def update(self, world):
        """
        Update the house state for each time step.
        
        Args:
            world: Reference to the world
        """
        # Weather affects condition
        weather = world.time_system.get_weather()
        season = world.time_system.get_season()
        
        # Deterioration based on weather conditions
        deterioration_rates = {
            "clear": 0.01,
            "rain": 0.03,
            "fog": 0.01,
            "storm": 0.05,
            "snow": 0.02
        }
        
        # Season modifiers
        season_modifiers = {
            "spring": 1.0,
            "summer": 0.8,
            "autumn": 1.2,
            "winter": 1.5
        }
        
        # Apply deterioration
        base_rate = deterioration_rates.get(weather, 0.01)
        season_mod = season_modifiers.get(season, 1.0)
        deterioration = base_rate * season_mod
        
        # Better insulation reduces deterioration
        insulation_effect = 1.0 - (self.properties["insulation"] * 0.5)
        deterioration *= insulation_effect
        
        self.deteriorate(deterioration)
        
        # Provide rest benefits to occupants
        # (In a real implementation, we would update agent rest here,
        # but for simplicity we have this logic in the agent class)
    
    def get_rest_quality(self) -> float:
        """
        Get the quality of rest provided by this house.
        
        Returns:
            Rest quality factor (0-1)
        """
        # Comfort and condition affect rest quality
        base_quality = self.properties["comfort"]
        condition_factor = self.condition / 100.0
        
        return base_quality * condition_factor
    
    def get_shelter_quality(self) -> float:
        """
        Get the quality of shelter provided by this house.
        
        Returns:
            Shelter quality factor (0-1)
        """
        # Insulation and condition affect shelter quality
        base_quality = self.properties["insulation"]
        condition_factor = self.condition / 100.0
        
        return base_quality * condition_factor
    
    def get_storage_capacity(self) -> float:
        """
        Get the storage capacity of this house.
        
        Returns:
            Storage capacity
        """
        # A simple house has limited storage
        return 200.0
    
    def get_remaining_construction_materials(self) -> Dict[str, float]:
        """
        Get materials needed to complete construction.
        
        Returns:
            Dictionary of resource_type -> amount needed
        """
        if self.is_complete():
            return {}
        
        remaining = {}
        for material, required in self.construction_materials.items():
            provided = self.materials_provided.get(material, 0.0)
            if provided < required:
                remaining[material] = required - provided
                
        return remaining
    
    def add_construction_materials(self, resource_type: str, amount: float) -> float:
        """
        Add construction materials to progress the building.
        
        Args:
            resource_type: Type of resource
            amount: Amount of resource to add
            
        Returns:
            Amount of resource actually used
        """
        if self.is_complete():
            return 0.0
        
        if resource_type not in self.construction_materials:
            return 0.0
            
        required = self.construction_materials[resource_type]
        provided = self.materials_provided.get(resource_type, 0.0)
        
        if provided >= required:
            return 0.0  # Already have enough of this material
            
        usable = min(amount, required - provided)
        self.materials_provided[resource_type] = provided + usable
        
        # Update construction progress
        total_required = sum(self.construction_materials.values())
        total_provided = sum(self.materials_provided.values())
        self.construction_progress = min(1.0, total_provided / total_required)
        
        return usable 