import pygame
import sys
import random
import argparse
import time
from typing import List, Dict, Optional

from src.utils.config import Config
from src.environment.world import World
from src.agents.agent import Agent
from src.jobs.farmer import FarmerJob
from src.visualization.renderer import Renderer

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Medieval Village Simulation")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--headless", action="store_true", help="Run without visualization")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

def initialize_simulation(config: Config) -> World:
    """
    Initialize the simulation with the given configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        Initialized world
    """
    # Create the world
    world = World(config)
    
    # Create and place agents
    agents = []
    for i in range(config.initial_agents):
        agent = Agent(config)
        
        # Place agent at a random position
        x = random.randint(0, world.width - 1)
        y = random.randint(0, world.height - 1)
        world.add_agent(agent, x, y)
        agents.append(agent)
    
    # Assign jobs to agents based on distribution
    job_distribution = config.get('job_distribution', {})
    for agent in agents:
        job_type = random.choices(
            population=list(job_distribution.keys()),
            weights=list(job_distribution.values()),
            k=1
        )[0]
        
        # Assign job based on type
        if job_type == 'farmer':
            job = FarmerJob()
            job.assign_to_agent(agent)
    
    return world

def run_simulation(world: World, config: Config, headless: bool = False):
    """
    Run the simulation with the given world and configuration.
    
    Args:
        world: The simulation world
        config: Configuration object
        headless: Whether to run without visualization
    """
    # Initialize visualization if not headless
    renderer = None
    if not headless:
        pygame.init()
        renderer = Renderer(world, config)
    
    # Main simulation loop
    running = True
    clock = pygame.time.Clock()
    tick_count = 0
    
    try:
        while running:
            # Process events
            if not headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    # Add other event handling here
            
            # Step the world
            world.step()
            
            # Step each agent
            for agent in world.agents[:]:  # Copy list to allow removal during iteration
                agent.step(world, 1.0)  # 1.0 = one tick
            
            # Update visualization
            if not headless:
                renderer.render()
                pygame.display.flip()
                clock.tick(config.fps)
            
            # Increment tick count
            tick_count += 1
            
            # Print status every hour (in simulation time)
            if tick_count % config.ticks_per_hour == 0:
                print(f"Simulation time: {world.time_system.get_date_time_string()}")
                print(f"Agents: {len(world.agents)}")
                
                # Every day, print more detailed stats
                if world.time_system.get_hour() == 0:
                    print_agent_stats(world)
    
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
    
    finally:
        if not headless:
            pygame.quit()
        print("Simulation ended")
        print_simulation_summary(world, tick_count)

def print_agent_stats(world: World):
    """
    Print statistics about agents.
    
    Args:
        world: The simulation world
    """
    # Count agents by job
    jobs_count = {}
    for agent in world.agents:
        job_name = agent.job.name if agent.job else "Unemployed"
        jobs_count[job_name] = jobs_count.get(job_name, 0) + 1
    
    print("=== Agent Statistics ===")
    print(f"Total agents: {len(world.agents)}")
    print("Jobs distribution:")
    for job_name, count in jobs_count.items():
        print(f"  {job_name}: {count}")
    
    # Average health and needs
    if world.agents:
        avg_health = sum(agent.health for agent in world.agents) / len(world.agents)
        print(f"Average health: {avg_health:.1f}")

def print_simulation_summary(world: World, tick_count: int):
    """
    Print a summary of the simulation.
    
    Args:
        world: The simulation world
        tick_count: Number of ticks executed
    """
    print("\n=== Simulation Summary ===")
    print(f"Simulation ran for {tick_count} ticks")
    print(f"Simulation time: {world.time_system.get_date_time_string()}")
    print(f"Final agent count: {len(world.agents)}")
    
    # More detailed summary here...

def main():
    """Main entry point for the simulation"""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Initialize configuration
    config = Config(args.config)
    
    # Initialize simulation
    world = initialize_simulation(config)
    
    # Run simulation
    run_simulation(world, config, args.headless)

if __name__ == "__main__":
    main() 