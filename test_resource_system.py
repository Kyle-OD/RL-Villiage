#!/usr/bin/env python
"""
Test script for the enhanced resource processing chains and storage systems.
This script simulates a small village with different job types and demonstrates
the flow of resources through dedicated storage facilities and processing chains.
"""

import time
import random
import pygame
import sys
from typing import List, Dict, Any, Tuple

# Import the required modules
from src.environment.resources import ResourceManager, ResourceType, Resource
from src.environment.world import World
from src.environment.storage import StorageManager, Warehouse, Granary, Stockpile, Armory
from src.environment.threats import ThreatManager
from src.agents.agent import Agent
from src.utils.config import Config
from src.jobs.job_manager import JobManager
from src.jobs import (
    WoodcutterJob, MinerJob, BuilderJob, BlacksmithJob, 
    GuardJob, HealerJob, MerchantJob, FarmerJob
)

class Simulation:
    """Class to run a simulation of the village with enhanced resource systems"""
    
    def __init__(self):
        """Initialize the simulation"""
        pygame.init()
        self.screen_width = 1024
        self.screen_height = 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Medieval Village Simulation - Resource System Test")
        
        # Set up config
        self.config = Config()
        self.config.set('world_width', 100)
        self.config.set('world_height', 100)
        
        # Set up the world
        self.world = World(self.config)
        
        # Add initial resources
        self._setup_initial_resources()
        
        # Add storage facilities
        self._setup_storage_facilities()
        
        # Create agents with different jobs
        self.agents = self._create_agents()
        
        # Variables to control simulation
        self.running = True
        self.paused = False
        self.simulation_speed = 1  # Frames per step
        self.frame_count = 0
        self.display_info = True
        
        # Camera position
        self.camera_x = 0
        self.camera_y = 0
        self.cell_size = 8  # Size of each grid cell when rendered
        
        # Font for rendering text
        self.font = pygame.font.SysFont("Arial", 12)
        self.large_font = pygame.font.SysFont("Arial", 14, bold=True)
    
    def _setup_initial_resources(self):
        """Set up initial resources in the world"""
        # Add resource nodes (these will be visible on the map)
        num_resource_nodes = 40
        
        # Add wood (trees)
        for _ in range(num_resource_nodes):
            x = random.randint(10, self.config.world_width - 10)
            y = random.randint(10, self.config.world_height - 10)
            # Avoid placing too close to village center
            if abs(x - self.world.village_center[0]) > 15 or abs(y - self.world.village_center[1]) > 15:
                amount = random.uniform(50, 100)
                resource = Resource(
                    resource_type=ResourceType.TREE,
                    position=(x, y),
                    quantity=amount,
                    max_quantity=amount * 1.2,
                    regrowth_rate=0.1
                )
                self.world.resource_manager.add_resource(resource)
        
        # Add stone
        for _ in range(num_resource_nodes // 2):
            x = random.randint(10, self.config.world_width - 10)
            y = random.randint(10, self.config.world_height - 10)
            if abs(x - self.world.village_center[0]) > 20 or abs(y - self.world.village_center[1]) > 20:
                amount = random.uniform(40, 80)
                resource = Resource(
                    resource_type=ResourceType.STONE,
                    position=(x, y),
                    quantity=amount,
                    max_quantity=amount,  # Stone doesn't regrow
                    regrowth_rate=0.0
                )
                self.world.resource_manager.add_resource(resource)
        
        # Add iron ore
        for _ in range(num_resource_nodes // 3):
            x = random.randint(10, self.config.world_width - 10)
            y = random.randint(10, self.config.world_height - 10)
            if abs(x - self.world.village_center[0]) > 25 or abs(y - self.world.village_center[1]) > 25:
                amount = random.uniform(30, 60)
                resource = Resource(
                    resource_type=ResourceType.IRON_ORE,
                    position=(x, y),
                    quantity=amount,
                    max_quantity=amount,  # Ore doesn't regrow
                    regrowth_rate=0.0
                )
                self.world.resource_manager.add_resource(resource)
                
        # Add copper ore (using CLAY as substitute since there's no COPPER_ORE)
        for _ in range(num_resource_nodes // 4):
            x = random.randint(10, self.config.world_width - 10)
            y = random.randint(10, self.config.world_height - 10)
            if abs(x - self.world.village_center[0]) > 25 or abs(y - self.world.village_center[1]) > 25:
                amount = random.uniform(20, 50)
                resource = Resource(
                    resource_type=ResourceType.CLAY,  # Using CLAY as a substitute for copper
                    position=(x, y),
                    quantity=amount,
                    max_quantity=amount,  # Ore doesn't regrow
                    regrowth_rate=0.0
                )
                self.world.resource_manager.add_resource(resource)
        
        # Add food (farmland - using FOOD_WHEAT)
        for _ in range(num_resource_nodes // 2):
            x = random.randint(10, self.config.world_width - 10)
            y = random.randint(10, self.config.world_height - 10)
            # Place closer to village for farms
            if 10 < abs(x - self.world.village_center[0]) < 30 and 10 < abs(y - self.world.village_center[1]) < 30:
                amount = random.uniform(30, 70)
                resource = Resource(
                    resource_type=ResourceType.FOOD_WHEAT,
                    position=(x, y),
                    quantity=amount,
                    max_quantity=amount * 1.5,
                    regrowth_rate=0.2
                )
                self.world.resource_manager.add_resource(resource)
        
        # Add initial resources to village storage
        initial_resources = {
            ResourceType.FOOD_WHEAT: 100.0,
            ResourceType.WOOD: 80.0,
            ResourceType.STONE: 50.0,
            ResourceType.IRON_ORE: 20.0,
            ResourceType.CLAY: 15.0,  # Using CLAY as copper ore
            ResourceType.IRON_INGOT: 10.0,
            ResourceType.BASIC_TOOLS: 5.0,
            ResourceType.WEAPONS: 3.0
        }
        
        for resource_type, amount in initial_resources.items():
            self.world.resource_manager.add_to_village_storage(resource_type, amount)
    
    def _setup_storage_facilities(self):
        """Set up storage facilities in the village"""
        # Storage facilities are initialized in World.__init__, 
        # but we can add more specialized ones here if needed
        center_x, center_y = self.world.village_center
        
        # Add an armory for weapons
        armory_pos = (center_x - 3, center_y + 3)
        armory = Armory(armory_pos)
        self.world.storage_manager.add_facility(armory)
    
    def _create_agents(self) -> List[Agent]:
        """Create agents with different jobs"""
        agents = []
        center_x, center_y = self.world.village_center
        
        # Job distribution
        job_counts = {
            "woodcutter": 3,
            "miner": 2,
            "builder": 2,
            "blacksmith": 2,
            "guard": 3,
            "healer": 1,
            "merchant": 2,
            "farmer": 3
        }
        
        # Create agents
        agent_id = 0
        for job_name, count in job_counts.items():
            for _ in range(count):
                # Create agent with random starting position near village center
                x = center_x + random.randint(-5, 5)
                y = center_y + random.randint(-5, 5)
                
                agent = Agent(self.config, f"Agent {agent_id}")
                agent_id += 1
                
                # Set the agent's position
                agent.position = (x, y)
                
                # Initialize random skills
                agent.skills = {
                    "strength": random.uniform(0.1, 0.5),
                    "endurance": random.uniform(0.1, 0.5),
                    "woodcutting": random.uniform(0.1, 0.5),
                    "mining": random.uniform(0.1, 0.5),
                    "building": random.uniform(0.1, 0.5),
                    "crafting": random.uniform(0.1, 0.5),
                    "farming": random.uniform(0.1, 0.5),
                    "combat": random.uniform(0.1, 0.5),
                    "perception": random.uniform(0.1, 0.5),
                    "healing": random.uniform(0.1, 0.5),
                    "charisma": random.uniform(0.1, 0.5),
                    "negotiation": random.uniform(0.1, 0.5),
                }
                
                # Assign job based on job name
                if job_name == "woodcutter":
                    job = WoodcutterJob()
                elif job_name == "miner":
                    job = MinerJob()
                elif job_name == "builder":
                    job = BuilderJob()
                elif job_name == "blacksmith":
                    job = BlacksmithJob()
                elif job_name == "guard":
                    job = GuardJob()
                elif job_name == "healer":
                    job = HealerJob()
                elif job_name == "merchant":
                    job = MerchantJob()
                elif job_name == "farmer":
                    job = FarmerJob()
                else:
                    job = FarmerJob()  # Default
                
                # Set job for agent
                job.assign_to_agent(agent)
                
                # Initialize job_data for the agent
                agent.job_data = job.job_specific_data.copy()
                
                # Add agent to world
                self.world.add_agent(agent, x, y)
                agents.append(agent)
        
        return agents
    
    def run(self):
        """Run the simulation"""
        clock = pygame.time.Clock()
        
        # Main simulation loop
        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.simulation_speed = min(10, self.simulation_speed + 1)
                    elif event.key == pygame.K_MINUS:
                        self.simulation_speed = max(1, self.simulation_speed - 1)
                    elif event.key == pygame.K_i:
                        self.display_info = not self.display_info
                    elif event.key == pygame.K_t:
                        # Test: Spawn a threat
                        self._spawn_test_threat()
                    elif event.key == pygame.K_UP:
                        self.camera_y += 10
                    elif event.key == pygame.K_DOWN:
                        self.camera_y -= 10
                    elif event.key == pygame.K_LEFT:
                        self.camera_x += 10
                    elif event.key == pygame.K_RIGHT:
                        self.camera_x -= 10
            
            # Step the simulation if not paused
            if not self.paused:
                if self.frame_count % self.simulation_speed == 0:
                    self.step()
                self.frame_count += 1
            
            # Render the world
            self.render()
            
            # Cap frame rate
            clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def step(self):
        """Advance the simulation by one step"""
        # Step the world (advances time, resources, threats, etc.)
        self.world.step()
        
        # Process agent actions
        for agent in self.agents:
            # Decide and execute actions based on job
            if agent.job:
                action = agent.job.decide_action(agent, self.world)
                if action:
                    agent.current_action = action
                    # Pass a time_delta of 1.0 to progress_action (standard step time)
                    agent.job.progress_action(agent, self.world, 1.0)
    
    def render(self):
        """Render the current state of the simulation"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Center the camera on the village center with offset
        center_x, center_y = self.world.village_center
        center_screen_x = self.screen_width // 2
        center_screen_y = self.screen_height // 2
        
        # Calculate base offset with camera position
        offset_x = center_screen_x - (center_x * self.cell_size) + self.camera_x
        offset_y = center_screen_y - (center_y * self.cell_size) + self.camera_y
        
        # Render grid for reference
        self._render_grid(offset_x, offset_y)
        
        # Render resources
        self._render_resources(offset_x, offset_y)
        
        # Render storage facilities
        self._render_storage_facilities(offset_x, offset_y)
        
        # Render agents
        self._render_agents(offset_x, offset_y)
        
        # Render threats
        self._render_threats(offset_x, offset_y)
        
        # Render UI information
        if self.display_info:
            self._render_ui_info()
        
        # Update the display
        pygame.display.flip()
    
    def _render_grid(self, offset_x, offset_y):
        """Render a grid for the world"""
        # Draw a background terrain
        for x in range(self.config.world_width):
            for y in range(self.config.world_height):
                # Calculate screen position
                screen_x = x * self.cell_size + offset_x
                screen_y = y * self.cell_size + offset_y
                
                # Skip if offscreen
                if (screen_x < -self.cell_size or 
                    screen_y < -self.cell_size or 
                    screen_x > self.screen_width or 
                    screen_y > self.screen_height):
                    continue
                
                # Draw terrain
                terrain_color = (30, 100, 30)  # Default green
                
                # Village center is lighter
                center_x, center_y = self.world.village_center
                dist_to_center = abs(x - center_x) + abs(y - center_y)
                if dist_to_center < 10:
                    terrain_color = (60, 120, 60)  # Lighter green for village
                
                pygame.draw.rect(
                    self.screen,
                    terrain_color,
                    (screen_x, screen_y, self.cell_size, self.cell_size)
                )
    
    def _render_resources(self, offset_x, offset_y):
        """Render resource nodes on the map"""
        for x in range(self.config.world_width):
            for y in range(self.config.world_height):
                # Get resources at this position
                resources = self.world.resource_manager.get_resources_at((x, y))
                
                if not resources:
                    continue
                
                # Calculate screen position
                screen_x = x * self.cell_size + offset_x
                screen_y = y * self.cell_size + offset_y
                
                # Skip if offscreen
                if (screen_x < -self.cell_size or 
                    screen_y < -self.cell_size or 
                    screen_x > self.screen_width or 
                    screen_y > self.screen_height):
                    continue
                
                # Draw the most significant resource
                resource = resources[0]  # Just take the first one for now
                resource_color = self._get_resource_color(resource.resource_type)
                
                pygame.draw.rect(
                    self.screen,
                    resource_color,
                    (screen_x, screen_y, self.cell_size, self.cell_size)
                )
    
    def _render_storage_facilities(self, offset_x, offset_y):
        """Render storage facilities on the map"""
        for facility in self.world.storage_manager.storage_facilities:
            x, y = facility.position
            
            # Calculate screen position
            screen_x = x * self.cell_size + offset_x
            screen_y = y * self.cell_size + offset_y
            
            # Skip if offscreen
            if (screen_x < -self.cell_size or 
                screen_y < -self.cell_size or 
                screen_x > self.screen_width or 
                screen_y > self.screen_height):
                continue
            
            # Draw based on facility type
            facility_color = (180, 180, 180)  # Default gray
            if facility.__class__.__name__ == "Granary":
                facility_color = (230, 180, 90)  # Tan color for granary
            elif facility.__class__.__name__ == "Warehouse":
                facility_color = (150, 120, 90)  # Brown for warehouse
            elif facility.__class__.__name__ == "Stockpile":
                facility_color = (100, 140, 120)  # Blue-green for stockpile
            elif facility.__class__.__name__ == "Armory":
                facility_color = (180, 60, 60)  # Red for armory
            
            # Draw larger rectangle for storage
            size = self.cell_size * 2
            pygame.draw.rect(
                self.screen,
                facility_color,
                (screen_x - size//4, screen_y - size//4, size, size)
            )
            
            # Add label
            label = self.font.render(facility.__class__.__name__, True, (255, 255, 255))
            self.screen.blit(label, (screen_x - size//4, screen_y - size//4 - 12))
    
    def _render_agents(self, offset_x, offset_y):
        """Render agents on the map"""
        for agent in self.agents:
            x, y = agent.position
            
            # Calculate screen position
            screen_x = x * self.cell_size + offset_x
            screen_y = y * self.cell_size + offset_y
            
            # Skip if offscreen
            if (screen_x < -self.cell_size or 
                screen_y < -self.cell_size or 
                screen_x > self.screen_width or 
                screen_y > self.screen_height):
                continue
            
            # Draw agent with job-specific color
            agent_color = self._get_job_color(agent.job)
            
            # Draw agent as circle
            pygame.draw.circle(
                self.screen,
                agent_color,
                (screen_x + self.cell_size // 2, screen_y + self.cell_size // 2),
                max(2, self.cell_size // 2)
            )
            
            # Show current action as tiny text
            if agent.current_action and self.cell_size >= 8:
                action_text = self.font.render(agent.current_action[:10], True, (255, 255, 255))
                self.screen.blit(action_text, (screen_x, screen_y - 10))
    
    def _render_threats(self, offset_x, offset_y):
        """Render threats on the map"""
        for threat in self.world.threat_manager.active_threats:
            x, y = threat.position
            
            # Calculate screen position
            screen_x = x * self.cell_size + offset_x
            screen_y = y * self.cell_size + offset_y
            
            # Skip if offscreen
            if (screen_x < -self.cell_size or 
                screen_y < -self.cell_size or 
                screen_x > self.screen_width or 
                screen_y > self.screen_height):
                continue
            
            # Determine color based on threat type and status
            threat_color = (200, 30, 30)  # Default red
            size = self.cell_size * 2
            
            # Draw threat
            pygame.draw.polygon(
                self.screen,
                threat_color,
                [
                    (screen_x, screen_y - size//2),
                    (screen_x - size//2, screen_y + size//2),
                    (screen_x + size//2, screen_y + size//2)
                ]
            )
            
            # Show threat status and health
            status_text = self.font.render(
                f"{threat.type.name}:{threat.status.name[:3]} HP:{threat.health:.0f}",
                True, (255, 255, 255)
            )
            self.screen.blit(status_text, (screen_x - size//2, screen_y - size//2 - 15))
    
    def _render_ui_info(self):
        """Render UI information"""
        # Create background for resource display
        pygame.draw.rect(
            self.screen,
            (0, 0, 0, 128),  # Semi-transparent black
            (10, 10, 300, 350)
        )
        
        # Display village resources
        y_pos = 15
        self.screen.blit(self.large_font.render("Village Resources:", True, (255, 255, 255)), (15, y_pos))
        y_pos += 20
        
        resources = self.world.resource_manager.village_resources
        for resource_type, amount in sorted(resources.items()):
            resource_text = self.font.render(f"{resource_type}: {amount:.1f}", True, (220, 220, 220))
            self.screen.blit(resource_text, (20, y_pos))
            y_pos += 15
        
        # Add separation
        y_pos += 10
        self.screen.blit(self.large_font.render("Storage Facilities:", True, (255, 255, 255)), (15, y_pos))
        y_pos += 20
        
        # Display storage information
        for facility in self.world.storage_manager.storage_facilities:
            facility_text = self.font.render(
                f"{facility.__class__.__name__} at {facility.position}:", 
                True, (220, 220, 220)
            )
            self.screen.blit(facility_text, (20, y_pos))
            y_pos += 15
            
            # Show top 3 resources
            contents = facility.get_contents()
            for i, (res_type, amount) in enumerate(sorted(contents.items(), key=lambda x: x[1], reverse=True)):
                if i >= 3:
                    break
                content_text = self.font.render(f"  {res_type}: {amount:.1f}", True, (200, 200, 200))
                self.screen.blit(content_text, (30, y_pos))
                y_pos += 15
            
            if not contents:
                empty_text = self.font.render("  (empty)", True, (200, 200, 200))
                self.screen.blit(empty_text, (30, y_pos))
                y_pos += 15
        
        # Add control info
        controls_text = [
            "Controls:",
            "SPACE - Pause/Resume",
            "+/- - Adjust speed",
            "I - Toggle info",
            "T - Spawn test threat",
            "Arrow keys - Move camera",
            "ESC - Quit"
        ]
        
        y_pos = self.screen_height - len(controls_text) * 15 - 10
        for text in controls_text:
            self.screen.blit(self.font.render(text, True, (255, 255, 255)), (15, y_pos))
            y_pos += 15
        
        # Display simulation status
        status_text = f"Simulation {'PAUSED' if self.paused else 'RUNNING'} - Speed: {self.simulation_speed}"
        time_text = f"Time: Day {self.world.time_system.get_day()}, {self.world.time_system.get_hour()}:00"
        
        self.screen.blit(self.large_font.render(status_text, True, (255, 255, 0)), 
                       (self.screen_width - 250, 15))
        self.screen.blit(self.large_font.render(time_text, True, (255, 255, 0)), 
                       (self.screen_width - 250, 35))
    
    def _get_resource_color(self, resource_type: ResourceType) -> Tuple[int, int, int]:
        """Get color for a resource type"""
        # Use the built-in color method from ResourceType
        return ResourceType.get_color(resource_type)
    
    def _get_job_color(self, job) -> Tuple[int, int, int]:
        """Get color for a job type"""
        if not job:
            return (200, 200, 200)  # Gray for no job
        
        colors = {
            "woodcutter": (120, 80, 40),   # Brown
            "miner": (160, 160, 160),      # Silver
            "builder": (80, 100, 220),     # Blue
            "blacksmith": (220, 60, 0),    # Orange-red
            "guard": (180, 0, 20),         # Red
            "healer": (220, 180, 220),     # Pink
            "merchant": (220, 180, 0),     # Gold
            "farmer": (60, 180, 60)        # Green
        }
        
        return colors.get(job.name, (255, 255, 255))  # Default white
    
    def _spawn_test_threat(self):
        """Spawn a test threat for demonstration"""
        center_x, center_y = self.world.village_center
        
        # Determine threat position (at edge of map)
        threat_distance = 15
        angle = random.uniform(0, 2 * 3.14159)  # Random angle in radians
        
        threat_x = int(center_x + threat_distance * math.cos(angle))
        threat_y = int(center_y + threat_distance * math.sin(angle))
        
        # Ensure within bounds
        threat_x = max(0, min(self.config.world_width - 1, threat_x))
        threat_y = max(0, min(self.config.world_height - 1, threat_y))
        
        # Choose a random threat type
        threat_type = random.choice([
            "RAIDERS", "WOLVES", "BEAR", "ORC_PARTY", "TROLL"
        ])
        
        # Create and add the threat
        self.world.threat_manager.create_threat(
            threat_type=threat_type,
            position=(threat_x, threat_y),
            target=self.world.village_center
        )

if __name__ == "__main__":
    import math  # Required for threat spawning
    simulation = Simulation()
    simulation.run() 