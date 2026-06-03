from typing import Optional, Dict, List

class Zone:
    """
    Represents a single node (hub, start, or end) in the drone network.
    
    Attributes:
        name (str): The unique identifier for the zone.
        x (int): The X coordinate.
        y (int): The Y coordinate.
        zone_type (str): Type of the zone ('normal', 'restricted', 'priority', 'blocked'). Defaults to 'normal'.
        color (Optional[str]): Optional color tag for visual representation.
        max_drones (int): Maximum capacity of the zone. Defaults to 1.
        is_start (bool): Indicates if this is the start hub.
        is_end (bool): Indicates if this is the end hub.
    """
    def __init__(self, name: str, x: int, y: int, zone_type: str = "normal", 
                 color: Optional[str] = None, max_drones: int = 1, 
                 is_start: bool = False, is_end: bool = False) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: str = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.is_start: bool = is_start
        self.is_end: bool = is_end


class Connection:
    """
    Represents a bidirectional edge linking two zones in the network.
    
    Attributes:
        zone1 (Zone): The first connected zone.
        zone2 (Zone): The second connected zone.
        max_link_capacity (int): The maximum number of drones that can traverse this connection simultaneously.
    """
    def __init__(self, zone1: Zone, zone2: Zone, max_link_capacity: int = 1) -> None:
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.max_link_capacity: int = max_link_capacity


class SimulationMap:
    """
    The central object that holds the entire parsed drone graph.
    
    Attributes:
        nb_drones (int): The total number of drones to route.
        zones (Dict[str, Zone]): A dictionary mapping zone names to their Zone objects.
        connections (List[Connection]): A list of all connections in the network.
        start_zone (Optional[Zone]): A direct reference to the starting zone.
        end_zone (Optional[Zone]): A direct reference to the target ending zone.
    """
    def __init__(self, nb_drones: int = 0) -> None:
        self.nb_drones: int = nb_drones
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None