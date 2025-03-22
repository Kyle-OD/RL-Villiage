from src.utils.config import Config

class TimeSystem:
    """
    Manages the flow of time in the simulation, including day/night cycles and seasons.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the time system.
        
        Args:
            config: Configuration object containing time parameters
        """
        self.config = config
        
        # Time tracking - all in ticks
        self.current_tick = 0
        self.ticks_per_hour = config.ticks_per_hour
        self.hours_per_day = 24
        self.days_per_season = 30
        self.seasons_per_year = 4
        
        # Weather
        self.current_weather = "clear"
        self.weather_change_chance = 0.1  # Chance to change weather per day
        self.possible_weather = ["clear", "rain", "fog", "storm", "snow"]
        self.season_weather = {
            "spring": ["clear", "rain", "fog"],
            "summer": ["clear", "storm"],
            "autumn": ["clear", "rain", "fog"],
            "winter": ["clear", "snow", "fog"]
        }
    
    def step(self):
        """
        Advance time by one tick.
        """
        self.current_tick += 1
        
        # Check if day changed
        if self.get_day_tick() == 0 and self.get_hour() == 0:
            self._update_weather()
    
    def get_tick(self) -> int:
        """Get the current absolute tick"""
        return self.current_tick
    
    def get_hour(self) -> int:
        """Get the current hour of the day (0-23)"""
        return (self.current_tick // self.ticks_per_hour) % self.hours_per_day
    
    def get_day_tick(self) -> int:
        """Get the tick within the current day"""
        return self.current_tick % (self.ticks_per_hour * self.hours_per_day)
    
    def get_day(self) -> int:
        """Get the current day number within the season"""
        total_day = self.current_tick // (self.ticks_per_hour * self.hours_per_day)
        return total_day % self.days_per_season
    
    def get_season_day(self) -> int:
        """Get the day within the current season (0-29)"""
        return self.get_day()
    
    def get_year_day(self) -> int:
        """Get the day within the current year (0-119)"""
        return (self.get_total_day() % (self.days_per_season * self.seasons_per_year))
    
    def get_total_day(self) -> int:
        """Get the total number of days elapsed in the simulation"""
        return self.current_tick // (self.ticks_per_hour * self.hours_per_day)
    
    def get_season(self) -> str:
        """Get the current season name"""
        season_index = (self.get_total_day() // self.days_per_season) % self.seasons_per_year
        seasons = ["spring", "summer", "autumn", "winter"]
        return seasons[season_index]
    
    def get_year(self) -> int:
        """Get the current year"""
        return self.get_total_day() // (self.days_per_season * self.seasons_per_year)
    
    def is_daytime(self) -> bool:
        """Check if it's currently daytime"""
        hour = self.get_hour()
        return 6 <= hour < 18  # Between 6am and 6pm
    
    def get_daytime_percentage(self) -> float:
        """Get a normalized value representing the time of day (0.0=midnight, 0.5=noon, 1.0=midnight)"""
        hour = self.get_hour()
        minute_percentage = (self.get_day_tick() % self.ticks_per_hour) / self.ticks_per_hour
        return (hour + minute_percentage) / self.hours_per_day
    
    def get_season_percentage(self) -> float:
        """Get a normalized value representing progress through the current season (0.0-1.0)"""
        return self.get_season_day() / self.days_per_season
    
    def get_weather(self) -> str:
        """Get the current weather condition"""
        return self.current_weather
    
    def _update_weather(self):
        """Update the weather based on season and random chance"""
        import random
        
        # Only change weather with a certain probability
        if random.random() < self.weather_change_chance:
            season = self.get_season()
            self.current_weather = random.choice(self.season_weather.get(season, ["clear"]))
    
    def get_date_time_string(self) -> str:
        """Get a formatted string representing the current date and time"""
        hour = self.get_hour()
        am_pm = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
            
        return f"Year {self.get_year()+1}, {self.get_season().capitalize()}, " \
               f"Day {self.get_season_day()+1}, {hour_12}:00 {am_pm} - {self.get_weather().capitalize()}" 