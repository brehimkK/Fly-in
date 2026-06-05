import sys
from typing import List, Dict
from models import SimulationMap, Drone
from parser import MapParser
from pathfinder import Pathfinder

class SimulationEngine:
    """
    The central coordinator that runs the Fly-in drone routing simulation.
    It orchestrates parsing, pathfinding, and strict turn-by-turn output formatting.
    """
    
    # ANSI escape codes for mandatory visual representation in the terminal
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "gray": "\033[90m",
        "reset": "\033[0m"
    }

    def __init__(self, map_path: str) -> None:
        self.map_path: str = map_path
        self.sim_map: SimulationMap = SimulationMap()
        self.drones: List[Drone] = []
        self.timeline: Dict[int, List[str]] = {}

    def initialize(self) -> None:
        """Phase 1 & 2: Parses the map and calculates the optimal routes."""
        try:
            parser = MapParser(self.map_path)
            self.sim_map = parser.parse()
            
            if not self.sim_map.start_zone or not self.sim_map.end_zone:
                print("Simulation Error: Map must contain a start_hub and an end_hub.")
                sys.exit(1)
                
            # Create drones using the parsed nb_drones
            self.drones = [Drone(i, self.sim_map.start_zone) for i in range(1, self.sim_map.nb_drones + 1)]
            
            # Run the Cooperative A* Algorithm
            pathfinder = Pathfinder(self.sim_map, self.drones)
            pathfinder.assign_paths()
            
        except Exception as e:
            # Satisfies the rule: "Your functions should handle exceptions gracefully to avoid crashes."
            print(f"Initialization Failed: {e}")
            sys.exit(1)

    def _format_movement(self, drone_name: str, zone) -> str:
        """Helper to format the string and add required visual color representation."""
        zone_name = zone.name if hasattr(zone, 'name') else zone
        
        # Apply color if the zone metadata defined one
        if hasattr(zone, 'color') and zone.color in self.COLORS:
            color_code = self.COLORS[zone.color]
            reset_code = self.COLORS["reset"]
            return f"{color_code}{drone_name}-{zone_name}{reset_code}"
        
        return f"{drone_name}-{zone_name}"

    def build_timeline(self) -> None:
        """Converts the drones' planned paths into a strict turn-by-turn timeline."""
        for drone in self.drones:
            if not self.sim_map.start_zone:
                continue
                
            current_location_name = self.sim_map.start_zone.name
            
            for turn_index, zone in enumerate(drone.path):
                if turn_index not in self.timeline:
                    self.timeline[turn_index] = []
                    
                zone_name = zone.name if hasattr(zone, 'name') else zone
                
                # Rule: "Drones that do not move in a given turn are omitted from that line."
                if zone_name != current_location_name:
                    
                    # Rule: Format must be D<ID>-<zone>
                    formatted_move = self._format_movement(drone.name, zone)
                    self.timeline[turn_index].append(formatted_move)
                    
                    current_location_name = zone_name

    def run(self) -> None:
        """Main execution loop that prints the final simulation output."""
        self.initialize()
        self.build_timeline()
        
        total_turns = 0
        
        for turn in sorted(self.timeline.keys()):
            if self.timeline[turn]:
                # Rule: "A line must list all the drone movements that occur during that turn, space-separated."
                print(" ".join(self.timeline[turn]))
                total_turns += 1
                
        # Print secondary evaluation metrics (Optional but highly recommended for peer review)
        print(f"\n--- Simulation Complete ---")
        print(f"Total Drones Delivered: {len(self.drones)}")
        print(f"Total Simulation Turns: {total_turns}")

if __name__ == "__main__":
    # Ensure the user provides a map file when running the script
    if len(sys.argv) < 2:
        print("Usage: python3 simulator.py <path_to_map_file>")
        sys.exit(1)
        
    engine = SimulationEngine(sys.argv[1])
    engine.run()