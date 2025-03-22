# Medieval Village Simulation - Project Structure

## Core Components

1. **Environment**
   - `world.py` - Main simulation environment 
   - `resources.py` - Resource management systems
   - `time_system.py` - Day/night and seasonal cycles

2. **Agents**
   - `agent.py` - Base agent class
   - `agent_brain.py` - Decision-making mechanisms
   - `needs.py` - Basic agent needs (hunger, rest, etc.)
   - `memory.py` - Agent memory and knowledge representation

3. **Jobs/Professions**
   - `job.py` - Base job class
   - Specific jobs:
     - `farmer.py`
     - `builder.py`
     - `miner.py`
     - `woodcutter.py`
     - `merchant.py`
     - etc.

4. **Buildings**
   - `building.py` - Base building class
   - Specific buildings:
     - `house.py`
     - `farm.py`
     - `market.py`
     - etc.

5. **Social Systems**
   - `relationships.py` - Inter-agent relationships
   - `economy.py` - Trading, currency, value systems
   - `governance.py` - Decision-making for village priorities

6. **Visualization**
   - `renderer.py` - Simple graphical representation
   - `stats.py` - Data collection and visualization

7. **Utils**
   - `config.py` - Configuration parameters
   - `logger.py` - Logging utilities

8. **Training**
   - `training.py` - RL training infrastructure
   - `reward_system.py` - Reward functions for different agent types 