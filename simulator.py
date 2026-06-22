import sys
from typing import List, Dict, Any
from models import SimulationMap, Drone
from map_parser import MapParser
from pathfinder import Pathfinder
import visualizer


class SimulationEngine:
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

            # initializes all drones at the start
            if self.sim_map.start_zone is None:
                raise ValueError("Start zone cannot be None")
            self.drones = [
                Drone(i, self.sim_map.start_zone)
                for i in range(1, self.sim_map.nb_drones + 1)
            ]

            pathfinder = Pathfinder(self.sim_map, self.drones)
            pathfinder.assign_paths()

        except Exception as e:
            print(f"Initialization Failed: {e}")
            sys.exit(1)

    def _format_movement(self, drone_name: str, zone: Any) -> str:
        zone_name = zone.name if hasattr(zone, 'name') else zone

        # Apply color if the zone metadata defined one
        if hasattr(zone, 'color') and zone.color in self.COLORS:
            color_code = self.COLORS[zone.color]
            reset_code = self.COLORS["reset"]
            return f"{color_code}{drone_name}-{zone_name}{reset_code}"

        return f"{drone_name}-{zone_name}"

    def build_timeline(self) -> None:
        for drone in self.drones:
            if not self.sim_map.start_zone:
                continue
            current_location_name = self.sim_map.start_zone.name

            # NEW: Track if the drone is currently occupying a connection
            in_transit = False

            for turn_index, zone in enumerate(drone.path):
                if turn_index not in self.timeline:
                    self.timeline[turn_index] = []

                zone_name = zone.name if hasattr(zone, 'name') else str(zone)
                # Check if the target zone is marked as restricted
                is_restricted = (
                    hasattr(zone,
                            'zone_type') and zone.zone_type == "restricted"
                )
                if zone_name != current_location_name:

                    if is_restricted and not in_transit:
                        connection_name = f"{current_location_name}"
                        f"-{zone_name}"

                        self.timeline[turn_index].append(f"{drone.name}"
                                                         f"-{connection_name}")
                        in_transit = True
                    else:
                        formatted_move = self._format_movement(drone.name,
                                                               zone)
                        self.timeline[turn_index].append(formatted_move)
                        current_location_name = zone_name
                        in_transit = False

    def run(self) -> None:
        """Main execution loop that prints the final simulation output."""
        self.initialize()
        self.build_timeline()

        total_turns = 0

        for turn in sorted(self.timeline.keys()):
            if self.timeline[turn]:
                print(" ".join(self.timeline[turn]))
                total_turns += 1
        gui = visualizer.PygameVisualizer(self.sim_map, self.timeline)
        gui.play()

        print("\n--- Simulation Complete ---")
        print(f"Total Drones Delivered: {len(self.drones)}")
        print(f"Total Simulation Turns: {total_turns}")


if __name__ == "__main__":
    # Ensure the user provides a map file when running the script
    if len(sys.argv) < 2:
        print("Usage: python3 simulator.py <path_to_map_file>")
        # sys.exit(1)
    try:
        engine = SimulationEngine(sys.argv[1])
        engine.run()
    except (Exception, KeyboardInterrupt) as e:
        print(e)
