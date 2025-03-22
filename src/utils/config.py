import yaml
import os
from typing import Dict, Any, Optional

class Config:
    """
    Configuration class for the medieval village simulation.
    Handles loading and accessing configuration parameters.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file, if any
        """
        # Default configuration values
        self._config = {
            # World settings
            'world_width': 50,
            'world_height': 50,
            'initial_agents': 15,
            
            # Time settings
            'ticks_per_hour': 10,
            'time_scale': 1.0,  # Multiplier for time passing
            
            # Resource settings
            'resource_density': 0.8,  # 0.0-1.0 scale of resource abundance
            'resource_variety': 0.7,  # 0.0-1.0 scale of resource variety
            'resource_regeneration': 0.5,  # 0.0-1.0 scale of resource regeneration speed
            
            # Agent settings
            'agent_need_decay_multiplier': 1.0,  # Higher values = faster need decay
            'agent_learning_rate': 1.0,  # How quickly agents learn skills
            'agent_memory_size': 20,  # Number of events an agent remembers
            
            # Job settings
            'job_types': ['farmer', 'woodcutter', 'miner', 'builder', 'merchant'],
            'job_distribution': {  # Approximate percentage of agents with each job
                'farmer': 0.3,
                'woodcutter': 0.2,
                'miner': 0.2,
                'builder': 0.2,
                'merchant': 0.1
            },
            
            # Social settings
            'social_interaction_radius': 3,  # Cell distance for social interactions
            'relationship_decay_rate': 0.01,  # Rate at which relationships decay if not maintained
            
            # Visualization settings
            'cell_size': 16,  # Pixel size of a cell
            'window_width': 1024,
            'window_height': 768,
            'fps': 30,
            'show_ui': True,  # Whether to show the UI overlay
            
            # Logging settings
            'log_level': 'INFO',
            'log_actions': True,
            'log_file': 'simulation.log'
        }
        
        # Load configuration from file if provided
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
    
    def _load_from_file(self, config_path: str):
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                
            # Update configuration with file values
            self._config.update(file_config)
            print(f"Loaded configuration from {config_path}")
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
    
    def save_to_file(self, config_path: str):
        """
        Save current configuration to a YAML file.
        
        Args:
            config_path: Path to save configuration to
        """
        try:
            with open(config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            print(f"Saved configuration to {config_path}")
        except Exception as e:
            print(f"Error saving configuration to {config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update multiple configuration values.
        
        Args:
            config_dict: Dictionary of configuration values to update
        """
        self._config.update(config_dict)
    
    # Properties for common configuration values
    @property
    def world_width(self) -> int:
        return self._config['world_width']
    
    @property
    def world_height(self) -> int:
        return self._config['world_height']
    
    @property
    def initial_agents(self) -> int:
        return self._config['initial_agents']
    
    @property
    def ticks_per_hour(self) -> int:
        return self._config['ticks_per_hour']
    
    @property
    def cell_size(self) -> int:
        return self._config['cell_size']
    
    @property
    def window_width(self) -> int:
        return self._config['window_width']
    
    @property
    def window_height(self) -> int:
        return self._config['window_height']
    
    @property
    def fps(self) -> int:
        return self._config['fps']
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get the entire configuration as a dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy() 