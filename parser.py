import re
from exceptions import ParseError
from typing import Any
from webcolors import name_to_hex


DEFAULT_COLOR = "#AAAAAA"


class Parser:

    nb_drones_re = re.compile(
        r"^nb_drones\s*:\s*(\+?\d+)\s*$",
        re.IGNORECASE
    )

    zone_re = re.compile(
        r"^(start_hub|end_hub|hub)\s*:\s*([^\s\-\[\]]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[\s*(.*?)\s*\])?\s*$",
        re.IGNORECASE
    )

    connection_re = re.compile(
        r"^connection\s*:\s*([^\s\-\[\]]+)\s*-\s*([^\s\-\[\]]+)\s*(?:\[\s*(.*?)\s*\])?\s*$",
        re.IGNORECASE
    )

    metadata_item_re = re.compile(
        r"(\w+)\s*=\s*([^\s\]=]+)",
        re.IGNORECASE
    )

    def __init__(self) -> None:
        self.nb_drones = None
        self.zones = {}
        self.connections = []
        self.start_zone = None
        self.end_zone = None
        self.seen_edges = set()

    def parse(self, file_path: str):
        has_content = False
        with open(file_path, "r") as file:
            for line_number, line in enumerate(file, start=1):
                _clean_line = self.clean_line(line)
                if _clean_line == "":
                    continue
                has_content = True
                self.parse_line(_clean_line, line_number)
        if not has_content:
            raise ValueError("File contains no valid content")
        self.final_validate()

    def clean_line(self, line: str) -> str:
        line = line.strip()
        if not line or line.startswith("#"):
            return ""
        return line.split('#')[0].strip()

    def parse_line(self, line: str, nu_line: int) -> None:
        lower_line = line.lower()

        if self.nb_drones is None and not lower_line.startswith("nb_drones"):
            raise ParseError(
                f"Error on line {nu_line}: "
                "nb_drones must be defined first"
            )

        if lower_line.startswith("nb_drones:"):
            self.parse_nb_drones(line, nu_line)

        elif lower_line.startswith("start_hub:") or \
                lower_line.startswith("hub:") or \
                lower_line.startswith("end_hub:"):
            self.parse_zone_line(line, nu_line)
        elif lower_line.startswith("connection:"):
            self.parse_connection_line(line, nu_line)
        else:
            raise ParseError(f"Error on line {nu_line}: unknown line format")

    def parse_nb_drones(self, line: str, nu_line: int) -> None:
        if self.nb_drones is not None:
            raise ParseError(
                f"Error on line {nu_line}: nb_drones is defined more than once"
            )

        match = self.nb_drones_re.match(line)
        if not match:
            raise ParseError(
                f"Error on line {nu_line}: invalid nb_drones syntax"
            )

        value = int(match.group(1))

        if value <= 0:
            raise ParseError(
                f"Error on line {nu_line}: "
                "nb_drones must be a positive integer"
            )

        self.nb_drones = value

    def resolve_color(self, color: str, nu_line: int) -> str:
        """
        Convert a color string to hex.

        Accepted values:
        - CSS named colors (red, blue, green, ...)
        - Hex colors (#fff or #ffffff)
        - 'rainbow' keyword

        Raises:
            ParseError: if the color is invalid
        """

        if color is None:
            return DEFAULT_COLOR

        color = color.strip()

        if color.lower() == "rainbow":
            return "rainbow"

        # Accept hex colors
        if re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", color):
            return color.lower()

        # Accept named CSS colors
        try:
            return name_to_hex(color.lower())
        except ValueError:
            raise ParseError(
                f"Error on line {nu_line}: invalid color '{color}'"
            )

    def parse_zone_line(self, line: str, nu_line: int) -> None:
        meta_data: dict[str, str] = {}
        final_dict: dict[str, Any] = {}

        match = self.zone_re.match(line)
        if not match:
            raise ParseError(
                f"Error on line {nu_line}: invalid zone line syntax"
            )

        typezone = match.group(1).lower()
        name = match.group(2)
        x = int(match.group(3))
        y = int(match.group(4))

        if match.group(5) is not None:
            metadata_text = match.group(5)
            meta_data = self.parse_metadata(metadata_text, nu_line, line)

        if "zone" not in meta_data:
            meta_data["zone"] = "normal"
        if "color" not in meta_data:
            meta_data["color"] = None
        if "max_drones" not in meta_data:
            if typezone in ("start_hub", "end_hub"):
                meta_data["max_drones"] = self.nb_drones
            else:
                meta_data["max_drones"] = 1

        types_zone = {"normal", "blocked", "restricted", "priority"}
        zone_type = meta_data.get("zone").lower()
        if zone_type not in types_zone:
            raise ParseError(
                f"Error on line {nu_line}: invalid zone type '{zone_type}'"
            )

        # Resolve color to hex (or keep 'rainbow'), fallback to DEFAULT_COLOR
        color = self.resolve_color(meta_data.get("color"), nu_line)

        try:
            max_drones = int(meta_data.get("max_drones"))
        except (ValueError, TypeError):
            raise ParseError(
                f"Error on line {nu_line}: max_drones must be a valid integer"
            )

        if max_drones <= 0:
            raise ParseError(
                f"Error on line {nu_line}: "
                "max_drones must be a positive integer"
            )

        if typezone in ("start_hub", "end_hub"):
            if max_drones > self.nb_drones or max_drones < self.nb_drones:
                max_drones = self.nb_drones

        if name in self.zones:
            raise ParseError(
                f"Error on line {nu_line}: "
                f"zone '{name}' is defined more than once"
            )

        if typezone == "start_hub":
            if meta_data.get("zone") == "blocked":
                raise ParseError(
                    f"Error on line {nu_line}: "
                    "start hub can't be blocked zone !!!"
                )

        if typezone == "end_hub":
            if meta_data.get("zone") == "blocked":
                raise ParseError(
                    f"Error on line {nu_line}: "
                    "end hub can't be blocked zone !!!"
                )

        final_dict.update({
            "typezone": typezone,
            "name": name,
            "x": x,
            "y": y,
            "zone_type": zone_type,
            "color": color,
            "max_drones": max_drones
        })

        self.zones[name] = final_dict

        if typezone == "start_hub":
            if self.start_zone is None:
                self.start_zone = name
            else:
                raise ParseError(
                    f"Error on line {nu_line}: "
                    "start_hub is defined more than once"
                )

        if typezone == "end_hub":
            if self.end_zone is None:
                self.end_zone = name
            else:
                raise ParseError(
                    f"Error on line {nu_line}: "
                    "end_hub is defined more than once"
                )

    def parse_metadata(self, metadata_text: str, nu_line: int,
                       line: str) -> dict[str, str]:
        meta_data_dict: dict[str, str] = {}

        if not metadata_text:
            return meta_data_dict

        lower_line = line.lower()

        if lower_line.startswith("connection:"):
            allowed_keys = {"max_link_capacity"}
        elif lower_line.startswith("start_hub:") or \
            lower_line.startswith("end_hub:") or \
                lower_line.startswith("hub:"):
            allowed_keys = {"zone", "color", "max_drones"}
        else:
            raise ParseError(
                f"Error on line {nu_line}: unknown metadata context"
            )

        matches = self.metadata_item_re.findall(metadata_text)

        if not matches or \
            " ".join(f"{k}={v}" for k,
                     v in matches) != " ".join(metadata_text.strip().split()):
            raise ParseError(
                f"Error on line {nu_line}: invalid metadata syntax"
            )

        for key, value in matches:
            key = key.lower()

            if key not in allowed_keys:
                raise ParseError(
                    f"Error on line {nu_line}: invalid metadata key '{key}'"
                )

            meta_data_dict[key] = value

        return meta_data_dict

    def parse_connection_line(self, line: str, nu_line: int) -> None:
        meta_dict: dict[Any, Any] = {}

        match = self.connection_re.match(line)
        if not match:
            raise ParseError(
                f"Error on line {nu_line}: invalid connection line syntax"
            )

        zone1 = match.group(1)
        zone2 = match.group(2)

        if match.group(3) is not None:
            meta_dict = self.parse_metadata(match.group(3), nu_line, line)

        if "max_link_capacity" not in meta_dict:
            meta_dict["max_link_capacity"] = 1

        try:
            max_link_capacity = int(meta_dict.get("max_link_capacity"))
        except (ValueError, TypeError):
            raise ParseError(
                f"Error on line {nu_line}: "
                "max_link_capacity must be a valid integer"
            )

        if max_link_capacity <= 0:
            raise ParseError(
                f"Error on line {nu_line}: "
                "max_link_capacity must be a positive integer"
            )

        if zone1 not in self.zones or zone2 not in self.zones:
            raise ParseError(
                f"Error on line {nu_line}: "
                "connection uses undefined zone"
            )

        if zone1 == zone2:
            raise ParseError(
                f"Error on line {nu_line}: "
                "connection cannot link a zone to itself"
            )

        edge_key = tuple(sorted((zone1, zone2)))
        if edge_key in self.seen_edges:
            raise ParseError(
                f"Error on line {nu_line}: "
                f"duplicate connection '{zone1}-{zone2}'"
            )

        connection_dict = {
            "from": zone1,
            "to": zone2,
            "max_link_capacity": max_link_capacity
        }

        self.seen_edges.add(edge_key)
        self.connections.append(connection_dict)

    def final_validate(self) -> None:
        if self.nb_drones is None:
            raise ParseError("nb_drones is not defined")

        if self.start_zone is None:
            raise ParseError("start_hub is not defined")

        if self.end_zone is None:
            raise ParseError("end_hub is not defined")

        if self.start_zone == self.end_zone:
            raise ParseError("start and end zones cannot be the same")

        if len(self.zones) == 0:
            raise ParseError("no zones defined")

        if len(self.connections) == 0:
            raise ParseError("no connections defined")
        connections_zones = set()
        for conn in self.connections:
            connections_zones.add(conn["from"])
            connections_zones.add(conn["to"])
        if self.start_zone not in connections_zones:
            raise ParseError(
                f"The start_hub '{self.start_zone}' has no connections."
            )
        if self.end_zone not in connections_zones:
            raise ParseError(
                f"The end_hub '{self.end_zone}' has no connections."
            )

    def build_map_data(self):
        return {
            "nb_drones": self.nb_drones,
            "zones": self.zones,
            "connections": self.connections,
            "start": self.start_zone,
            "end": self.end_zone
        }
