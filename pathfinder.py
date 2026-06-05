import heapq
from typing import List, Dict, Set, Tuple, Optional
from models import SimulationMap, Zone, Drone

class Pathfinder:
    """
    Advanced Multi-Agent Pathfinding (MAPF) using Cooperative A* / Time-Space Dijkstra.
    Routes drones individually and reserves zones/links by time to prevent deadlocks.
    """
    def __init__(self, sim_map: SimulationMap, drones: List[Drone]) -> None:
        self.sim_map: SimulationMap = sim_map
        self.drones: List[Drone] = drones
        
        # TIME-SPACE RESERVATIONS
        # Tracks how many drones occupy a zone at a specific turn: (zone_name, turn) -> count
        self.zone_reservations: Dict[Tuple[str, int], int] = {}
        # Tracks how many drones traverse a link at a specific turn: (zone1_name, zone2_name, turn) -> count
        self.link_reservations: Dict[Tuple[str, str, int], int] = {}

    def _is_zone_available(self, zone: Zone, turn: int) -> bool:
        """Checks if a zone has capacity at a specific future turn."""
        if zone.is_start or zone.is_end:
            return True  # Start and End zones have infinite capacity
        current_occupancy = self.zone_reservations.get((zone.name, turn), 0)
        return current_occupancy < zone.max_drones

    def _is_link_available(self, z1: str, z2: str, turn: int, max_cap: int) -> bool:
        """Checks if a connection has capacity during a specific turn."""
        # Check both directions since links are bidirectional
        occupancy = self.link_reservations.get((z1, z2, turn), 0) + \
                    self.link_reservations.get((z2, z1, turn), 0)
        return occupancy < max_cap

    def _reserve_path(self, path_sequence: List[Tuple[Zone, int]], drone: Drone) -> None:
        """Saves the path into the time-space reservation dictionaries."""
        drone.path = []
        for i in range(len(path_sequence)):
            zone, turn = path_sequence[i]
            drone.path.append(zone)
            
            # Reserve the zone
            if not zone.is_start and not zone.is_end:
                self.zone_reservations[(zone.name, turn)] = self.zone_reservations.get((zone.name, turn), 0) + 1

            # Reserve the connection leading to this zone (if not the first step)
            if i > 0:
                prev_zone, prev_turn = path_sequence[i-1]
                # Find the connection capacity
                for conn in self.sim_map.connections:
                    if (conn.zone1 == prev_zone and conn.zone2 == zone) or (conn.zone1 == zone and conn.zone2 == prev_zone):
                        self.link_reservations[(prev_zone.name, zone.name, prev_turn)] = \
                            self.link_reservations.get((prev_zone.name, zone.name, prev_turn), 0) + 1
                        break

    def find_path_for_drone(self, start_turn: int) -> Optional[List[Tuple[Zone, int]]]:
        """Finds the fastest available path for a single drone, considering existing traffic."""
        start = self.sim_map.start_zone
        end = self.sim_map.end_zone
        
        if not start or not end:
            return None

        # Queue stores: (accumulated_cost, current_turn, zone_name, path_history)
        queue: List[Tuple[float, int, str, List[Tuple[Zone, int]]]] = [(0.0, start_turn, start.name, [(start, start_turn)])]
        # Visited tracks (zone_name, turn) instead of just zone_name to allow waiting
        visited: Set[Tuple[str, int]] = set()

        while queue:
            cost, turn, current_name, path = heapq.heappop(queue)
            state = (current_name, turn)

            if state in visited:
                continue
            visited.add(state)
            current_zone = self.sim_map.zones[current_name]

            # Reached target
            if current_zone == end:
                return path

            # OPTION 1: Wait in the current zone for 1 turn (if it's not the start/end, check capacity)
            if current_zone.is_start or self._is_zone_available(current_zone, turn + 1):
                heapq.heappush(queue, (cost + 1.0, turn + 1, current_name, path + [(current_zone, turn + 1)]))

            # OPTION 2: Move to adjacent zones
            for conn in self.sim_map.connections:
                neighbor = conn.zone2 if conn.zone1.name == current_name else (conn.zone1 if conn.zone2.name == current_name else None)
                
                if neighbor and neighbor.zone_type != "blocked":
                    # Calculate movement costs and turns
                    is_restricted = (neighbor.zone_type == "restricted")
                    turn_cost = 2 if is_restricted else 1
                    arrival_turn = turn + turn_cost
                    
                    # Heuristic cost (prefer priority zones)
                    h_cost = 0.5 if neighbor.zone_type == "priority" else float(turn_cost)

                    # Validation: Does the connection have capacity?
                    if not self._is_link_available(current_name, neighbor.name, turn, conn.max_link_capacity):
                        continue
                    
                    # Validation: Does the destination have capacity when we arrive?
                    if not self._is_zone_available(neighbor, arrival_turn):
                        continue
                        
                    # Validation: If restricted, connection must also be empty during the transit turn
                    if is_restricted and not self._is_link_available(current_name, neighbor.name, turn + 1, conn.max_link_capacity):
                        continue
                    # If all checks pass, add to queue
                    heapq.heappush(queue, (cost + h_cost, arrival_turn, neighbor.name, path + [(neighbor, arrival_turn)]))
                    
        return None # No path found (trapped)

    def assign_paths(self) -> None:
        """Main orchestrator: Routes drones sequentially to avoid collisions."""
        # Optional optimization: Sort drones to prioritize certain routing logic if needed
        for drone in self.drones:
            # All drones start calculating from turn 0
            best_path = self.find_path_for_drone(start_turn=0)
            
            if best_path:
                self._reserve_path(best_path, drone)
                # Remove the starting zone at turn 0 so the simulation only executes the next steps
                if drone.path and drone.path[0] == self.sim_map.start_zone:
                    drone.path.pop(0)
            else:
                print(f"Warning: Could not find a path for Drone {drone.drone_id}")
