from typing import List


class Zone:
    """
    Represents a specific physical location or hub on the map.

    It holds information about its coordinate position, its operational rules,
    and keeps track of how many drones are currently sitting inside it.
    """
    def __init__(self, name: str, x: int, y: int, max_drones: int,
                 zone_type: str, color: str | None) -> None:
        """
        Sets up a zone with its name, location, capacities, and visual color.

        Args:
            name (str): The unique name of the zone.
            x (int): The X coordinate on the grid.
            y (int): The Y coordinate on the grid.
            max_drones (int): The maximum number of drones allowed
            here at once.
            zone_type (str): The category of the zone (e.g., normal,
            restricted).
            color (str | None): The display color name or hex code.
        """
        self.name = name
        self.x = x
        self.y = y
        self.max_drones = max_drones
        self.zone_type = zone_type
        self.color = color
        self.drones: List["Drone"] = []  # all drones currently inside the zone

    def is_full(self) -> bool:
        """Check if the zone has reached its maximum capacity"""
        return len(self.drones) >= self.max_drones


class Connection:
    """
    Represents a flight path link between two distinct zones.

    It regulates traffic flow by tracking how many drones are actively flying
    across this link at any given time.
    """
    def __init__(self, zoneA: Zone, zoneB: Zone,
                 max_link_capacity: int) -> None:
        """
        Creates a connection path between two zone objects.

        Args:
            zoneA (Zone): The first zone object.
            zoneB (Zone): The second zone object.
            max_link_capacity (int): Maximum number of drones
            that can fly here simultaneously.
        """
        self.zoneA = zoneA
        self.zoneB = zoneB
        self.max_link_capacity = max_link_capacity
        # how many drones are currently using this connection
        self.current_transit = 0

    def connects(self, zone1: str, zone2: str) -> bool:
        """Checks if this connection links two zones"""
        return (
            (self.zoneA.name == zone1 and self.zoneB.name == zone2)
            or
            (self.zoneA.name == zone2 and self.zoneB.name == zone1)
        )


class Drone:
    """
    Represents an individual autonomous drone tracking its own
    delivery mission.

    It remembers its current location, its remaining path steps, and whether
    it is currently moving or waiting out time limits.
    """
    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        """
        Initializes a drone with a unique ID and places it at its starting hub.

        Args:
            drone_id (int): The numerical identity tag for this drone.
            start_zone (Zone): The zone where the drone begins its journey.
        """
        self.drone_id = drone_id
        self.current_zone = start_zone
        self.path: List[Zone] = []
        self.in_transit = False  # Is drone currently moving
        self.turns_remaining = 0  # this for restricted zones
        self.path_index = 0


class MapData:
    """Represents the entire graph"""
    def __init__(self, nb_drones: int, zones: dict[str, Zone],
                 connections: List[Connection],
                 start: str, end: str):
        """
        Assembles all map pieces including global drone
        counts and specific hubs.

        Args:
            nb_drones (int): Total number of drones operating in the map.
            zones (dict[str, Zone]): A lookup dictionary of all
            available zones.
            connections (List[Connection]): A list of all available link paths.
            start (str): The name of the global starting hub.
            end (str): The name of the global target destination hub.
        """
        self.nb_drones = nb_drones
        self.zones = zones
        self.connections = connections
        self.start_zone = zones[start]
        self.end_zone = zones[end]
        self.neighbors: dict[str, List[Zone]] = self.build_neighbors()

    def build_neighbors(self) -> dict[str, List[Zone]]:
        """
        Scans all path connections to build a quick lookup map of
        adjacent neighbor zones.

        Returns:
            dict[str, List[Zone]]: A dictionary mapping each zone name to
            its neighboring Zone objects.
        """
        adj: dict[str, list[Zone]] = {name: [] for name in self.zones}
        for conn in self.connections:
            adj[conn.zoneA.name].append(conn.zoneB)
            adj[conn.zoneB.name].append(conn.zoneA)
        return adj
