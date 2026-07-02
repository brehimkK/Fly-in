import sys
from typing import Dict

from models import Connection, SimulationMap, Zone


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
        self,
        metadata_str: str,
        line_num: int,
    ) -> Dict[str, str]:
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
            "normal",
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
            key = key.lower().lstrip()
            value = value.lower().lstrip()

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
        self,
        line: str,
        line_num: int,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        """Parses start_hub, end_hub, and regular hub lines."""

        zone_prefix, zone_data = line.split(":", 1)
        zone_prefix = zone_prefix.strip()
        zone_data = zone_data.strip()

        parts = zone_data.split(maxsplit=3)

        if len(parts) < 3:
            self._raise_error(
                "Zone definition requires at least a"
                " name, X, and Y coordinate.",
                line_num,
            )

        name = parts[0]

        if "-" in name or " " in name:
            self._raise_error(
                f"Zone name '{name}' cannot contain dashes or spaces.",
                line_num,
            )

        if name in self.sim_map.zones:
            self._raise_error(f"Duplicate zone name '{name}'.", line_num)

        try:
            x = int(parts[1])
            y = int(parts[2])

            for existing_zone in self.sim_map.zones.values():
                if existing_zone.x == x and existing_zone.y == y:
                    self._raise_error(
                        f"Zone '{name}' has the same "
                        f"coordinates as zone '{existing_zone.name}'.",
                        line_num,
                    )

        except ValueError:
            self._raise_error(
                "Invalid coordinates: both X and Y values are required "
                "and must be integers.",
                line_num,
            )

        metadata_str = parts[3] if len(parts) > 3 else ""
        meta_dict = self._parse_metadata(metadata_str, line_num)

        zone_type = meta_dict.get("zone", "normal")
        color = meta_dict.get("color", "white")

        if zone_type not in {
            "normal",
            "restricted",
            "priority",
            "blocked",
            "NORMAL",
            "RESTRICTED",
            "PRIORITY",
            "BLOCKED",
        }:
            self._raise_error(f"Invalid zone type '{zone_type}'.", line_num)

        if is_start and zone_type.lower() == "blocked":
            self._raise_error(
                "start_hub cannot be blocked.",
                line_num,
            )

        if is_end and zone_type.lower() == "blocked":
            self._raise_error(
                "end_hub cannot be blocked.",
                line_num,
            )

        try:
            max_drones = int(meta_dict.get("max_drones", 1))
            if max_drones <= 0:
                self._raise_error(
                    "max_drones must be a positive integer.",
                    line_num,
                )
        except ValueError:
            self._raise_error("max_drones must be an integer.", line_num)

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
            is_start=is_start,
            is_end=is_end,
        )

        self.sim_map.zones[name] = zone

        if is_start:
            self.sim_map.start_zone = zone

        if is_end:
            self.sim_map.end_zone = zone

    def _parse_connection(self, line: str, line_num: int) -> None:
        """Parses connection lines and prevents duplicate edges."""
        # Example line: connection: roof1-roof2 [max_link_capacity=2]
        parts = line.split(":", 1)

        if len(parts) != 2:
            self._raise_error("Invalid connection format.", line_num)

        if not self.has_start:
            print("No start zone provided")
            exit(1)

        if not self.has_end:
            print("No end zone provided", line_num - 2)
            exit(1)

        link_type = parts[0].strip()
        if link_type != "connection":
            self._raise_error("Invalid connection format.", line_num)

        connection_data = parts[1].strip()

        if "-" not in connection_data:
            self._raise_error(
                "Connection must link two "
                "zones separated by a dash (e.g., a-b).",
                line_num,
            )

        zone1_name, zone2_name = connection_data.split("-", 1)
        zone1_name = zone1_name.strip()
        zone2_name = zone2_name.split(" ")[0].strip()

        # Validation: Ensure zones exist
        if (
            zone1_name not in self.sim_map.zones
            or zone2_name not in self.sim_map.zones
        ):
            print(f"{zone1_name},{zone2_name.split(' ')[0]}")
            self._raise_error(
                "Connection links to an undefined zone.",
                line_num,
            )

        # Validation: Check for duplicates
        for conn in self.sim_map.connections:
            if (
                (
                    conn.zone1.name == zone1_name
                    and conn.zone2.name == zone2_name
                )
                or (
                    conn.zone1.name == zone2_name
                    and conn.zone2.name == zone1_name
                )
            ):
                self._raise_error(
                    f"Duplicate connection between '{zone1_name}' "
                    f"and '{zone2_name}'.",
                    line_num,
                )

        # Parse connection metadata
        metadata_str = ""
        if len(parts) >= 2 and " " in connection_data:
            metadata_str = connection_data.split(" ", 1)[1]

        meta_dict = self._parse_metadata(metadata_str, line_num)

        max_capacity = 0
        try:
            max_capacity = int(meta_dict.get("max_link_capacity", 1))
            if max_capacity <= 0:
                self._raise_error(
                    "max_link_capacity must be a positive integer.",
                    line_num,
                )
        except ValueError:
            self._raise_error(
                "max_link_capacity must be an integer.",
                line_num,
            )

        # Create connection
        z1 = self.sim_map.zones[zone1_name]
        z2 = self.sim_map.zones[zone2_name]
        connection = Connection(
            zone1=z1,
            zone2=z2,
            max_link_capacity=max_capacity,
        )
        self.sim_map.connections.append(connection)

    def _validate_optional_metadata_block(
        self,
        line: str,
        line_num: int,
        example: str,
    ) -> None:
        """Validate metadata only if the line contains metadata."""
        open_count = line.count("[")
        close_count = line.count("]")

        # Metadata is optional, so no [ ] is valid.
        if open_count == 0 and close_count == 0:
            return

        # If one bracket exists, both must exist exactly once.
        if open_count != 1 or close_count != 1:
            self._raise_error(
                "Invalid zone format: metadata must be complete inside [ ]. "
                f"Example: {example}",
                line_num,
            )

        open_index = line.index("[")
        close_index = line.index("]")

        if open_index > close_index:
            self._raise_error(
                "Invalid zone format: '[' must come before ']'.",
                line_num,
            )

        if line[close_index + 1:].strip():
            self._raise_error(
                "Invalid zone format: nothing is allowed after ']'.",
                line_num,
            )

    def parse(self) -> SimulationMap:
        first_info_found = False

        try:
            with open(self.file_path, "r") as file:
                for line_num, line in enumerate(file, 1):
                    line = line.split("#", 1)[0].strip()
                    line_type = line.split(":", 1)[0].strip().lower()

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

                    if line_type == "nb_drones":
                        try:
                            nb = int(line.split(":")[1].strip())
                            if nb <= 0:
                                self._raise_error(
                                    "nb_drones must be a positive integer.",
                                    line_num,
                                )
                            if self.sim_map.nb_drones:
                                self._raise_error(
                                    "map must contain "
                                    "one 'nb_drones'",
                                    line_num,
                                )
                                exit(1)
                            self.sim_map.nb_drones = nb
                        except ValueError:
                            self._raise_error(
                                "Invalid nb_drones value.",
                                line_num,
                            )

                    elif line_type == "start_hub":
                        self._validate_optional_metadata_block(
                            line,
                            line_num,
                            "start_hub: start 0 0 [color=green max_drones=5]",
                        )

                        if self.has_start:
                            self._raise_error(
                                "Map cannot have more than one start_hub.",
                                line_num,
                            )

                        self._parse_zone(line, line_num, is_start=True)
                        self.has_start = True

                    elif line_type == "end_hub":
                        self._validate_optional_metadata_block(
                            line,
                            line_num,
                            "end_hub: goal 4 0 [color=green max_drones=5]",
                        )

                        if self.has_end:
                            self._raise_error(
                                "Map cannot have more than one end_hub.",
                                line_num,
                            )

                        self._parse_zone(line, line_num, is_end=True)
                        self.has_end = True

                    elif line_type == "hub":
                        self._validate_optional_metadata_block(
                            line,
                            line_num,
                            "hub: loop_a 1 0 [color=orange max_drones=2]",
                        )

                        self._parse_zone(line, line_num)

                    elif line_type == "connection":
                        self._parse_connection(line, line_num)

                    else:
                        self._raise_error(
                            "Unrecognized line format.",
                            line_num,
                        )

        except FileNotFoundError:
            print(f"Error: Could not find map file '{self.file_path}'")
            sys.exit(1)

        return self.sim_map
