import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class MinerJob(Job):
    """
    Miner job responsible for extracting stone and ore from the earth.
    Miners locate mineral deposits, mine resources and bring them back to the village.
    """
    
    def __init__(self):
        """Initialize the miner job with appropriate skills and data"""
        super().__init__("miner", "Extracts stone and ore from mining sites")
        
        # Set skill modifiers - miners get bonuses to these skills
        self.skill_modifiers = {
            "mining": 0.5,      # Major boost to mining
            "strength": 0.4,    # Moderate boost to strength
            "perception": 0.2   # Minor boost to perception (finding ore)
        }
        
        # Job-specific data
        self.job_specific_data = {
            "known_deposits": {},  # Resource type -> list of locations
            "current_deposit": None,  # Current deposit being worked on (position, type)
            "ore_stockpile": 0.0,   # Temporary ore being carried
            "stone_stockpile": 0.0, # Temporary stone being carried
            "max_carry_capacity": 40.0,  # Maximum minerals that can be carried
            "deposits_depleted": 0  # Career statistic
        }
    
    def decide_action(self, agent, world):
        """
        Decide the next mining action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Check if carrying capacity reached
        total_carried = self.job_specific_data["ore_stockpile"] + self.job_specific_data["stone_stockpile"]
        if total_carried >= self.job_specific_data["max_carry_capacity"]:
            # Return to village/storage
            agent._set_action("return_with_minerals", None)
            return
        
        # Check if agent has a deposit assigned
        if not self.job_specific_data["current_deposit"]:
            # Find a deposit to mine
            agent._set_action("find_deposit", None)
            return
        
        # Check if agent is at their assigned deposit
        deposit_pos, deposit_type = self.job_specific_data["current_deposit"]
        if agent.position != deposit_pos:
            # Go to deposit
            agent._set_action("go_to_deposit", deposit_pos)
            return
        
        # At the deposit, check if there are minerals to mine
        resources = world.resource_manager.get_resources_at(*deposit_pos)
        has_minerals = any(r.resource_type == deposit_type for r in resources)
        
        if has_minerals:
            # Mine minerals
            agent._set_action("mine_deposit", deposit_pos)
        else:
            # No minerals left, find a new deposit
            self.job_specific_data["current_deposit"] = None
            agent._set_action("find_deposit", None)
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a mining action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "find_deposit":
            return self._progress_find_deposit(agent, world, time_delta)
        elif action == "go_to_deposit":
            return self._progress_go_to_deposit(agent, world, time_delta)
        elif action == "mine_deposit":
            return self._progress_mine_deposit(agent, world, time_delta)
        elif action == "return_with_minerals":
            return self._progress_return_with_minerals(agent, world, time_delta)
        
        return None
    
    def _progress_find_deposit(self, agent, world, time_delta: float):
        """Find a mineral deposit to mine"""
        # First, determine what type to look for
        # If we already know deposits, check what's available
        prefer_stone = random.random() < 0.6  # Default preference to stone (more common)
        
        # If we know both types, slightly prefer the one with more known locations
        if ResourceType.STONE in self.job_specific_data["known_deposits"] and ResourceType.IRON_ORE in self.job_specific_data["known_deposits"]:
            stone_count = len(self.job_specific_data["known_deposits"][ResourceType.STONE])
            ore_count = len(self.job_specific_data["known_deposits"][ResourceType.IRON_ORE])
            prefer_stone = stone_count >= ore_count
        
        # Check if we already know deposits
        if prefer_stone and ResourceType.STONE in self.job_specific_data["known_deposits"] and self.job_specific_data["known_deposits"][ResourceType.STONE]:
            # Assign a known stone deposit
            deposit_pos = random.choice(self.job_specific_data["known_deposits"][ResourceType.STONE])
            self.job_specific_data["current_deposit"] = (deposit_pos, ResourceType.STONE)
            agent._set_action("go_to_deposit", deposit_pos)
            return {"agent": agent.name, "action": "assigned_stone_deposit", "location": deposit_pos}
        elif not prefer_stone and ResourceType.IRON_ORE in self.job_specific_data["known_deposits"] and self.job_specific_data["known_deposits"][ResourceType.IRON_ORE]:
            # Assign a known ore deposit
            deposit_pos = random.choice(self.job_specific_data["known_deposits"][ResourceType.IRON_ORE])
            self.job_specific_data["current_deposit"] = (deposit_pos, ResourceType.IRON_ORE)
            agent._set_action("go_to_deposit", deposit_pos)
            return {"agent": agent.name, "action": "assigned_ore_deposit", "location": deposit_pos}
        
        # Look for potential deposits nearby
        x, y = agent.position
        neighbors = world.get_neighboring_cells(x, y, 5)  # Search in a larger radius
        
        # Check for suitable locations
        potential_stone = []
        potential_ore = []
        
        for nx, ny in neighbors:
            resources = world.resource_manager.get_resources_at(nx, ny)
            
            for resource in resources:
                if resource.resource_type == ResourceType.STONE:
                    potential_stone.append((nx, ny))
                elif resource.resource_type == ResourceType.IRON_ORE:
                    potential_ore.append((nx, ny))
        
        # First try to find the preferred type
        if prefer_stone and potential_stone:
            deposit_pos = random.choice(potential_stone)
            deposit_type = ResourceType.STONE
        elif not prefer_stone and potential_ore:
            deposit_pos = random.choice(potential_ore)
            deposit_type = ResourceType.IRON_ORE
        # If preferred not found, try the other
        elif potential_stone:
            deposit_pos = random.choice(potential_stone)
            deposit_type = ResourceType.STONE
        elif potential_ore:
            deposit_pos = random.choice(potential_ore)
            deposit_type = ResourceType.IRON_ORE
        else:
            # No deposits found, wander and keep looking
            agent._progress_wander(world, time_delta)
            agent.action_progress = 0.5  # Still looking
            return None
        
        # Found a deposit
        if deposit_type not in self.job_specific_data["known_deposits"]:
            self.job_specific_data["known_deposits"][deposit_type] = []
            
        if deposit_pos not in self.job_specific_data["known_deposits"][deposit_type]:
            self.job_specific_data["known_deposits"][deposit_type].append(deposit_pos)
            
        self.job_specific_data["current_deposit"] = (deposit_pos, deposit_type)
        agent._set_action("go_to_deposit", deposit_pos)
        
        # Add to agent's memory
        memory_type = "stone_deposit" if deposit_type == ResourceType.STONE else "ore_deposit"
        if memory_type not in agent.known_locations:
            agent.known_locations[memory_type] = []
        if deposit_pos not in agent.known_locations[memory_type]:
            agent.known_locations[memory_type].append(deposit_pos)
            
        return {"agent": agent.name, "action": f"found_{memory_type}", "location": deposit_pos}
    
    def _progress_go_to_deposit(self, agent, world, time_delta: float):
        """Go to the assigned deposit"""
        deposit_pos = agent.action_target
        if not deposit_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = deposit_pos
        
        # Already at deposit
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_deposit", "location": deposit_pos}
        
        # Move towards deposit
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
    
    def _progress_mine_deposit(self, agent, world, time_delta: float):
        """Mine minerals from a deposit"""
        # Check if we're at the deposit
        deposit_pos = agent.action_target
        if agent.position != deposit_pos:
            agent._set_action("go_to_deposit", deposit_pos)
            return None
        
        # Get deposit type from current assignment
        _, deposit_type = self.job_specific_data["current_deposit"]
        
        # Get mineral resources at location
        resources = world.resource_manager.get_resources_at(*deposit_pos)
        mineral_resources = [r for r in resources if r.resource_type == deposit_type]
        
        if not mineral_resources:
            # No minerals here anymore
            agent.action_progress = 1.0
            self.job_specific_data["current_deposit"] = None
            return {"agent": agent.name, "action": "deposit_depleted", "location": deposit_pos}
        
        # Mine resource
        if agent.action_progress < 0.95:
            # Still mining
            mining_skill = agent.skills["mining"]
            progress_amount = 0.1 + mining_skill * 0.15  # Mining is slower than woodcutting
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "mining", 0.007)
            self.improve_skills(agent, "strength", 0.004)
            
            return None
        else:
            # Mining complete - harvest minerals
            agent.action_progress = 1.0
            
            # Determine amount of minerals harvested based on skill
            mining_skill = agent.skills["mining"]
            mineral_amount = 5.0 + mining_skill * 15.0  # 5-20 units based on skill
            
            # Add to appropriate stockpile
            if deposit_type == ResourceType.STONE:
                self.job_specific_data["stone_stockpile"] += mineral_amount
                stockpile_key = "stone_stockpile"
            else:  # Iron ore
                self.job_specific_data["ore_stockpile"] += mineral_amount
                stockpile_key = "ore_stockpile"
            
            # Remove some of the mineral resource
            mineral = mineral_resources[0]
            mineral.quantity -= 1
            
            if mineral.quantity <= 0:
                # Deposit has been depleted
                world.resource_manager.remove_resource(mineral)
                self.job_specific_data["deposits_depleted"] += 1
                
                # Update known deposits list
                if deposit_type in self.job_specific_data["known_deposits"] and deposit_pos in self.job_specific_data["known_deposits"][deposit_type]:
                    self.job_specific_data["known_deposits"][deposit_type].remove(deposit_pos)
            
            # Check if carrying capacity reached
            total_carried = self.job_specific_data["ore_stockpile"] + self.job_specific_data["stone_stockpile"]
            if total_carried >= self.job_specific_data["max_carry_capacity"]:
                agent._set_action("return_with_minerals", None)
            
            return {
                "agent": agent.name, 
                "action": f"mined_{deposit_type.name.lower()}", 
                "amount": mineral_amount,
                "total_carried": self.job_specific_data[stockpile_key]
            }
    
    def _progress_return_with_minerals(self, agent, world, time_delta: float):
        """Return to village with harvested minerals"""
        # Ideally would return to a storage building or processing area
        # For now, head home or to center of village
        target = agent.home_position
        
        if not target:
            # No home, go to center of map
            target = (world.width // 2, world.height // 2)
        
        current_x, current_y = agent.position
        target_x, target_y = target
        
        # Already at target
        if current_x == target_x and current_y == target_y:
            # Deposit the minerals in village storage
            stone_amount = self.job_specific_data["stone_stockpile"]
            ore_amount = self.job_specific_data["ore_stockpile"]
            
            # Add to village resources
            if stone_amount > 0:
                world.resource_manager.add_to_village_storage(ResourceType.STONE, stone_amount)
            
            if ore_amount > 0:
                world.resource_manager.add_to_village_storage(ResourceType.IRON_ORE, ore_amount)
            
            # Reset stockpiles
            self.job_specific_data["stone_stockpile"] = 0.0
            self.job_specific_data["ore_stockpile"] = 0.0
            
            agent.action_progress = 1.0
            return {
                "agent": agent.name, 
                "action": "deposited_minerals", 
                "stone_amount": stone_amount,
                "ore_amount": ore_amount,
                "location": agent.position
            }
        
        # Move towards target
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
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling miner-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # If carrying minerals, drop them
        stone_carried = self.job_specific_data.get("stone_stockpile", 0.0)
        ore_carried = self.job_specific_data.get("ore_stockpile", 0.0)
        
        if stone_carried > 0 or ore_carried > 0:
            # In a more complete system, would drop minerals at agent's location
            # For now, just lose them
            self.job_specific_data["stone_stockpile"] = 0.0
            self.job_specific_data["ore_stockpile"] = 0.0
        
        # Call parent remove method
        super().remove_from_agent(agent) 