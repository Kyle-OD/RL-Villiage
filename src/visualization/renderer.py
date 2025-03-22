import pygame
import numpy as np
from typing import Dict, List, Optional, Tuple

from src.utils.config import Config
from src.environment.world import World

class Renderer:
    """
    Handles visualization of the simulation using Pygame.
    """
    
    def __init__(self, world: World, config: Config):
        """
        Initialize the renderer.
        
        Args:
            world: The simulation world
            config: Configuration object
        """
        self.world = world
        self.config = config
        
        # Get dimensions
        self.cell_size = config.cell_size
        self.window_width = config.window_width
        self.window_height = config.window_height
        
        # Calculate grid dimensions that fit in the window
        self.grid_width = min(world.width, self.window_width // self.cell_size)
        self.grid_height = min(world.height, self.window_height // self.cell_size)
        
        # Initialize Pygame elements
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Medieval Village Simulation")
        
        # UI elements
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 16)
        
        # Camera position (for large worlds)
        self.camera_x = 0
        self.camera_y = 0
        
        # Selected agent for detailed view
        self.selected_agent = None
    
    def render(self):
        """Render the current state of the simulation"""
        # Clear screen
        self.screen.fill((0, 0, 0))  # Black background
        
        # Create a surface for the world grid
        grid_surface = pygame.Surface((self.grid_width * self.cell_size, 
                                     self.grid_height * self.cell_size))
        
        # Render base terrain
        self._render_terrain(grid_surface)
        
        # Render resources
        self._render_resources(grid_surface)
        
        # Render buildings
        self._render_buildings(grid_surface)
        
        # Render agents
        self._render_agents(grid_surface)
        
        # Blit the grid to the screen with camera offset
        self.screen.blit(grid_surface, (0, 0))
        
        # Render UI overlay
        self._render_ui()
        
        # Render selected agent details if any
        if self.selected_agent:
            self._render_agent_details()
    
    def _render_terrain(self, surface: pygame.Surface):
        """
        Render the base terrain.
        
        Args:
            surface: The surface to render on
        """
        # Draw grid cells
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                world_x = x + self.camera_x
                world_y = y + self.camera_y
                
                # Skip if out of world bounds
                if not (0 <= world_x < self.world.width and 0 <= world_y < self.world.height):
                    continue
                
                # Base terrain color (could be more complex based on terrain type)
                color = (50, 120, 50)  # Green for grass
                
                # Draw cell
                pygame.draw.rect(
                    surface,
                    color,
                    (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                )
                
                # Draw grid lines
                pygame.draw.rect(
                    surface,
                    (40, 100, 40),  # Darker green for grid lines
                    (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size),
                    1  # Line width
                )
    
    def _render_resources(self, surface: pygame.Surface):
        """
        Render resources on the grid.
        
        Args:
            surface: The surface to render on
        """
        # Let the resource manager handle rendering
        self.world.resource_manager.render(surface)
    
    def _render_buildings(self, surface: pygame.Surface):
        """
        Render buildings on the grid.
        
        Args:
            surface: The surface to render on
        """
        for building in self.world.buildings:
            # Skip if not visible in current view
            x, y = building.position
            if not (self.camera_x <= x < self.camera_x + self.grid_width and
                   self.camera_y <= y < self.camera_y + self.grid_height):
                continue
            
            # Adjust for camera position
            screen_x = (x - self.camera_x) * self.cell_size
            screen_y = (y - self.camera_y) * self.cell_size
            
            # Draw building
            building.render(surface)
    
    def _render_agents(self, surface: pygame.Surface):
        """
        Render agents on the grid.
        
        Args:
            surface: The surface to render on
        """
        for agent in self.world.agents:
            # Skip if not visible in current view
            x, y = agent.position
            if not (self.camera_x <= x < self.camera_x + self.grid_width and
                   self.camera_y <= y < self.camera_y + self.grid_height):
                continue
            
            # Adjust for camera position
            screen_x = (x - self.camera_x) * self.cell_size
            screen_y = (y - self.camera_y) * self.cell_size
            
            # Draw agent
            # Let the agent handle its own rendering logic
            agent.render(surface)
    
    def _render_ui(self):
        """Render UI elements like time, stats, etc."""
        # Time display
        time_text = self.world.time_system.get_date_time_string()
        time_surface = self.font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (10, 10))
        
        # Agent count
        agent_text = f"Agents: {len(self.world.agents)}"
        agent_surface = self.font.render(agent_text, True, (255, 255, 255))
        self.screen.blit(agent_surface, (10, 40))
        
        # More UI elements as needed...
    
    def _render_agent_details(self):
        """Render detailed information about the selected agent"""
        if not self.selected_agent:
            return
            
        # Create a panel on the right side
        panel_width = 300
        panel_height = self.window_height
        panel_x = self.window_width - panel_width
        panel_y = 0
        
        # Draw panel background
        pygame.draw.rect(
            self.screen,
            (50, 50, 50),  # Dark gray
            (panel_x, panel_y, panel_width, panel_height)
        )
        
        # Agent name and basic info
        name_text = f"Agent: {self.selected_agent.name}"
        name_surface = self.font.render(name_text, True, (255, 255, 255))
        self.screen.blit(name_surface, (panel_x + 10, panel_y + 10))
        
        # Job
        job_text = f"Job: {self.selected_agent.job.name if self.selected_agent.job else 'Unemployed'}"
        job_surface = self.font.render(job_text, True, (255, 255, 255))
        self.screen.blit(job_surface, (panel_x + 10, panel_y + 40))
        
        # Health
        health_text = f"Health: {self.selected_agent.health:.1f}%"
        health_surface = self.font.render(health_text, True, (255, 255, 255))
        self.screen.blit(health_surface, (panel_x + 10, panel_y + 70))
        
        # Current action
        action_text = f"Action: {self.selected_agent.current_action or 'None'}"
        action_surface = self.font.render(action_text, True, (255, 255, 255))
        self.screen.blit(action_surface, (panel_x + 10, panel_y + 100))
        
        # Needs
        needs_title = "Needs:"
        needs_surface = self.font.render(needs_title, True, (255, 255, 255))
        self.screen.blit(needs_surface, (panel_x + 10, panel_y + 130))
        
        y_offset = 160
        for need_type, value in self.selected_agent.needs.items():
            need_text = f"{need_type}: {value:.1f}%"
            need_surface = self.small_font.render(need_text, True, (255, 255, 255))
            self.screen.blit(need_surface, (panel_x + 20, panel_y + y_offset))
            y_offset += 20
        
        # Skills
        skills_title = "Skills:"
        skills_surface = self.font.render(skills_title, True, (255, 255, 255))
        self.screen.blit(skills_surface, (panel_x + 10, panel_y + y_offset + 10))
        
        y_offset += 40
        for skill_name, value in self.selected_agent.skills.items():
            skill_text = f"{skill_name}: {value:.2f}"
            skill_surface = self.small_font.render(skill_text, True, (255, 255, 255))
            self.screen.blit(skill_surface, (panel_x + 20, panel_y + y_offset))
            y_offset += 20
        
        # Inventory
        inventory_title = "Inventory:"
        inventory_surface = self.font.render(inventory_title, True, (255, 255, 255))
        self.screen.blit(inventory_surface, (panel_x + 10, panel_y + y_offset + 10))
        
        y_offset += 40
        if self.selected_agent.inventory:
            for item, quantity in self.selected_agent.inventory.items():
                item_text = f"{item}: {quantity:.1f}"
                item_surface = self.small_font.render(item_text, True, (255, 255, 255))
                self.screen.blit(item_surface, (panel_x + 20, panel_y + y_offset))
                y_offset += 20
        else:
            empty_text = "Empty"
            empty_surface = self.small_font.render(empty_text, True, (255, 255, 255))
            self.screen.blit(empty_surface, (panel_x + 20, panel_y + y_offset))
    
    def handle_event(self, event):
        """
        Handle user input events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if click is within the grid
            if event.pos[0] < self.grid_width * self.cell_size and event.pos[1] < self.grid_height * self.cell_size:
                # Convert to grid coordinates
                grid_x = event.pos[0] // self.cell_size + self.camera_x
                grid_y = event.pos[1] // self.cell_size + self.camera_y
                
                # Check if there's an agent at this position
                agents_at_pos = [agent for agent in self.world.agents 
                                if agent.position == (grid_x, grid_y)]
                
                if agents_at_pos:
                    # Select the first agent at this position
                    self.selected_agent = agents_at_pos[0]
                    return True
                else:
                    # Deselect if clicking empty space
                    self.selected_agent = None
                    return True
        
        elif event.type == pygame.KEYDOWN:
            # Camera movement
            if event.key == pygame.K_LEFT:
                self.camera_x = max(0, self.camera_x - 1)
                return True
            elif event.key == pygame.K_RIGHT:
                self.camera_x = min(self.world.width - self.grid_width, self.camera_x + 1)
                return True
            elif event.key == pygame.K_UP:
                self.camera_y = max(0, self.camera_y - 1)
                return True
            elif event.key == pygame.K_DOWN:
                self.camera_y = min(self.world.height - self.grid_height, self.camera_y + 1)
                return True
        
        return False  # Event not handled 