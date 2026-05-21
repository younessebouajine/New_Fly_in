# 1. Start at start_zone, cost = 0
# 2. Keep a priority queue → always pick the zone with LOWEST cost
# 3. For each neighbor:
#    - new_cost = current_cost + move_cost(neighbor)
#    - if new_cost < known_cost → update and add to queue
# 4. Skip blocked zones
# 5. Stop when you reach end_zone
# 6. Reconstruct path using "came_from" dict



# get_move_cost()     → returns 1 or 2 based on zone type
#                       (blocked should never reach here)

# find_path()         → core Dijkstra algorithm
#                       takes start and end zones
#                       returns list of zones [start → ... → end]
#                       returns None if no path found

# reconstruct_path()  → after Dijkstra finishes
#                       walks backwards through came_from
#                       builds the path list

# find_all_paths()    → calls find_path() for each drone
#                       handles distributing drones across paths
#                       returns list of paths






# {
#     "start": [junction],

#     "junction": [
#         start,
#         path_a,
#         path_b
#     ],

#     "path_a": [junction, goal],

#     "path_b": [junction, goal],

#     "goal": [path_a, path_b]
# }


import heapq
from typing import List, Optional
from models import Zone, MapData


class PathFinder:
    def __init__(self, map_data: MapData) -> None:
        self.map_data = map_data

    def get_move_cost(self, zone: Zone) -> float:
        """Return movement cost based on zone type"""

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
        Find shortest path from start to end using Dijkstra.
        Returns list of zones from start to end, or None if no path exists.
        """
        distances: dict[str, float] = {
            zone_name: float("inf")
            for zone_name in self.map_data.zones
        }
        distances[start.name] = 0
        came_from: dict[str, str] = {}
        priority_queue: list[tuple[float, str]] = [(0, start.name)]  # (cost, zone_name)
        visited: set[str] = set()

        while priority_queue:
            current_distance, current_name = heapq.heappop(priority_queue)

            if current_name in visited:
                continue
            visited.add(current_name)

            if current_name == end.name:
                return self.reconstruct_path(came_from, end)

            # current_zone = self.map_data.zones[current_name]

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

    # def find_all_paths(self) -> List[List[Zone]]:
    #     """
    #     Assign the shortest path to all drones.
    #     Returns a list of paths, one per drone.
    #     """

    #     start = self.map_data.start_zone
    #     end = self.map_data.end_zone

    #     path = self.find_path(start, end)

    #     if path is None:
    #         raise ValueError("No path exists from start to goal")

    #     return [path for _ in range(self.map_data.nb_drones)]

    def find_all_paths(self) -> List[List[Zone]]:
    
        start = self.map_data.start_zone
        end = self.map_data.end_zone

        penalties: dict[str, float] = {}
        paths = []

        for _ in range(self.map_data.nb_drones):

            path = self.find_path(start, end, penalties)

            if path is None:
                raise ValueError("No path exists from start to goal")

            paths.append(path)

            for zone in path[1:-1]:
                penalties[zone.name] = penalties.get(zone.name, 0) + 4

        return paths

