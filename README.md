# Medieval Village Simulation

A complex multi-agent reinforcement learning project that simulates autonomous agents in a medieval world. Agents work to survive and thrive through cooperation and competition in a resource-constrained environment.

## Features

- Autonomous agents with needs, skills, and memory
- Resource-constrained environment with day/night cycles and seasons
- Various job specializations (farming, woodcutting, mining, etc.)
- Realistic resource constraints requiring cooperation
- Independent, somewhat greedy agents who must work together to survive
- Dynamic economy and trading systems
- Visualization tools to observe agent behavior

## Project Structure

- **environment/**: World, resources, and time systems
- **agents/**: Agent behavior, needs, and decision-making
- **jobs/**: Job specializations and actions
- **buildings/**: Structures that agents can build and use
- **social/**: Relationships and social dynamics
- **visualization/**: Rendering and visualization tools
- **utils/**: Configuration and utility functions
- **training/**: Reinforcement learning mechanics

## Getting Started

### Prerequisites

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/medieval-village-simulation.git
   cd medieval-village-simulation
   ```

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Simulation

To run the simulation with default settings:

```
python src/main.py
```

#### Command-line Arguments

- `--config <file>`: Path to a custom configuration file
- `--headless`: Run without visualization
- `--seed <number>`: Set a random seed for reproducibility
- `--debug`: Enable debug mode

## Configuration

The simulation is highly configurable through the `config.py` module or by providing a YAML configuration file. See `src/utils/config.py` for available configuration options.

## Extending the Simulation

The project is designed to be modular and extensible:

- Add new job types by extending the `Job` class
- Create new resources in the `ResourceType` enum
- Implement new building types
- Add agent behaviors by extending the decision-making system

## Roadmap

See the [project plan](implementation_plan.md) for a detailed development roadmap.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
