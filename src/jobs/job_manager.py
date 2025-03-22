from typing import Dict, List, Optional, Any
import random

from src.jobs.job import Job
from src.jobs.farmer import FarmerJob
from src.jobs.woodcutter import WoodcutterJob
from src.jobs.miner import MinerJob
from src.jobs.builder import BuilderJob
from src.jobs.blacksmith import BlacksmithJob
from src.jobs.guard import GuardJob
from src.jobs.healer import HealerJob
from src.jobs.merchant import MerchantJob
from src.utils.config import Config

class JobManager:
    """
    Manages job distribution and assignments in the village.
    Tracks village needs and helps agents switch jobs as needed.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the job manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Target job distributions based on config
        self.target_distribution = config.get('job_distribution', {})
        
        # Current job distribution
        self.current_distribution = {}
        
        # Available job types that can be created
        self.job_types = {
            'farmer': FarmerJob,
            'woodcutter': WoodcutterJob,
            'miner': MinerJob,
            'builder': BuilderJob,
            'blacksmith': BlacksmithJob,
            'guard': GuardJob,
            'healer': HealerJob,
            'merchant': MerchantJob
        }
        
        # Village needs tracking
        self.village_needs = {
            'food': 0.0,       # Higher value = more food needed
            'building': 0.0,    # Higher value = more construction needed
            'wood': 0.0,       # Higher value = more wood needed
            'mining': 0.0,     # Higher value = more mining needed
            'trading': 0.0,    # Higher value = more trading needed
            'crafting': 0.0,   # Higher value = more crafting/blacksmithing needed
            'security': 0.0,   # Higher value = more village security needed
            'health': 0.0      # Higher value = more healing needed
        }
        
        # History of job changes
        self.job_change_history = []
    
    def register_agent(self, agent):
        """
        Register an agent with the job manager.
        
        Args:
            agent: Agent to register
        """
        job_name = agent.job.name if agent.job else "unemployed"
        
        if job_name not in self.current_distribution:
            self.current_distribution[job_name] = 0
            
        self.current_distribution[job_name] += 1
    
    def unregister_agent(self, agent):
        """
        Unregister an agent from the job manager.
        
        Args:
            agent: Agent to unregister
        """
        job_name = agent.job.name if agent.job else "unemployed"
        
        if job_name in self.current_distribution:
            self.current_distribution[job_name] -= 1
            
            if self.current_distribution[job_name] <= 0:
                del self.current_distribution[job_name]
    
    def update_village_needs(self, world):
        """
        Update village needs based on current world state.
        
        Args:
            world: Reference to the world
        """
        # Reset needs
        for need in self.village_needs:
            self.village_needs[need] = 0.0
        
        # Food need increases if average agent food is low
        avg_food = sum(agent.needs["food"] for agent in world.agents) / len(world.agents) if world.agents else 100.0
        self.village_needs['food'] = max(0.0, (100.0 - avg_food) / 20.0)
        
        # Wood need increases in colder seasons
        if world.time_system.get_season() in ["autumn", "winter"]:
            self.village_needs['wood'] += 2.0
        
        # Building need increases if population is growing or housing is damaged
        buildings_condition = sum(b.condition for b in world.buildings) / len(world.buildings) if world.buildings else 100.0
        self.village_needs['building'] = max(0.0, (100.0 - buildings_condition) / 20.0)
        
        # Mining need increases if crafters need materials
        resources = world.resource_manager.get_village_resources()
        stone_amount = resources.get("STONE", 0.0)
        ore_amount = resources.get("IRON_ORE", 0.0)
        if stone_amount < 50.0 or ore_amount < 20.0:
            self.village_needs['mining'] += max(0.0, (50.0 - stone_amount) / 10.0) + max(0.0, (20.0 - ore_amount) / 5.0)
        
        # Crafting need increases if village needs tools and weapons
        tools_amount = resources.get("BASIC_TOOLS", 0.0) + resources.get("ADVANCED_TOOLS", 0.0)
        weapons_amount = resources.get("WEAPONS", 0.0)
        if tools_amount < 10.0 or weapons_amount < 5.0:
            self.village_needs['crafting'] += max(0.0, (10.0 - tools_amount) / 2.0) + max(0.0, (5.0 - weapons_amount) / 1.0)
        
        # Security need based on village size and threats
        self.village_needs['security'] = min(5.0, len(world.agents) / 10.0)  # At least one guard per 10 villagers
        
        # Health need increases if average agent health is low
        avg_health = sum(agent.health for agent in world.agents) / len(world.agents) if world.agents else 100.0
        self.village_needs['health'] = max(0.0, (100.0 - avg_health) / 20.0)
        
        # Trading need increases based on surplus/deficit of resources
        resource_balance = sum(amount for resource, amount in resources.items() if amount > 50.0)
        self.village_needs['trading'] = min(5.0, resource_balance / 100.0)  # Trading increases with surplus
        
        # Adjust based on seasonal considerations
        self._adjust_for_season(world.time_system.get_season())
    
    def _adjust_for_season(self, season: str):
        """
        Adjust village needs based on the current season.
        
        Args:
            season: Current season
        """
        if season == "spring":
            # Planting season - more farmers needed
            self.village_needs['food'] *= 1.5
        elif season == "summer":
            # Building season - more builders needed
            self.village_needs['building'] *= 1.5
        elif season == "autumn":
            # Harvest season - more farmers needed
            self.village_needs['food'] *= 1.3
        elif season == "winter":
            # Winter - more wood needed for heating
            self.village_needs['wood'] *= 2.0
    
    def should_change_job(self, agent, world) -> bool:
        """
        Determine if an agent should change their job based on village needs.
        
        Args:
            agent: The agent to evaluate
            world: Reference to the world
            
        Returns:
            True if agent should change jobs, False otherwise
        """
        # Don't change jobs too frequently
        last_change = next((change for change in self.job_change_history 
                         if change['agent_id'] == agent.id), None)
        
        if last_change:
            days_since_change = (world.time_system.get_total_day() - last_change['day'])
            if days_since_change < 15:  # Minimum 15 days between job changes
                return False
        
        # Check if current job matches village needs
        current_job = agent.job.name if agent.job else "unemployed"
        
        # Map job names to village needs
        job_need_map = {
            'farmer': 'food',
            'woodcutter': 'wood',
            'builder': 'building',
            'miner': 'mining',
            'merchant': 'trading',
            'blacksmith': 'crafting',
            'guard': 'security',
            'healer': 'health'
        }
        
        # Check if there's a job with higher need
        current_need = self.village_needs.get(job_need_map.get(current_job, ''), 0.0)
        best_need = current_need
        best_job = current_job
        
        for job_name, need_key in job_need_map.items():
            need_value = self.village_needs.get(need_key, 0.0)
            
            # Consider skill aptitude - agents prefer jobs they're good at
            skill_aptitude = self._get_job_skill_aptitude(agent, job_name)
            
            # Adjust need value by skill aptitude
            adjusted_need = need_value * (0.5 + 0.5 * skill_aptitude)
            
            if adjusted_need > best_need:
                best_need = adjusted_need
                best_job = job_name
        
        # Should change job if there's a significantly better job
        # The threshold ensures agents don't constantly switch for minor differences
        return best_job != current_job and (best_need > current_need * 1.5)
    
    def _get_job_skill_aptitude(self, agent, job_name):
        """
        Calculate an agent's aptitude for a specific job based on skills.
        
        Args:
            agent: The agent to evaluate
            job_name: Name of the job to check aptitude for
            
        Returns:
            Aptitude value between 0.0 and 1.0
        """
        if job_name == 'farmer':
            return agent.skills.get('farming', 0.0)
        elif job_name == 'woodcutter':
            return agent.skills.get('woodcutting', 0.0)
        elif job_name == 'builder':
            return agent.skills.get('building', 0.0)
        elif job_name == 'miner':
            return agent.skills.get('mining', 0.0)
        elif job_name == 'merchant':
            return (agent.skills.get('negotiation', 0.0) + agent.skills.get('charisma', 0.0)) / 2
        elif job_name == 'blacksmith':
            return (agent.skills.get('crafting', 0.0) + agent.skills.get('strength', 0.0)) / 2
        elif job_name == 'guard':
            return (agent.skills.get('combat', 0.0) + agent.skills.get('strength', 0.0)) / 2
        elif job_name == 'healer':
            return agent.skills.get('healing', 0.0)
        
        return 0.5  # Default aptitude
    
    def assign_new_job(self, agent, world):
        """
        Assign a new job to an agent based on village needs.
        
        Args:
            agent: The agent to assign a job to
            world: Reference to the world
            
        Returns:
            True if job was changed, False otherwise
        """
        # Unregister from current job
        self.unregister_agent(agent)
        
        # Find the most needed job
        best_job = None
        best_need = -1
        
        job_need_map = {
            'farmer': 'food',
            'woodcutter': 'wood',
            'builder': 'building',
            'miner': 'mining',
            'merchant': 'trading',
            'blacksmith': 'crafting',
            'guard': 'security',
            'healer': 'health'
        }
        
        for job_name, need_key in job_need_map.items():
            need_value = self.village_needs.get(need_key, 0.0)
            
            # Consider skill aptitude - agents prefer jobs they're good at
            skill_aptitude = self._get_job_skill_aptitude(agent, job_name)
            
            # Adjust need value by skill aptitude
            adjusted_need = need_value * (0.5 + 0.5 * skill_aptitude)
            
            # Check if job type is available to be created
            if job_name in self.job_types and adjusted_need > best_need:
                best_need = adjusted_need
                best_job = job_name
        
        if not best_job or best_job not in self.job_types:
            # Default to farmer if no better job found or job type not implemented
            best_job = 'farmer'
        
        # Create the new job
        job_class = self.job_types[best_job]
        new_job = job_class()
        
        # Assign to agent
        new_job.assign_to_agent(agent)
        
        # Register with new job
        self.register_agent(agent)
        
        # Record job change
        self.job_change_history.append({
            'agent_id': agent.id,
            'from_job': agent.job.name if agent.job else "unemployed",
            'to_job': best_job,
            'day': world.time_system.get_total_day()
        })
        
        return True
    
    def get_current_distribution(self) -> Dict[str, int]:
        """
        Get the current job distribution.
        
        Returns:
            Dictionary of job_name -> count
        """
        return self.current_distribution.copy()
    
    def get_target_distribution(self) -> Dict[str, float]:
        """
        Get the target job distribution.
        
        Returns:
            Dictionary of job_name -> percentage
        """
        return self.target_distribution.copy()
    
    def get_needs_summary(self) -> Dict[str, float]:
        """
        Get a summary of current village needs.
        
        Returns:
            Dictionary of need_name -> value
        """
        return self.village_needs.copy() 