import random
from typing import Dict, List, Tuple, Any, Optional
import math
import pygame

from src.jobs.job import Job
from src.environment.resources import ResourceType

class WoodcutterJob(Job):
    """
    Woodcutter job class. Responsible for cutting trees and providing wood resources.
    Manages tree identification, chopping, and wood transportation.
    """
    
    def __init__(self):
        """Initialize the woodcutter job with skill modifiers and job-specific data"""
        super().__init__("woodcutter")
        
        # Skill modifiers for this job
        self.skill_modifiers = {
            "strength": 1.2,
            "woodcutting": 1.5,
            "endurance": 1.1
        }
        
        # Job-specific data
        self.job_specific_data = {
            "known_trees": [],           # List of known tree locations
            "current_tree": None,        # Currently targeted tree
            "chopping_progress": 0.0,    # Progress in chopping (0-100)
            "wood_harvested": 0.0,       # Amount of wood harvested so far
            "nearest_stockpile": None,   # Nearest stockpile for storing wood
            "carrying_wood": 0.0,        # Amount of wood currently carrying
            "max_carry_capacity": 25.0,  # Max amount the woodcutter can carry
            "fatigue": 0.0,              # Fatigue level (0-100)
            "trees_cut": 0               # Number of trees cut
        }
    
    def decide_action(self, agent: Any, world: Any) -> str:
        """
        Decide the next action for the agent based on current situation.
        
        Args:
            agent: The agent performing the job
            world: The world environment
            
        Returns:
            The action to perform next
        """
        job_data = agent.job_data
        
        # Find the nearest stockpile if we don't have one
        if job_data["nearest_stockpile"] is None:
            storage_facilities = world.storage_manager.get_facilities_by_type("Stockpile")
            if storage_facilities:
                # Find the closest stockpile
                agent_pos = agent.position
                closest_stockpile = min(storage_facilities, 
                                     key=lambda f: abs(f.position[0] - agent_pos[0]) + 
                                                 abs(f.position[1] - agent_pos[1]))
                job_data["nearest_stockpile"] = closest_stockpile
        
        # If carrying wood at capacity, deliver to stockpile
        if job_data["carrying_wood"] >= job_data["max_carry_capacity"]:
            return "deliver_to_stockpile"
        
        # If fatigue is high, rest
        if job_data["fatigue"] > 80:
            return "rest"
        
        # If no current tree or tree is depleted, find a new one
        if job_data["current_tree"] is None:
            return "find_tree"
        
        # Go to current tree if not there
        target_tree = job_data["current_tree"]
        if abs(agent.position[0] - target_tree[0]) > 1 or abs(agent.position[1] - target_tree[1]) > 1:
            return "go_to_tree"
        
        # Chop the tree
        return "chop_tree"
    
    def progress_action(self, agent: Any, world: Any, action_name: str):
        """
        Progress the current action forward.
        
        Args:
            agent: The agent performing the job
            world: The world environment
            action_name: The name of the action to progress
        """
        if action_name == "find_tree":
            self._progress_find_tree(agent, world)
        elif action_name == "go_to_tree":
            self._progress_go_to_tree(agent, world)
        elif action_name == "chop_tree":
            self._progress_chop_tree(agent, world)
        elif action_name == "deliver_to_stockpile":
            self._progress_deliver_to_stockpile(agent, world)
        elif action_name == "rest":
            self._progress_rest(agent, world)
    
    def _progress_find_tree(self, agent: Any, world: Any):
        """Find a tree to chop"""
        job_data = agent.job_data
        
        # Use the resource manager to find trees
        agent_pos = agent.position
        trees = world.resource_manager.find_nearby_resources(agent_pos, "wood", 15)
        
        if trees:
            # Sort by distance
            trees.sort(key=lambda tree: abs(tree[0] - agent_pos[0]) + abs(tree[1] - agent_pos[1]))
            
            # Choose the closest tree or one of the closest for variety
            closest_trees = trees[:min(3, len(trees))]
            chosen_tree = random.choice(closest_trees)
            
            # Set as current tree
            job_data["current_tree"] = chosen_tree
            
            # Add to known trees
            if chosen_tree not in job_data["known_trees"]:
                job_data["known_trees"].append(chosen_tree)
            
            # Go to the tree
            agent.current_action = "go_to_tree"
        else:
            # No trees found, rest and look again later
            agent.current_action = "rest"
    
    def _progress_go_to_tree(self, agent: Any, world: Any):
        """Progress towards reaching a tree"""
        job_data = agent.job_data
        
        # Check if we have a tree target
        if job_data["current_tree"] is None:
            agent.current_action = "find_tree"
            return
        
        # Get the tree position
        tree_pos = job_data["current_tree"]
        
        # Move toward tree
        self._move_toward_position(agent, world, tree_pos)
        
        # Check if close enough to chop (adjacent)
        if abs(agent.position[0] - tree_pos[0]) <= 1 and abs(agent.position[1] - tree_pos[1]) <= 1:
            agent.current_action = "chop_tree"
        
        # Slight fatigue from walking
        job_data["fatigue"] += 0.2
    
    def _progress_chop_tree(self, agent: Any, world: Any):
        """Chop the current tree"""
        job_data = agent.job_data
        
        # Make sure we have a tree
        if job_data["current_tree"] is None:
            agent.current_action = "find_tree"
            return
        
        # Check if tree still exists (might have been depleted by another woodcutter)
        tree_pos = job_data["current_tree"]
        tree_exists = world.resource_manager.check_resource_at(tree_pos, "wood")
        
        if not tree_exists:
            # Tree is gone, find another
            job_data["current_tree"] = None
            agent.current_action = "find_tree"
            return
        
        # Increase chopping progress based on woodcutting skill
        woodcutting_skill = agent.skills.get("woodcutting", 0)
        strength_skill = agent.skills.get("strength", 0)
        
        progress_rate = 2.5 + (woodcutting_skill * 0.5) + (strength_skill * 0.3)
        job_data["chopping_progress"] += progress_rate
        
        # Increase fatigue from chopping
        job_data["fatigue"] += 1.5
        
        # If chopping is complete
        if job_data["chopping_progress"] >= 100:
            # Calculate wood yield based on woodcutting skill
            base_yield = random.uniform(8, 12)
            skill_bonus = woodcutting_skill * 0.3
            total_yield = base_yield + skill_bonus
            
            # Try to harvest the wood from the world
            harvested = world.resource_manager.harvest_resource(tree_pos, "wood", total_yield)
            
            if harvested > 0:
                # Add to carrying amount
                job_data["carrying_wood"] += harvested
                job_data["wood_harvested"] += harvested
                job_data["trees_cut"] += 1
            
            # Reset chopping progress
            job_data["chopping_progress"] = 0
            
            # Check if tree is depleted
            if not world.resource_manager.check_resource_at(tree_pos, "wood"):
                # Tree is fully depleted, remove from known trees
                if tree_pos in job_data["known_trees"]:
                    job_data["known_trees"].remove(tree_pos)
                
                # Clear current tree
                job_data["current_tree"] = None
            
            # If carrying capacity reached, deliver to storage
            if job_data["carrying_wood"] >= job_data["max_carry_capacity"]:
                agent.current_action = "deliver_to_stockpile"
            elif job_data["fatigue"] > 80:
                agent.current_action = "rest"
            else:
                # Find another tree
                agent.current_action = "find_tree"
    
    def _progress_deliver_to_stockpile(self, agent: Any, world: Any):
        """Progress towards delivering harvested wood to a stockpile"""
        job_data = agent.job_data
        
        # If we don't have a stockpile, try to find one
        if job_data["nearest_stockpile"] is None:
            storage_facilities = world.storage_manager.get_facilities_by_type("Stockpile")
            if storage_facilities:
                # Find the closest stockpile
                agent_pos = agent.position
                closest_stockpile = min(storage_facilities, 
                                      key=lambda f: abs(f.position[0] - agent_pos[0]) + 
                                                  abs(f.position[1] - agent_pos[1]))
                job_data["nearest_stockpile"] = closest_stockpile
        
        # If we have a stockpile, move toward it
        if job_data["nearest_stockpile"]:
            stockpile = job_data["nearest_stockpile"]
            stockpile_pos = stockpile.position
            
            # Move toward stockpile
            self._move_toward_position(agent, world, stockpile_pos)
            
            # If we reached the stockpile or are adjacent, deposit wood
            if agent.position == stockpile_pos or (
                abs(agent.position[0] - stockpile_pos[0]) <= 1 and 
                abs(agent.position[1] - stockpile_pos[1]) <= 1):
                
                # Store the wood in the stockpile
                wood_amount = job_data["carrying_wood"]
                # Assuming wood is stored as "wood" resource type
                added_amount = stockpile.add_resource("wood", wood_amount)
                
                # If not all wood was added to the stockpile (it might be full)
                if added_amount < wood_amount:
                    # Add remainder to village storage
                    remaining = wood_amount - added_amount
                    world.resource_manager.add_to_village_storage("wood", remaining)
                
                # Reset carrying amount and reduce fatigue slightly (taking a break)
                job_data["carrying_wood"] = 0.0
                job_data["fatigue"] = max(0, job_data["fatigue"] - 20)
                
                # Go back to finding trees
                agent.current_action = "find_tree"
        else:
            # No stockpile found, add to village storage directly
            world.resource_manager.add_to_village_storage("wood", job_data["carrying_wood"])
            job_data["carrying_wood"] = 0.0
            job_data["fatigue"] = max(0, job_data["fatigue"] - 20)
            agent.current_action = "find_tree"
    
    def _progress_rest(self, agent: Any, world: Any):
        """Rest to reduce fatigue"""
        job_data = agent.job_data
        
        # Reduce fatigue
        fatigue_reduction = 5 + agent.skills.get("endurance", 0) * 0.5
        job_data["fatigue"] = max(0, job_data["fatigue"] - fatigue_reduction)
        
        # If rested enough, go back to work
        if job_data["fatigue"] < 30:
            agent.current_action = "find_tree"
        else:
            # Simple implementation - just idle and occasionally move around
            if random.random() < 0.2:  # 20% chance to move each tick when resting
                # Get neighboring cells
                neighbors = world.get_neighboring_cells(agent.position[0], agent.position[1])
                if neighbors:
                    # Move to a random neighboring cell
                    new_pos = random.choice(neighbors)
                    world.move_agent(agent, new_pos[0], new_pos[1])
    
    def _move_toward_position(self, agent: Any, world: Any, target_pos: Tuple[int, int]):
        """
        Move the agent toward a target position.
        
        Args:
            agent: The agent to move
            world: The world environment
            target_pos: The position to move toward
        """
        # Simple pathfinding - move toward target
        current_x, current_y = agent.position
        target_x, target_y = target_pos
        
        # Calculate direction to move (simplified)
        dx = 0
        dy = 0
        
        if current_x < target_x:
            dx = 1
        elif current_x > target_x:
            dx = -1
            
        if current_y < target_y:
            dy = 1
        elif current_y > target_y:
            dy = -1
        
        # Attempt to move (first try diagonal, then cardinal directions)
        if dx != 0 and dy != 0:
            # Try diagonal move
            new_x, new_y = current_x + dx, current_y + dy
            
            # Check if position is valid and not occupied
            entities = world.get_entities_at(new_x, new_y)
            if any(entity != agent and hasattr(entity, 'blocks_movement') and entity.blocks_movement 
                  for entity in entities):
                # If diagonal blocked, try cardinal directions
                if world.move_agent(agent, current_x + dx, current_y):
                    pass  # Moved horizontally
                elif world.move_agent(agent, current_x, current_y + dy):
                    pass  # Moved vertically
            else:
                world.move_agent(agent, new_x, new_y)  # Moved diagonally
        
        elif dx != 0:
            # Try horizontal move
            world.move_agent(agent, current_x + dx, current_y)
        elif dy != 0:
            # Try vertical move
            world.move_agent(agent, current_x, current_y + dy)
    
    def remove_from_agent(self, agent: Any):
        """
        Handle cleanup when job is removed from an agent.
        
        Args:
            agent: The agent to remove this job from
        """
        # Deliver any carried wood to storage
        job_data = agent.job_data
        if job_data.get("carrying_wood", 0) > 0:
            # Try to find the world object through the agent
            if hasattr(agent, "world") and agent.world:
                agent.world.resource_manager.add_to_village_storage("wood", job_data["carrying_wood"])
        
        super().remove_from_agent(agent) 