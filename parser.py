import re
from exceptions import ParseError
from typing import Any
from webcolors import name_to_hex


class Parser:
    """
    A class to read and validate map configuration files for a drone system.

    This parser reads a text file line by line to set up hubs, connections,
    and drone settings while checking for any format errors.

    Attributes:
        nb_drones (int | None): The total number of drones allowed.
        zones (dict): A dictionary of all hubs/zones found in the file.
        connections (list): A list of dictionaries showing links between zones.
        start_zone (str | None): The name of the starting hub.
        end_zone (str | None): The name of the ending hub.
        seen_edges (set): A set of already processed links to prevent
            duplicates.

    Example Usage:
        parser = Parser()
        parser.parse("map.txt")
        map_data = parser.build_map_data()
    """

    nb_drones_re = re.compile(
        r"^nb_drones\s*:\s*(\+?\d+)\s*$",
        re.IGNORECASE
    )

    zone_re = re.compile(
        r"^(start_hub|end_hub|hub)\s*:\s*"
        r"([^\s\-\[\]]+)\s+"
        r"(-?\d+)\s+"
        r"(-?\d+)\s*"
        r"(?:\[\s*(.*?)\s*\])?\s*$",
        re.IGNORECASE
    )

    connection_re = re.compile(
        r"^connection\s*:\s*"
        r"([^\s\-\[\]]+)\s*-\s*"
        r"([^\s\-\[\]]+)\s*(?:\[\s*(.*?)\s*\])?\s*$",
        re.IGNORECASE
    )

    metadata_item_re = re.compile(
        r"(\w+)\s*=\s*([^\s\]=]+)",
        re.IGNORECASE
    )

    def __init__(self) -> None:
        """
        Initializes a new Parser instance with empty values.

        Sets up the basic storage for drones, zones, connections, and
        tracking systems to help validate the map data.
        """
        self.nb_drones: int | None = None
        self.zones: dict[str, dict] = {}
        self.connections: list[dict[str, Any]] = []
        self.start_zone: str | None = None
        self.end_zone: str | None = None
        self.seen_edges: set[tuple[str, str]] = set()

    def parse(self, file_path: str) -> None:
        """
        Opens and reads a map configuration file line by line.

        It cleans each line, processes valid data lines, checks for errors,
        and performs a final validation check on the entire file content.

        Args:
            file_path (str): The path or location of the text file to read.

        Raises:
            ValueError: If the file is completely empty or only contains
                comments.
            ParseError: If there is a format or validation error inside
                the file.
        """
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
        """
        Removes spaces and comments from a line of text.

        It strips empty spaces from the start and end of the line. If the
        line contains a comment character (#), it cuts off the comment text
        and returns only the useful data.

        Args:
            line (str): The raw line of text read from the file.

        Returns:
            str: The cleaned line of text, or an empty string if
            the line is a comment or empty.
        """
        line = line.strip()
        if not line or line.startswith("#"):
            return ""
        return line.split('#')[0].strip()

    def parse_line(self, line: str, nu_line: int) -> None:
        """
        Identifies what type of information a line contains
        and sends it to the right handler.

        It checks the start of the line to find if it configures
        the drone count,
        a zone/hub, or a connection path.
        It also enforces the rule that the total 
        number of drones must be set before reading any other map data.

        Args:
            line (str): The cleaned text line to process.
            nu_line (int): The current line number in the file
            (used for error messages).

        Raises:
            ParseError: If 'nb_drones' is not defined first,
            or if the line has a format that cannot be recognized.
        """
        lower_line = line.lower()

        if self.nb_drones is None and not lower_line.startswith("nb_drones"):
            raise ParseError(
                f"Error on line {nu_line}: "
                "nb_drones must be defined first"
            )

        if lower_line.startswith("nb_drones"):
            self.parse_nb_drones(line, nu_line)
        elif lower_line.startswith("start_hub") or \
                lower_line.startswith("hub") or \
                lower_line.startswith("end_hub"):
            self.parse_zone_line(line, nu_line)
        elif lower_line.startswith("connection"):
            self.parse_connection_line(line, nu_line)
        else:
            raise ParseError(f"Error on line {nu_line}: unknown line format")

    def parse_nb_drones(self, line: str, nu_line: int) -> None:
        """
        Extracts and validates the total number of drones from a line.

        It checks that the number is defined only once, matches the correct
        format, and is a positive number greater than zero.

        Args:
            line (str): The text line containing the drone count data.
            nu_line (int): The current line number for error reporting.

        Raises:
            ParseError: If the drone count is duplicated, has bad syntax,
            or is not positive.
        """
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

        if (color is None or color.lower() == "none"):
            return "#AAAAAA"

        color = color.strip()

        if color.lower() == "rainbow":
            return "rainbow"

        # Accept hex colors
        if re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", color):
            return color.lower()

        # Accept named CSS colors
        try:
            return str(name_to_hex(color.lower()))
        except ValueError:
            raise ParseError(
                f"Error on line {nu_line}: invalid color '{color}'"
            )

    def parse_zone_line(self, line: str, nu_line: int) -> None:
        """
        Reads and checks a hub or zone line from the text file.

        It extracts the name, coordinates, type, color,
        and maximum drone limits.
        It also makes sure there are no duplicate names,
        and that the start or end 
        hubs are not completely blocked.

        Args:
            line (str): The text line that defines a zone or hub.
            nu_line (int): The current line number for error reporting.

        Raises:
            ParseError: If syntax is wrong, a zone is duplicated, data values
                        are invalid, or a start/end hub is set to blocked.
        """
        meta_data: dict[str, Any] = {}
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
            meta_data = dict(self.parse_metadata(metadata_text, nu_line, line))

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
        zone_type = meta_data.get("zone", "normal").lower()
        if zone_type not in types_zone:
            raise ParseError(
                f"Error on line {nu_line}: invalid zone type '{zone_type}'"
            )

        # Resolve color to hex (or keep 'rainbow'), fallback to DEFAULT_COLOR
        color_value = meta_data.get("color")
        if color_value is None:
            color = "#AAAAAA"
        else:
            color = self.resolve_color(color_value, nu_line)

        try:
            max_drones = int(meta_data.get("max_drones", "0"))
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
            if max_drones != self.nb_drones:
                if self.nb_drones is None:
                    raise ValueError("nb_drones is not initialized")
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
        """
        Reads and checks settings inside brackets like
        [zone=priority color=red].

        It makes sure the settings use the correct formatting and only contain
        allowed keywords depending on whether the line is a zone or a
        connection.

        Args:
            metadata_text (str): The raw text found inside the brackets.
            nu_line (int): The current line number for error reporting.
            line (str): The full text line to check if it is a hub or
            connection.

        Returns:
            dict[str, str]: A dictionary of the parsed settings.

        Raises:
            ParseError: If the syntax is wrong or contains unallowed keywords.
        """
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
        """
        Reads and checks a connection line linking two hubs together.

        It extracts the names of the two zones and the maximum path capacity.
        It ensures both zones exist, the path doesn't connect a zone to itself,
        and that this identical path hasn't already been created.

        Args:
            line (str): The text line defining the path connection.
            nu_line (int): The current line number for error reporting.

        Raises:
            ParseError: If syntax is invalid, a zone doesn't exist, the link
                        connects to itself, or the connection is duplicated.
        """
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
            max_link_capacity = int(meta_dict.get("max_link_capacity", "0"))
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

        edge_key = tuple(sorted((str(zone1), str(zone2))))
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
        u, v = edge_key
        self.seen_edges.add((u, v))
        self.connections.append(connection_dict)

    def final_validate(self) -> None:
        """
        Runs final security checks after reading the entire file.

        It makes sure that the drone count, starting hub,
        and ending hub are all
        properly set. It also verifies that both
        the start and end hubs are actually 
        connected to at least one path so drones can travel.

        Raises:
            ParseError: If critical information is missing, or if the start and
                        end hubs have no connection paths.
        """
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

    def build_map_data(self) -> dict:
        """
        Gathers all the checked map information into one clean dictionary.

        This makes it easy to pass all the parsed data—like drones, zones,
        connections, start, and end points—to other parts of your program.

        Returns:
            dict: A dictionary containing all the organized map data.
        """
        return {
            "nb_drones": self.nb_drones,
            "zones": self.zones,
            "connections": self.connections,
            "start": self.start_zone,
            "end": self.end_zone
        }
