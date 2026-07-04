import sys
from typing import Dict, List

import visualizer
from map_parser import MapParser
from models import Drone, SimulationMap
from pathfinder import Pathfinder


class SimulationEngine:
    def __init__(self, map_path: str) -> None:
        self.map_path = map_path
        self.sim_map = SimulationMap()
        self.drones: List[Drone] = []
        self.timeline: Dict[int, List[str]] = {}

    def initialize(self) -> None:
        parser = MapParser(self.map_path)
        self.sim_map = parser.parse()

        if self.sim_map.start_zone is None:
            raise ValueError("Simulation map has no start zone defined")

        self.drones = [
            Drone(i, self.sim_map.start_zone)
            for i in range(1, self.sim_map.nb_drones + 1)
        ]
        self.pathfinder = Pathfinder(self.sim_map, self.drones)
        self.pathfinder.assign_paths()

    def build_timeline(self) -> None:
        start = self.sim_map.start_zone

        if start is None:
            return

        for drone in self.drones:
            current_name = start.name
            in_transit = False

            for turn, zone in enumerate(drone.path):
                zone_name = zone.name
                is_restricted = zone.zone_type == "restricted"

                if zone_name == current_name:
                    continue

                self.timeline.setdefault(turn, [])

                if is_restricted and not in_transit:
                    move = f"{drone.name}-{current_name}-{zone_name}"
                    in_transit = True
                else:
                    move = f"{drone.name}-{zone_name}"
                    current_name = zone_name
                    in_transit = False

                self.timeline[turn].append(move)

    def run(self) -> None:
        self.initialize()
        self.build_timeline()

        for turn in sorted(self.timeline):
            if self.timeline[turn]:
                print(" ".join(self.timeline[turn]))

        visualizer.PygameVisualizer(self.sim_map, self.timeline).play()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 simulator.py <map_file_path>")
        sys.exit(1)
    try:
        SimulationEngine(sys.argv[1]).run()
    except (Exception, KeyboardInterrupt) as e:
        print(e)
