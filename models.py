from typing import Dict, List, Optional, Union


class Zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: str = "normal",
        color: Optional[str] = None,
        max_drones: int = 1,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: str = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.is_start: bool = is_start
        self.is_end: bool = is_end

    def __lt__(self, other: "Zone") -> bool:
        return self.name < other.name


class Connection:
    def __init__(
        self,
        zone1: Zone,
        zone2: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.max_link_capacity: int = max_link_capacity


class SimulationMap:
    def __init__(self, nb_drones: int = 0) -> None:
        self.nb_drones: int = nb_drones
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None


class Drone:
    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        self.drone_id: int = drone_id
        self.current_location: Union[Zone, Connection] = start_zone
        self.is_arrived: bool = False
        self.path: List[Zone] = []

        # This is crucial for handling the 2-turn "restricted" zone rule
        self.transit_destination: Optional[Zone] = None

    @property
    def name(self) -> str:
        return f"D{self.drone_id}"
