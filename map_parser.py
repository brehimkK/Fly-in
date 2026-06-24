import sys
from typing import Dict
from models import Zone, Connection, SimulationMap


class MapParser:
    """
    Parses the drone simulation map files and builds a SimulationMap object.
    Enforces strict validation rules for zones, connections, and metadata.
    """
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.sim_map: SimulationMap = SimulationMap()
        self.has_start: bool = False
        self.has_end: bool = False

    def _raise_error(self, message: str, line_num: int) -> None:
        print(f"Parsing Error on line {line_num}: {message}")
        sys.exit(1)

    def _parse_metadata(
            self, metadata_str: str, line_num: int) -> Dict[str, str]:

        metadata: Dict[str, str] = {}

        if not metadata_str:
            return metadata

        allowed_keys = {
            "zone",
            "color",
            "max_drones",
            "max_link_capacity",
        }

        allowed_zone_types = {
            "restricted",
            "priority",
            "blocked",
        }

        # Remove [ and ]
        clean_str = metadata_str.strip("[]")

        if not clean_str:
            self._raise_error(
                "Invalid metadata format: metadata cannot be empty.",
                line_num,
            )

        pairs = clean_str.split()

        for pair in pairs:
            if "=" not in pair:
                self._raise_error(
                    f"Invalid metadata format '{pair}'. Expected key=value.",
                    line_num,
                )

            key, value = pair.split("=", 1)
            key = key.lower()
            value = value.lower()

            if not key or not value:
                self._raise_error(
                    f"Invalid metadata format '{pair}'. Key "
                    "and value cannot be empty.",
                    line_num,
                )

            if key not in allowed_keys:
                self._raise_error(
                    f"Invalid metadata key '{key}'.",
                    line_num,
                )

            if key in metadata:
                self._raise_error(
                    f"Duplicate metadata key '{key}'.",
                    line_num,
                )

            if key == "zone" and value not in allowed_zone_types:
                self._raise_error(
                    "Invalid zone type. Expected: "
                    "restricted, priority, or blocked.",
                    line_num,
                )

            if key in ("max_drones", "max_link_capacity"):
                try:
                    number = int(value)
                    if number <= 0:
                        self._raise_error(
                            f"{key} must be a positive integer.",
                            line_num,
                        )
                except ValueError:
                    self._raise_error(
                        f"{key} must be a number.",
                        line_num,
                    )

            metadata[key] = value

        return metadata

    def _parse_zone(
            self, line: str, line_num: int, is_start: bool = False,
            is_end: bool = False) -> None:

        """Parses start_hub, end_hub, and regular hub lines."""
        # Example line: hub: roof1 3 4 [zone=restricted color=red]
        parts = line.split(maxsplit=3)

        if len(parts) < 3:
            self._raise_error("Zone definition requires at"
                              " least a name, X, and Y coordinate.", line_num)

        if ":" not in parts[0]:
            self._raise_error(f"line{line_num} must ""contain ':'", line_num)

        # Remove the 'start_hub:', 'end_hub:', or 'hub:' prefix
        name = parts[1]

        # Validation: Names cannot contain dashes or spaces
        if '-' in name or ' ' in name:
            self._raise_error(f"Zone name '{name}' "
                              "cannot contain dashes or spaces.", line_num)

        if name in self.sim_map.zones:
            self._raise_error(f"Duplicate zone name '{name}'.", line_num)
        x = y = 0
        try:
            x, y = int(parts[2]), int(parts[3].split(" ")[0])
            for existing_zone in self.sim_map.zones.values():
                if existing_zone.x == x and existing_zone.y == y:
                    self._raise_error(
                        f"Zone '{name}' has the same "
                        "coordinates as zone '{existing_zone.name}'.",
                        line_num
                    )
        except ValueError:
            self._raise_error(
                "Invalid coordinates: both X and Y values"
                " are required and must be integers.", line_num)

        # Parse metadata if it exists
        metadata_str = parts[3].split(" ", 1)[1] if len(parts) > 3 else ""
        meta_dict = self._parse_metadata(metadata_str, line_num)

        zone_type = meta_dict.get("zone", "normal")
        if zone_type not in {"normal", "restricted", "priority", "blocked",
                             "NORMAL", "RESTRICTED", "PRIORITY", "BLOCKED"}:

            self._raise_error(f"Invalid zone type '{zone_type}'.", line_num)
        if is_start and zone_type.lower() == "blocked":
            self._raise_error(
                "start_hub cannot be blocked.",
                line_num
            )

        if is_end and zone_type.lower() == "blocked":
            self._raise_error(
                "end_hub cannot be blocked.",
                line_num
            )

        color = meta_dict.get("color", None)
        max_drones = 0
        try:
            max_drones = int(meta_dict.get("max_drones", 1))
            if max_drones <= 0:
                self._raise_error(
                    "max_drones must be a positive integer.", line_num)
        except ValueError:
            self._raise_error("max_drones must be an integer.", line_num)

        # Create the Zone object
        zone = Zone(name=name, x=x, y=y, zone_type=zone_type, color=color,
                    max_drones=max_drones, is_start=is_start, is_end=is_end)

        self.sim_map.zones[name] = zone
        if is_start:
            self.sim_map.start_zone = zone
        if is_end:
            self.sim_map.end_zone = zone

    def _parse_connection(self, line: str, line_num: int) -> None:
        """Parses connection lines and prevents duplicate edges."""
        # Example line: connection: roof1-roof2 [max_link_capacity=2]
        parts = line.split(maxsplit=1)

        if parts[0] != "connection:":
            self._raise_error("Invalid connection format.", line_num)

        if '-' not in parts[1]:
            self._raise_error(
                "Connection must link two zones"
                " separated by a dash (e.g., a-b).", line_num)

        zone1_name, zone2_name = parts[1].split('-', 1)
        zone2_name = zone2_name.split(" ")[0]

        # Validation: Ensure zones exist
        if (zone1_name not in self.sim_map.zones or
                zone2_name not in self.sim_map.zones):
            print(f"{zone1_name},{zone2_name.split(' ')[0]}")
            self._raise_error(
                "Connection links to an undefined zone.", line_num)

        # Validation: Check for duplicates
        for conn in self.sim_map.connections:
            if (conn.zone1.name == zone1_name and
                    conn.zone2.name == zone2_name) or \
               (conn.zone1.name == zone2_name and
                    conn.zone2.name == zone1_name):
                self._raise_error(
                    f"Duplicate connection between '{zone1_name}' "
                    "and '{zone2_name}'.", line_num)

        # Parse connection metadata
        metadata_str = ""
        if len(parts) >= 2 and " " in parts[-1]:
            metadata_str = parts[-1].split(" ", 1)[1]
        meta_dict = self._parse_metadata(metadata_str, line_num)
        max_capacity = 0
        try:
            max_capacity = int(meta_dict.get("max_link_capacity", 1))
            if max_capacity <= 0:
                self._raise_error(
                    "max_link_capacity must be a positive integer.", line_num)
        except ValueError:
            self._raise_error(
                "max_link_capacity must be an integer.", line_num)

        # Create connection
        z1 = self.sim_map.zones[zone1_name]
        z2 = self.sim_map.zones[zone2_name]
        connection = Connection(
            zone1=z1, zone2=z2, max_link_capacity=max_capacity)
        self.sim_map.connections.append(connection)

    def parse(self) -> SimulationMap:
        first_info_found = False

        try:
            with open(self.file_path, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.split("#", 1)[0].strip()
                    line = line.lower()

                    # Ignore empty lines and comments
                    if not line:
                        continue

                    if not first_info_found:
                        if not line.startswith("nb_drones:"):
                            self._raise_error(
                                "Invalid map: first "
                                "instruction must be nb_drones.",
                                line_num,
                            )
                        first_info_found = True

                    if line.startswith('nb_drones:'):
                        try:
                            nb = int(line.split(':')[1].strip())
                            if nb <= 0:
                                self._raise_error(
                                    "nb_drones must be a positive integer.",
                                    line_num,
                                )
                            self.sim_map.nb_drones = nb
                        except ValueError:
                            self._raise_error(
                                "Invalid nb_drones value.", line_num)

                    elif line.startswith('start_hub'):
                        if line.count("[") != 1 or line.count("]") != 1:
                            self._raise_error(
                                "Invalid zone format: "
                                "options must be inside [ ]. "
                                "Example: start_hub: start"
                                " 0 0 [color=green max_drones=5]",
                                line_num,
                            )

                        if self.has_start:
                            self._raise_error(
                                "Map cannot have more than one start_hub.",
                                line_num,
                            )

                        self._parse_zone(line, line_num, is_start=True)
                        self.has_start = True

                    elif line.startswith('end_hub'):
                        if line.count("[") != 1 or line.count("]") != 1:
                            self._raise_error(
                                "Invalid zone format: "
                                "options must be inside [ ]. "
                                "Example: end_hub: goal"
                                " 4 0 [color=green max_drones=5]",
                                line_num,
                            )

                        if self.has_end:
                            self._raise_error(
                                "Map cannot have more than one end_hub.",
                                line_num,
                            )

                        self._parse_zone(line, line_num, is_end=True)
                        self.has_end = True

                    elif line.startswith('hub'):
                        if line.count("[") != 1 or line.count("]") != 1:
                            self._raise_error(
                                "Invalid zone format: options"
                                " must be inside [ ]. "
                                "Example: hub: loop_a 1 0"
                                "[color=orange max_drones=2]",
                                line_num,
                            )

                        self._parse_zone(line, line_num)

                    elif line.startswith('connection'):
                        self._parse_connection(line, line_num)

                    else:
                        self._raise_error(
                            "Unrecognized line format.", line_num)

        except FileNotFoundError:
            print(f"Error: Could not find map file '{self.file_path}'")
            sys.exit(1)

        return self.sim_map
