import heapq
from typing import List, Dict, Set, Tuple, Optional
from models import SimulationMap, Zone, Drone


class Pathfinder:

    def __init__(self, sim_map: SimulationMap, drones: List[Drone]) -> None:
        self.sim_map: SimulationMap = sim_map
        self.drones: List[Drone] = drones
        self.zone_reservations: Dict[Tuple[str, int], int] = {}
        self.link_reservations: Dict[Tuple[str, str, int], int] = {}

    def _is_zone_available(self, zone: Zone, turn: int) -> bool:
        """Checks if a zone has capacity at a specific future turn."""
        if zone.is_start or zone.is_end:
            return True
        current_occupancy = self.zone_reservations.get((zone.name, turn), 0)
        return current_occupancy < zone.max_drones

    def _is_link_available(
            self, z1: str, z2: str, turn: int, max_cap: int) -> bool:
        """Checks if a connection has capacity during a specific turn."""
        occupancy = self.link_reservations.get((z1, z2, turn), 0) + \
            self.link_reservations.get((z2, z1, turn), 0)
        return occupancy < max_cap

    def _reserve_path(self,
                      path_sequence: List[Tuple[Zone, int]],
                      drone: Drone) -> None:
        """Saves the path into the time-space reservation dictionaries."""
        drone.path = []
        for i in range(len(path_sequence)):
            zone, turn = path_sequence[i]
            drone.path.append(zone)

            if not zone.is_start and not zone.is_end:
                self.zone_reservations[(zone.name, turn)] = (
                    self.zone_reservations.get((zone.name, turn), 0) + 1
                )
            if i > 0:
                prev_zone, prev_turn = path_sequence[i-1]
                # Find the connection capacity
                for conn in self.sim_map.connections:
                    is_connection_match = (
                        (conn.zone1 == prev_zone and conn.zone2 == zone) or
                        (conn.zone1 == zone and conn.zone2 == prev_zone)
                    )
                    if is_connection_match:
                        key = (prev_zone.name, zone.name, prev_turn)
                        self.link_reservations[key] =\
                            self.link_reservations.get(key, 0) + 1
                        break

    def find_path_for_drone(self,
                            start_turn: int) -> Optional[List[Tuple[Zone,
                                                                    int]]]:
        start = self.sim_map.start_zone
        end = self.sim_map.end_zone
        zone_count = len(self.sim_map.zones)
        drone_count = len(self.drones)

        max_turn_limit = max(200, zone_count * drone_count * 10)

        " Queue stores: (accumulated_cost, current_turn,"
        " zone_name, path_history(zone_name, turn))"
        if start is None:
            raise ValueError("Start zone cannot be None")
        queue: List[Tuple[float, int, str, List[Tuple[Zone, int]]]] = [
            (0.0, start_turn, start.name, [(start, start_turn)])
        ]

        visited: Set[Tuple[str, int]] = set()

        while queue:
            cost, turn, current_name, path = heapq.heappop(queue)
            state = (current_name, turn)
            if turn > max_turn_limit:
                print("Invalid map: start zone and end zone must "
                      "be on the same row or same column.")
                exit(1)

            if state in visited:
                continue
            visited.add(state)

            # the full zone object
            current_zone = self.sim_map.zones[current_name]

            # Reached target
            if current_zone == end:
                return path

            # OPTION 1: push to queue the same zone with cost+1/turn+1...
            if current_zone.is_start or self._is_zone_available(current_zone,
                                                                turn + 1):
                heapq.heappush(
                    queue,
                    (cost + 1.0, turn + 1, current_name, path + [(current_zone,
                                                                  turn + 1)]))
            # OPTION 2: Move to adjacent zones
            for conn in self.sim_map.connections:

                if conn.zone1.name == current_name:
                    neighbor = conn.zone2
                elif conn.zone2.name == current_name:
                    neighbor = conn.zone1
                else:
                    neighbor = None

                if neighbor and neighbor.zone_type != "blocked":
                    # Calculate movement costs and turns
                    is_restricted = (neighbor.zone_type == "restricted")
                    turn_cost = 2 if is_restricted else 1
                    arrival_turn = turn + turn_cost

                    h_cost = (
                        0.5 if neighbor.zone_type == "priority"
                        else int(turn_cost))

                    if not self._is_link_available(
                        current_name, neighbor.name,
                            turn, conn.max_link_capacity):
                        continue

                    if not self._is_zone_available(neighbor, arrival_turn):
                        continue
                    if is_restricted:
                        if not self._is_zone_available(neighbor, turn + 1):
                            continue
                        if not self._is_zone_available(neighbor, turn + 2):
                            continue
                    if is_restricted:
                        new_path = path + [
                            (neighbor, turn + 1),
                            (neighbor, turn + 2)
                        ]
                    else:
                        new_path = path + [
                            (neighbor, arrival_turn)
                        ]
                    if is_restricted and not self._is_link_available(
                        current_name, neighbor.name, turn + 1,
                        conn.max_link_capacity
                    ):
                        continue

                    # If all checks pass, add to queue
                    heapq.heappush(
                        queue,
                        (cost + h_cost, arrival_turn, neighbor.name, new_path)
                    )

        return None

    def assign_paths(self) -> None:
        for drone in self.drones:
            best_path = self.find_path_for_drone(start_turn=0)

            if best_path:
                self._reserve_path(best_path, drone)
                "Remove the starting zone at turn 0 so "
                "the simulation only executes the next steps"
                if drone.path and drone.path[0] == self.sim_map.start_zone:
                    drone.path.pop(0)
            else:
                print(f"Warning: Could not find a path for "
                      f"Drone {drone.drone_id}")
