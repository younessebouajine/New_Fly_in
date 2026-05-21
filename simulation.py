from pathfinding import PathFinder
from models import MapData, Drone, Zone, Connection
from typing import List
from rich import print
from colors import Colorizer


class Simulation:
    def __init__(self, map_data: MapData):
        self.map_data = map_data
        self.pathfinder = PathFinder(map_data)

        self.drones: List[Drone] = []
        self.current_turn = 0

        self.colorizer = Colorizer()

        self.create_drones()
        self.assign_paths()

    def create_drones(self) -> None:
        start_zone = self.map_data.start_zone
        for i in range(self.map_data.nb_drones):
            drone = Drone(
                drone_id=i + 1,
                start_zone=start_zone
            )
            self.drones.append(drone)
            start_zone.drones.append(drone)

    def assign_paths(self) -> None:
        all_paths = self.pathfinder.find_all_paths()
        for drone in self.drones:
            drone.path = all_paths[self.drones.index(drone) % len(all_paths)]

    def run(self) -> None:
        print("\n=== SIMULATION START ===\n")
        while not self.all_drones_arrived():
            self.current_turn += 1
            print(f"\n==> TURN {self.current_turn} <==\n")
            self.move_drones()
            self.reset_connections()
        print(f"\nTOTAL TURNS: {self.current_turn}")
        print("\n=== SIMULATION FINISHED ===")

    def move_drones(self) -> None:
        turn_movements = []
        reserved_zones = set()
        for drone in self.drones:
            # already arrived
            if drone.current_zone == self.map_data.end_zone:
                continue
            # safety
            if drone.path_index >= len(drone.path) - 1:
                continue
            next_zone = drone.path[drone.path_index + 1]
            # drone still flying to restricted zone
            if drone.turns_remaining > 0:
                drone.turns_remaining -= 1
                if drone.turns_remaining == 0:
                    next_zone.drones.append(drone)
                    drone.current_zone = next_zone
                    drone.path_index += 1
                    turn_movements.append(
                        f"{self.colorizer.color(f'D{drone.drone_id}', 'cyan')}-"
                        f"{self.colorizer.color(next_zone.name, next_zone.color)}"
                    )
                continue
            # blocked zone
            if next_zone.zone_type == "blocked":
                continue
            # reservation fix
            if (
                next_zone.name in reserved_zones
                and next_zone != self.map_data.end_zone
            ):
                continue
            # capacity
            if (
                next_zone != self.map_data.end_zone
                and next_zone.is_full()
            ):
                continue

            connection = self.give_us_connection(
                drone.current_zone,
                next_zone
            )

            if connection is None:
                continue

            # connection capacity
            if connection.current_transit >= connection.max_link_capacity:
                continue

            old_zone = drone.current_zone

            old_zone.drones.remove(drone)

            connection.current_transit += 1

            # restricted zone
            if next_zone.zone_type == "restricted":

                drone.turns_remaining = 1

                turn_movements.append(
                    f"{self.colorizer.color(f'D{drone.drone_id}', 'cyan')}-"
                    f"{self.colorizer.color(old_zone.name, old_zone.color)}->"
                    f"{self.colorizer.color(next_zone.name, next_zone.color)}"
                )

            else:

                next_zone.drones.append(drone)

                drone.current_zone = next_zone

                drone.path_index += 1

                turn_movements.append(
                    f"{self.colorizer.color(f'D{drone.drone_id}', 'cyan')}-"
                    f"{self.colorizer.color(next_zone.name, next_zone.color)}"
                )

                if next_zone != self.map_data.end_zone:
                    reserved_zones.add(next_zone.name)

        if turn_movements:
            print(" ".join(turn_movements))

    def give_us_connection(
        self,
        zone_a: Zone,
        zone_b: Zone
    ) -> Connection | None:

        for connection in self.map_data.connections:

            if connection.connects(zone_a.name, zone_b.name):
                return connection

        return None

    def reset_connections(self) -> None:

        for connection in self.map_data.connections:
            connection.current_transit = 0

    def all_drones_arrived(self) -> bool:

        for drone in self.drones:

            if drone.current_zone != self.map_data.end_zone:
                return False

        return True
