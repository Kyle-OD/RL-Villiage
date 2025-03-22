from typing import Dict, List, Optional, Any
import time
import heapq

class Memory:
    """
    Stores and manages agent memories/knowledge.
    Includes mechanisms for importance, recency, and recall.
    """
    
    def __init__(self, capacity: int = 100):
        """
        Initialize memory with a specific capacity.
        
        Args:
            capacity: Maximum number of memories to store
        """
        self.capacity = capacity
        self.memories = []  # List of memory items
        self.locations = {}  # Type -> list of locations
        self.knowledge = {}  # Key -> value, for general knowledge
    
    def add_memory(self, memory_type: str, content: Dict[str, Any], importance: float = 1.0):
        """
        Add a new memory.
        
        Args:
            memory_type: Type of memory (e.g., "resource_found", "met_agent", etc.)
            content: Content of the memory
            importance: Importance score (higher = more important)
        """
        timestamp = time.time()
        memory = {
            "type": memory_type,
            "content": content.copy(),
            "importance": importance,
            "timestamp": timestamp,
            "recall_count": 0,
            "last_recalled": timestamp
        }
        
        self.memories.append(memory)
        
        # Keep memories within capacity by removing least important ones
        if len(self.memories) > self.capacity:
            self._prune_memories()
        
        # If memory includes a location, store it
        if "position" in content:
            position = content["position"]
            if memory_type not in self.locations:
                self.locations[memory_type] = []
            self.locations[memory_type].append(position)
    
    def _prune_memories(self):
        """Remove least important memories to stay within capacity"""
        # Calculate memory value based on importance, recency, and recall frequency
        for memory in self.memories:
            age = time.time() - memory["timestamp"]
            recency = 1.0 / (1.0 + age / 3600.0)  # Recency decays over hours
            recall_factor = 1.0 + (0.1 * memory["recall_count"])  # More recalls = more important
            memory["_value"] = memory["importance"] * recency * recall_factor
        
        # Sort by value and keep the most valuable ones
        self.memories.sort(key=lambda x: x["_value"], reverse=True)
        self.memories = self.memories[:self.capacity]
        
        # Clean up the _value field
        for memory in self.memories:
            if "_value" in memory:
                del memory["_value"]
    
    def recall(self, memory_type: Optional[str] = None, filter_func=None, limit: int = 5):
        """
        Recall memories by type and/or content filter.
        
        Args:
            memory_type: Type of memories to recall, or None for all
            filter_func: Function to filter memories by content
            limit: Maximum number of memories to return
            
        Returns:
            List of matching memories, sorted by importance
        """
        # Filter memories
        matches = []
        for memory in self.memories:
            if memory_type is not None and memory["type"] != memory_type:
                continue
                
            if filter_func is not None and not filter_func(memory["content"]):
                continue
                
            # Update recall stats
            memory["recall_count"] += 1
            memory["last_recalled"] = time.time()
            
            matches.append(memory)
        
        # Sort by importance and return top matches
        matches.sort(key=lambda x: x["importance"], reverse=True)
        return matches[:limit]
    
    def get_locations(self, memory_type: str) -> List:
        """
        Get all known locations of a specific type.
        
        Args:
            memory_type: Type of locations to retrieve
            
        Returns:
            List of positions
        """
        return self.locations.get(memory_type, [])
    
    def add_knowledge(self, key: str, value: Any):
        """
        Add or update a knowledge item.
        
        Args:
            key: Knowledge identifier
            value: Knowledge value
        """
        self.knowledge[key] = value
    
    def get_knowledge(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a knowledge item.
        
        Args:
            key: Knowledge identifier
            default: Default value if knowledge doesn't exist
            
        Returns:
            Knowledge value or default
        """
        return self.knowledge.get(key, default)
    
    def forget_old_memories(self, age_threshold: float = 86400.0):
        """
        Forget memories older than a threshold.
        
        Args:
            age_threshold: Age threshold in seconds (default: 24 hours)
        """
        current_time = time.time()
        self.memories = [
            memory for memory in self.memories 
            if current_time - memory["timestamp"] < age_threshold
        ]
    
    def forget_memory_type(self, memory_type: str):
        """
        Forget all memories of a specific type.
        
        Args:
            memory_type: Type of memories to forget
        """
        self.memories = [
            memory for memory in self.memories 
            if memory["type"] != memory_type
        ]
        
        if memory_type in self.locations:
            del self.locations[memory_type]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the agent's memory.
        
        Returns:
            Dictionary with memory summary
        """
        memory_types = {}
        for memory in self.memories:
            memory_type = memory["type"]
            if memory_type not in memory_types:
                memory_types[memory_type] = 0
            memory_types[memory_type] += 1
        
        return {
            "total_memories": len(self.memories),
            "capacity": self.capacity,
            "memory_types": memory_types,
            "known_locations": {k: len(v) for k, v in self.locations.items()},
            "knowledge_items": len(self.knowledge)
        } 