import heapq
from typing import List, Optional
from models import Zone, MapData


class PathFinder:
    """
    A multi-agent pathfinding coordinator that uses a penalized Dijkstra
    algorithm to calculate distinct,
    low-cost routing paths for a fleet of drones.
    """
    def __init__(self, map_data: MapData) -> None:
        """Initializes the pathfinder with map and fleet configuration data."""
        self.map_data = map_data

    def get_move_cost(self, zone: Zone) -> float:
        """Return movement cost based on zone type"""
        if zone.zone_type == "priority":
            return 0.8
        if zone.zone_type == "normal":
            return 1
        if zone.zone_type == "restricted":
            return 2

    def find_path(self, start: Zone, end: Zone,
                  penalties: dict[str, float]) -> Optional[List[Zone]]:
        """
        Find shortest path from start to end using Dijkstra.
        Returns list of zones from start to end, or None if no path exists.
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
        """Rebuild path from came_from dict"""
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
