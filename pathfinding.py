import heapq
from typing import List, Optional
from models import Zone, MapData


class PathFinder:
    """
    Calculates smart flight paths for the drones across the map.

    It uses a modified Dijkstra algorithm that applies temporary cost penalties
    to shared areas, encouraging multiple drones to choose distinct,
    low-traffic 
    routes instead of all jamming into the same path.
    """
    def __init__(self, map_data: MapData) -> None:
        """Initializes the pathfinder with map and fleet configuration data."""
        self.map_data = map_data

    def get_move_cost(self, zone: Zone) -> float | int:
        """
        Determines the base difficulty or travel time cost of entering a zone.

        For example, priority zones have a lower cost to encourage traffic
        there,
        while restricted zones have a higher cost because they slow down
        drones.

        Args:
            zone (Zone): The zone to calculate the movement cost for.

        Returns:
            float | int: The numerical movement cost value.
        """
        if zone.zone_type == "priority":
            return 0.8
        if zone.zone_type == "normal":
            return 1
        if zone.zone_type == "restricted":
            return 2
        return 1

    def find_path(self, start: Zone, end: Zone,
                  penalties: dict[str, float]) -> Optional[List[Zone]]:
        """
        Finds the single cheapest path from a start zone to an end zone.

        It looks at both the base zone type costs and any added congestion
        penalties to safely steer drones away from heavily busy areas.

        Args:
            start (Zone): The starting location.
            end (Zone): The target destination.
            penalties (dict[str, float]): Current congestion penalties for
            each zone name.

        Returns:
            Optional[List[Zone]]: A list of sequential Zone objects, or None
            if blocked.
        """
        distances: dict[str, float] = {
            zone_name: float("inf")
            for zone_name in self.map_data.zones
        }
        distances[start.name] = 0
        came_from: dict[str, str] = {}
        priority_queue: list[tuple[float, str]] = [(0, start.name)]
        visited: set[str] = set()
        while priority_queue:
            current_distance, current_name = heapq.heappop(priority_queue)
            if current_name in visited:
                continue
            visited.add(current_name)
            if current_name == end.name:
                return self.reconstruct_path(came_from, end)
            for neighbor in self.map_data.neighbors[current_name]:
                if neighbor.zone_type == "blocked":
                    continue
                base_cost = self.get_move_cost(neighbor)
                penalty = penalties.get(neighbor.name, 0)
                move_cost = base_cost + penalty
                new_distance = current_distance + move_cost
                if new_distance < distances[neighbor.name]:
                    distances[neighbor.name] = new_distance
                    came_from[neighbor.name] = current_name
                    heapq.heappush(
                        priority_queue,
                        (new_distance, neighbor.name)
                    )
        return None

    def reconstruct_path(
        self,
        came_from: dict[str, str],
        end: Zone
    ) -> List[Zone]:
        """
        Traces back through the navigation history map to assemble
        the final route.

        Args:
            came_from (dict[str, str]): A tracking map of which zone
            led to which.
            end (Zone): The final destination zone.

        Returns:
            List[Zone]: The reconstructed path ordered from start to end
            destination.
        """
        path = []
        current_name = end.name
        while current_name in came_from:
            current_zone = self.map_data.zones[current_name]
            path.append(current_zone)
            current_name = came_from[current_name]
        start_zone = self.map_data.zones[current_name]
        path.append(start_zone)
        path.reverse()
        return path

    def find_all_paths(self) -> List[List[Zone]]:
        """
        Finds unique paths for multiple drones from the start to end zone,
        applying cost penalties to shared zones to encourage distinct routes.
        """
        start = self.map_data.start_zone
        end = self.map_data.end_zone
        penalties: dict[str, float] = {}
        paths = []

        for _ in range(self.map_data.nb_drones):
            path = self.find_path(start, end, penalties)
            if path in paths:
                continue
            if path is None:
                raise ValueError("No path exists from start to goal")
            paths.append(path)
            for zone in path[1:-1]:
                penalties[zone.name] = penalties.get(zone.name, 0) + 4
        if len(paths) == 1:
            return paths
        paths.sort(
            key=lambda path: sum([self.get_move_cost(zone) for zone in path])
            )
        return paths[0:2]
