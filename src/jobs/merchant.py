import random
from typing import Dict, List, Optional, Any

from src.jobs.job import Job
from src.environment.resources import ResourceType

class MerchantJob(Job):
    """
    Merchant job responsible for trading, buying and selling resources.
    Merchants travel to other villages, manage the village's market, and facilitate commerce.
    """
    
    def __init__(self):
        """Initialize the merchant job with appropriate skills and data"""
        super().__init__("merchant", "Buys, sells, and trades resources")
        
        # Set skill modifiers - merchants get bonuses to these skills
        self.skill_modifiers = {
            "negotiation": 0.8,   # Major boost to negotiation
            "perception": 0.2,    # Minor boost to perception
            "charisma": 0.5       # Good boost to charisma
        }
        
        # Job-specific data
        self.job_specific_data = {
            "market_position": None,        # Location of the market
            "known_trade_routes": [],       # Known routes to trade with
            "current_trade_route": None,    # Current route being traveled
            "trade_inventory": {},          # Resources being carried for trade
            "max_inventory_capacity": 50.0, # Maximum resources that can be carried
            "current_inventory_value": 0.0, # Value of current inventory
            "profit_earned": 0.0,           # Total profit earned
            "trades_completed": 0,          # Number of successful trades
            "trade_status": "idle",         # Current trading status
            "trade_timer": 0.0              # Timer for trade-related actions
        }
        
        # Resource price data - base prices and fluctuations
        self.job_specific_data["prices"] = {
            ResourceType.FOOD: {"base_price": 1.0, "current_multiplier": 1.0},
            ResourceType.WOOD: {"base_price": 0.8, "current_multiplier": 1.0},
            ResourceType.STONE: {"base_price": 1.2, "current_multiplier": 1.0},
            ResourceType.IRON_ORE: {"base_price": 1.5, "current_multiplier": 1.0},
            ResourceType.IRON_INGOT: {"base_price": 3.0, "current_multiplier": 1.0},
            ResourceType.GOLD: {"base_price": 5.0, "current_multiplier": 1.0},
            ResourceType.HERB: {"base_price": 1.8, "current_multiplier": 1.0},
            ResourceType.POTION: {"base_price": 4.0, "current_multiplier": 1.0},
            ResourceType.BASIC_TOOLS: {"base_price": 5.0, "current_multiplier": 1.0},
            ResourceType.WEAPONS: {"base_price": 8.0, "current_multiplier": 1.0},
            ResourceType.ADVANCED_TOOLS: {"base_price": 10.0, "current_multiplier": 1.0}
        }
        
        # Update prices with random fluctuations
        self._update_trade_prices()
    
    def decide_action(self, agent, world):
        """
        Decide the next merchant action for the agent.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
        """
        # Set up market position if not set
        if not self.job_specific_data["market_position"]:
            # For now, just use the center of village
            self.job_specific_data["market_position"] = (world.width // 2, world.height // 2)
        
        # Initialize trade routes if none exist
        if not self.job_specific_data["known_trade_routes"]:
            self._setup_trade_routes(world)
        
        # Update trade prices occasionally
        if random.random() < 0.05:  # 5% chance each decision
            self._update_trade_prices()
        
        # Check current trade status
        trade_status = self.job_specific_data["trade_status"]
        
        # Handle different trade statuses
        if trade_status == "traveling_to_trade":
            # Continue traveling to trade destination
            route = self.job_specific_data["current_trade_route"]
            if not route:
                # No active route, reset status
                self.job_specific_data["trade_status"] = "idle"
                agent._set_action("go_to_market", None)
            else:
                # Continue traveling
                destination = route["destination"]
                agent._set_action("travel_to_trade", destination)
            return
        
        elif trade_status == "trading":
            # Currently engaged in trading
            agent._set_action("conduct_trade", None)
            return
            
        elif trade_status == "returning_home":
            # Returning from a trade journey
            market_pos = self.job_specific_data["market_position"]
            agent._set_action("return_to_market", market_pos)
            return
        
        # If we're at the market, decide what to do based on inventory and needs
        if agent.position == self.job_specific_data["market_position"]:
            # Check if we have trade goods to sell
            if self.job_specific_data["trade_inventory"] and self.job_specific_data["current_inventory_value"] > 0:
                agent._set_action("sell_trade_goods", None)
                return
            
            # Check if it's time to go on a trade journey
            # Criteria: village has excess resources to trade, or needs resources from trade
            village_resources = world.resource_manager.get_village_resources()
            
            # Determine if we should go trading based on village needs
            if self._should_go_trading(village_resources):
                # Select a trade route
                route = self._select_trade_route()
                if route:
                    self.job_specific_data["current_trade_route"] = route
                    self.job_specific_data["trade_status"] = "traveling_to_trade"
                    agent._set_action("travel_to_trade", route["destination"])
                    return
            
            # If no trading needed, manage the market
            agent._set_action("manage_market", None)
            return
        
        # If not at market, go there
        agent._set_action("go_to_market", self.job_specific_data["market_position"])
    
    def progress_action(self, agent, world, time_delta: float):
        """
        Progress a merchant action.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            time_delta: Time elapsed since last step
            
        Returns:
            Result of the action's progress if any
        """
        action = agent.current_action
        
        if action == "go_to_market":
            return self._progress_go_to_market(agent, world, time_delta)
        elif action == "manage_market":
            return self._progress_manage_market(agent, world, time_delta)
        elif action == "travel_to_trade":
            return self._progress_travel_to_trade(agent, world, time_delta)
        elif action == "conduct_trade":
            return self._progress_conduct_trade(agent, world, time_delta)
        elif action == "return_to_market":
            return self._progress_return_to_market(agent, world, time_delta)
        elif action == "sell_trade_goods":
            return self._progress_sell_trade_goods(agent, world, time_delta)
        
        return None
    
    def _setup_trade_routes(self, world):
        """Set up potential trade routes"""
        # Trade routes would connect to other villages or cities outside the map
        # For simulation, create virtual trade destinations at the edges of the map
        
        routes = []
        
        # Create 2-4 trade routes in different directions
        num_routes = random.randint(2, 4)
        
        # Different possible directions (N, E, S, W, NE, SE, SW, NW)
        directions = ["north", "east", "south", "west", "northeast", "southeast", "southwest", "northwest"]
        
        # Select random directions for trade routes
        selected_directions = random.sample(directions, num_routes)
        
        for i, direction in enumerate(selected_directions):
            # Create a destination point near the edge of the map based on direction
            if direction == "north":
                x, y = world.width // 2, 0
            elif direction == "east":
                x, y = world.width - 1, world.height // 2
            elif direction == "south":
                x, y = world.width // 2, world.height - 1
            elif direction == "west":
                x, y = 0, world.height // 2
            elif direction == "northeast":
                x, y = world.width - 1, 0
            elif direction == "southeast":
                x, y = world.width - 1, world.height - 1
            elif direction == "southwest":
                x, y = 0, world.height - 1
            elif direction == "northwest":
                x, y = 0, 0
            
            # Add random offset
            x = max(0, min(world.width - 1, x + random.randint(-5, 5)))
            y = max(0, min(world.height - 1, y + random.randint(-5, 5)))
            
            # Define trade specialties - what this route is good for buying/selling
            buys = random.sample(list(ResourceType), random.randint(2, 4))
            sells = random.sample(list(ResourceType), random.randint(2, 4))
            
            # Ensure buys and sells don't completely overlap
            overlap = set(buys) & set(sells)
            if len(overlap) > 1:
                for item in list(overlap)[1:]:
                    if item in buys and random.random() < 0.5:
                        buys.remove(item)
                    elif item in sells:
                        sells.remove(item)
            
            # Create route data
            route = {
                "id": f"route_{i+1}",
                "name": f"{direction.capitalize()} Village",
                "destination": (x, y),
                "direction": direction,
                "distance": random.uniform(0.8, 1.2),  # Travel time multiplier
                "buys": buys,  # Resources they buy (we sell)
                "sells": sells,  # Resources they sell (we buy)
                "price_modifier": random.uniform(0.8, 1.2),  # Overall price modifier
                "last_visit_time": 0.0
            }
            
            routes.append(route)
        
        self.job_specific_data["known_trade_routes"] = routes
    
    def _update_trade_prices(self):
        """Update trade prices with random fluctuations"""
        for resource_type in self.job_specific_data["prices"]:
            # Apply random fluctuation (0.8-1.2 range)
            new_multiplier = random.uniform(0.8, 1.2)
            self.job_specific_data["prices"][resource_type]["current_multiplier"] = new_multiplier
    
    def _get_resource_price(self, resource_type, is_buying=True):
        """
        Get the current price for a resource.
        
        Args:
            resource_type: Type of resource
            is_buying: True if merchant is buying, False if selling
            
        Returns:
            Current price for the resource
        """
        if resource_type not in self.job_specific_data["prices"]:
            # Default price for unknown resources
            return 1.0
            
        price_data = self.job_specific_data["prices"][resource_type]
        base_price = price_data["base_price"]
        multiplier = price_data["current_multiplier"]
        
        # Apply buy/sell modifier (merchants buy low, sell high)
        if is_buying:
            buy_modifier = 0.8  # Pay 80% of base when buying
            return base_price * multiplier * buy_modifier
        else:
            sell_modifier = 1.2  # Charge 120% of base when selling
            return base_price * multiplier * sell_modifier
    
    def _should_go_trading(self, village_resources):
        """
        Determine if merchant should go on a trading journey based on village resources.
        
        Args:
            village_resources: Current village resource quantities
            
        Returns:
            True if merchant should go trading, False otherwise
        """
        # Check if we have excess of any resources that we can sell
        excess_resources = []
        
        for resource_type, amount in village_resources.items():
            # Determine threshold based on resource type
            threshold = 0.0
            
            if resource_type == ResourceType.FOOD:
                threshold = 100.0  # Keep at least 100 food
            elif resource_type == ResourceType.WOOD:
                threshold = 50.0   # Keep at least 50 wood
            elif resource_type == ResourceType.STONE:
                threshold = 30.0   # Keep at least 30 stone
            elif resource_type == ResourceType.IRON_ORE:
                threshold = 20.0   # Keep at least 20 iron ore
            else:
                threshold = 10.0   # Default threshold
            
            if amount > threshold:
                excess_amount = amount - threshold
                if excess_amount >= 10.0:  # Only trade if we have a meaningful amount
                    excess_resources.append((resource_type, excess_amount))
        
        # Go trading if we have excess resources or it's been a while since last trade
        current_time = self.job_specific_data["trade_timer"]
        time_since_last_trade = current_time - self.job_specific_data.get("last_trade_time", 0.0)
        
        return len(excess_resources) > 0 or time_since_last_trade > 48.0  # Go trade every ~48 time units
    
    def _select_trade_route(self):
        """
        Select a trade route based on current needs and opportunities.
        
        Returns:
            Selected trade route or None if no suitable route
        """
        routes = self.job_specific_data["known_trade_routes"]
        if not routes:
            return None
            
        # For now, just choose a random route
        # In a more developed system, would choose based on current village needs
        return random.choice(routes)
    
    def _prepare_trade_inventory(self, agent, world):
        """
        Prepare inventory for trade journey by taking resources from village.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            
        Returns:
            Dictionary of resources collected for trade
        """
        # Clear current inventory
        self.job_specific_data["trade_inventory"] = {}
        self.job_specific_data["current_inventory_value"] = 0.0
        
        # Get current route
        route = self.job_specific_data["current_trade_route"]
        if not route:
            return {}
            
        # Determine what resources the destination buys (what we should bring to sell)
        resources_they_buy = route["buys"]
        
        # Get village resources
        village_resources = world.resource_manager.get_village_resources()
        
        # Prepare trade inventory
        trade_inventory = {}
        total_amount = 0.0
        
        for resource_type in resources_they_buy:
            # Skip if not in village resources
            if resource_type not in village_resources:
                continue
                
            village_amount = village_resources[resource_type]
            
            # Determine threshold - how much to keep in village
            threshold = 0.0
            if resource_type == ResourceType.FOOD:
                threshold = 100.0
            elif resource_type == ResourceType.WOOD:
                threshold = 50.0
            elif resource_type == ResourceType.STONE:
                threshold = 30.0
            else:
                threshold = 10.0
                
            # Calculate how much we can take
            tradeable_amount = max(0.0, village_amount - threshold)
            
            # Limit by carry capacity
            remaining_capacity = self.job_specific_data["max_inventory_capacity"] - total_amount
            take_amount = min(tradeable_amount, remaining_capacity)
            
            if take_amount > 0:
                # Take from village storage
                world.resource_manager.take_from_village_storage(resource_type, take_amount)
                
                # Add to trade inventory
                trade_inventory[resource_type] = take_amount
                total_amount += take_amount
                
                # Calculate value
                value = take_amount * self._get_resource_price(resource_type, is_buying=False)
                self.job_specific_data["current_inventory_value"] += value
        
        self.job_specific_data["trade_inventory"] = trade_inventory
        return trade_inventory
    
    def _progress_go_to_market(self, agent, world, time_delta: float):
        """Progress movement towards the market"""
        market_pos = self.job_specific_data["market_position"]
        if not market_pos:
            agent.action_progress = 1.0
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = market_pos
        
        # Already at market
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "arrived_at_market", "location": market_pos}
        
        # Move towards market
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
    
    def _progress_manage_market(self, agent, world, time_delta: float):
        """Manage the market (adjusting prices, organizing)"""
        # Update trade timer
        self.job_specific_data["trade_timer"] += time_delta
        
        # Progress action
        if agent.action_progress < 0.9:
            # Still managing
            progress_amount = 0.1 * time_delta
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "negotiation", 0.001)
            self.improve_skills(agent, "charisma", 0.002)
            
            return None
        else:
            # Management complete
            agent.action_progress = 1.0
            
            # Small chance to update prices
            if random.random() < 0.3:
                self._update_trade_prices()
            
            return {"agent": agent.name, "action": "market_managed"}
    
    def _progress_travel_to_trade(self, agent, world, time_delta: float):
        """Travel to a trading destination"""
        route = self.job_specific_data["current_trade_route"]
        if not route:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "idle"
            return {"agent": agent.name, "action": "trade_journey_cancelled", "reason": "no_route"}
            
        destination = agent.action_target
        if not destination:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "idle"
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = destination
        
        # Prepare trade inventory if we haven't already
        if not self.job_specific_data["trade_inventory"] and agent.action_progress < 0.2:
            inventory = self._prepare_trade_inventory(agent, world)
            
            # Cancel journey if inventory is empty
            if not inventory:
                agent.action_progress = 1.0
                self.job_specific_data["trade_status"] = "idle"
                return {"agent": agent.name, "action": "trade_journey_cancelled", "reason": "no_goods"}
        
        # Already at destination
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "trading"
            
            # Update last visit time
            route["last_visit_time"] = self.job_specific_data["trade_timer"]
            
            return {
                "agent": agent.name, 
                "action": "arrived_at_trade_destination", 
                "location": destination,
                "route": route["name"]
            }
        
        # Move towards destination
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Progress increases based on distance traveled and route difficulty
        distance_modifier = route["distance"]
        progress_amount = 0.05 * time_delta / distance_modifier
        
        # Arrival is imminent if we're close to destination
        manhattan_distance = abs(new_x - target_x) + abs(new_y - target_y)
        if manhattan_distance <= 2:
            progress_amount *= 2.0
        
        agent.action_progress += progress_amount
        
        # Cap progress to ensure we actually reach the destination
        if agent.action_progress >= 0.9 and manhattan_distance > 0:
            agent.action_progress = 0.89
        
        # Check if we've arrived (either by position or progress)
        if (new_x == target_x and new_y == target_y) or agent.action_progress >= 0.9:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "trading"
            
            # Update last visit time
            route["last_visit_time"] = self.job_specific_data["trade_timer"]
            
            return {
                "agent": agent.name, 
                "action": "arrived_at_trade_destination", 
                "location": destination,
                "route": route["name"]
            }
            
        return None
    
    def _progress_conduct_trade(self, agent, world, time_delta: float):
        """Conduct trade at a destination"""
        route = self.job_specific_data["current_trade_route"]
        if not route:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "returning_home"
            return {"agent": agent.name, "action": "trade_failed", "reason": "no_route"}
            
        # Trading takes time based on negotiation skill
        negotiation_skill = agent.skills["negotiation"]
        
        if agent.action_progress < 0.9:
            # Still trading
            progress_amount = (0.1 + negotiation_skill * 0.1) * time_delta
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "negotiation", 0.01)
            self.improve_skills(agent, "charisma", 0.005)
            
            return None
        else:
            # Trade complete
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "returning_home"
            
            # Process the results of the trade
            trade_results = self._process_trade_results(agent, world, route)
            
            # Update trade stats
            self.job_specific_data["trades_completed"] += 1
            self.job_specific_data["last_trade_time"] = self.job_specific_data["trade_timer"]
            
            return {
                "agent": agent.name, 
                "action": "trade_completed", 
                "route": route["name"],
                "results": trade_results
            }
    
    def _process_trade_results(self, agent, world, route):
        """
        Process the results of a completed trade.
        
        Args:
            agent: The agent performing the job
            world: Reference to the world
            route: The trade route
            
        Returns:
            Dictionary with trade results
        """
        # Get trade inventory (resources we brought to sell)
        inventory = self.job_specific_data["trade_inventory"]
        if not inventory:
            return {"status": "failed", "reason": "no_inventory"}
            
        # Calculate sell value with route and skill modifiers
        negotiation_skill = agent.skills["negotiation"]
        skill_price_bonus = 1.0 + negotiation_skill * 0.2  # 1.0-1.2 based on skill
        
        route_price_modifier = route["price_modifier"]
        
        # Sell resources
        total_sell_value = 0.0
        for resource_type, amount in inventory.items():
            base_price = self._get_resource_price(resource_type, is_buying=False)
            final_price = base_price * route_price_modifier * skill_price_bonus
            
            value = amount * final_price
            total_sell_value += value
        
        # Clear sold inventory
        self.job_specific_data["trade_inventory"] = {}
        
        # Determine what resources we can buy with our money
        resources_they_sell = route["sells"]
        
        # Pick 1-3 resource types to buy
        num_resources_to_buy = min(len(resources_they_sell), random.randint(1, 3))
        resources_to_buy = random.sample(resources_they_sell, num_resources_to_buy)
        
        # Buy resources with our money
        purchased_resources = {}
        remaining_money = total_sell_value
        
        for resource_type in resources_to_buy:
            buy_price = self._get_resource_price(resource_type, is_buying=True) * route_price_modifier
            
            # Apply negotiation skill discount
            buy_price = buy_price / skill_price_bonus
            
            # Determine how much to buy
            max_quantity = remaining_money / buy_price
            
            # Limit by capacity
            max_quantity = min(max_quantity, self.job_specific_data["max_inventory_capacity"] / num_resources_to_buy)
            
            # Add some randomness to quantity
            quantity = max_quantity * random.uniform(0.6, 1.0)
            quantity = max(0.0, quantity)
            
            if quantity > 0:
                cost = quantity * buy_price
                remaining_money -= cost
                
                # Add to purchased resources
                purchased_resources[resource_type] = quantity
        
        # Calculate profit (difference between buy and sell values)
        total_buy_value = total_sell_value - remaining_money
        profit = total_sell_value - total_buy_value
        
        # Add profit to stats
        self.job_specific_data["profit_earned"] += profit
        
        # Set new inventory for return journey
        self.job_specific_data["trade_inventory"] = purchased_resources
        self.job_specific_data["current_inventory_value"] = total_buy_value
        
        return {
            "status": "success",
            "sold_value": total_sell_value,
            "bought_value": total_buy_value,
            "profit": profit,
            "resources_bought": purchased_resources
        }
    
    def _progress_return_to_market(self, agent, world, time_delta: float):
        """Return to village market from trade journey"""
        market_pos = self.job_specific_data["market_position"]
        if not market_pos:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "idle"
            return None
            
        current_x, current_y = agent.position
        target_x, target_y = market_pos
        
        # Already at market
        if current_x == target_x and current_y == target_y:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "idle"
            
            return {
                "agent": agent.name, 
                "action": "returned_from_trade", 
                "location": market_pos
            }
        
        # Move towards market
        dx = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        dy = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        
        new_x, new_y = current_x + dx, current_y + dy
        world.move_agent(agent, new_x, new_y)
        
        # Progress increases based on distance traveled
        progress_amount = 0.05 * time_delta
        
        # Arrival is imminent if we're close to destination
        manhattan_distance = abs(new_x - target_x) + abs(new_y - target_y)
        if manhattan_distance <= 2:
            progress_amount *= 2.0
        
        agent.action_progress += progress_amount
        
        # Cap progress to ensure we actually reach the destination
        if agent.action_progress >= 0.9 and manhattan_distance > 0:
            agent.action_progress = 0.89
        
        # Check if we've arrived (either by position or progress)
        if (new_x == target_x and new_y == target_y) or agent.action_progress >= 0.9:
            agent.action_progress = 1.0
            self.job_specific_data["trade_status"] = "idle"
            
            return {
                "agent": agent.name, 
                "action": "returned_from_trade", 
                "location": market_pos
            }
            
        return None
    
    def _progress_sell_trade_goods(self, agent, world, time_delta: float):
        """Sell trade goods at the village market"""
        inventory = self.job_specific_data["trade_inventory"]
        if not inventory:
            agent.action_progress = 1.0
            return {"agent": agent.name, "action": "nothing_to_sell"}
            
        # Selling takes time based on charisma and negotiation
        charisma_skill = agent.skills["charisma"]
        negotiation_skill = agent.skills["negotiation"]
        
        if agent.action_progress < 0.9:
            # Still selling
            progress_amount = (0.1 + charisma_skill * 0.05 + negotiation_skill * 0.05) * time_delta
            agent.action_progress += progress_amount
            
            # Skill improvement from practice
            self.improve_skills(agent, "negotiation", 0.003)
            self.improve_skills(agent, "charisma", 0.003)
            
            return None
        else:
            # Selling complete
            agent.action_progress = 1.0
            
            # Add resources to village storage
            for resource_type, amount in inventory.items():
                world.resource_manager.add_to_village_storage(resource_type, amount)
            
            # Clear trade inventory
            self.job_specific_data["trade_inventory"] = {}
            self.job_specific_data["current_inventory_value"] = 0.0
            
            return {
                "agent": agent.name, 
                "action": "sold_trade_goods",
                "resources": inventory
            }
    
    def remove_from_agent(self, agent):
        """
        Remove this job from an agent, handling merchant-specific cleanup.
        
        Args:
            agent: The agent to remove the job from
        """
        # If merchant is carrying trade goods, return them to village
        inventory = self.job_specific_data["trade_inventory"]
        if inventory:
            # In a real system, this would add resources back to village storage
            self.job_specific_data["trade_inventory"] = {}
            self.job_specific_data["current_inventory_value"] = 0.0
        
        # Reset trade status
        self.job_specific_data["trade_status"] = "idle"
        self.job_specific_data["current_trade_route"] = None
        
        # Call parent remove method
        super().remove_from_agent(agent) 