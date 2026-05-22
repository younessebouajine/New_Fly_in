from pathfinding import PathFinder
from models import MapData, Drone, Zone, Connection
from typing import List
from rich import print
from colors import Colorizer


class Simulation:
    """
    The engine that manages running and animating
    the drone movements turn by turn.

    It deploys the drone fleet, tracks travel schedules,
    applies traffic constraints
    like capacity bottlenecks or delays in restricted areas,
    and visually logs progress.
    """
    def __init__(self, map_data: MapData):
        """
        Sets up the orchestration variables and pre-calculates target
        paths for the fleet.

        Args:
            map_data (MapData): Structured application map setup configuration.
        """
        self.map_data = map_data
        self.pathfinder = PathFinder(map_data)

        self.drones: List[Drone] = []
        self.current_turn = 0

        self.colore = Colorizer()

        self.create_drones()
        self.assign_paths()

    def create_drones(self) -> None:
        """
        Generates individual drone data objects and houses them
        inside the initial hub.
        """
        start_zone = self.map_data.start_zone
        for i in range(self.map_data.nb_drones):
            drone = Drone(
                drone_id=i + 1,
                start_zone=start_zone
            )
            self.drones.append(drone)
            start_zone.drones.append(drone)

    def assign_paths(self) -> None:
        """
        Distributes pre-calculated distinct routing tracks evenly
        across the active fleet.
        """
        all_paths = self.pathfinder.find_all_paths()
        for drone in self.drones:
            drone.path = all_paths[self.drones.index(drone) % len(all_paths)]

    def run(self) -> None:
        """
        Starts the central operational loop,
        ticking step clocks forward until everyone lands.
        """
        print("\n=== SIMULATION START ===\n")
        while not self.all_drones_arrived():
            self.current_turn += 1
            print(f"\n==> TURN {self.current_turn} <==\n")
            self.move_drones()
            self.reset_connections()
        print(f"\nTOTAL TURNS: {self.current_turn}")
        print("\n=== SIMULATION FINISHED ===")

    def move_drones(self) -> None:
        """
        Executes single-turn tick logic calculations governing lane
        speeds and grid spacing.

        It checks traffic limits, processes delay timers inside restricted
        airspace zones,
        and prints terminal logs showing active vehicle placements.
        """
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
                        f"{self.colore.color(f'D{drone.drone_id}', 'cyan')}-"
                        f"{self.colore.color(next_zone.name, next_zone.color)}"
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
                    f"{self.colore.color(f'D{drone.drone_id}', 'cyan')}-"
                    f"{self.colore.color(old_zone.name, old_zone.color)}->"
                    f"{self.colore.color(next_zone.name, next_zone.color)}"
                )

            else:

                next_zone.drones.append(drone)

                drone.current_zone = next_zone

                drone.path_index += 1

                turn_movements.append(
                    f"{self.colore.color(f'D{drone.drone_id}', 'cyan')}-"
                    f"{self.colore.color(next_zone.name, next_zone.color)}"
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
        """
        Locates the shared bridge connection object
        connecting two layout points together.

        Args:
            zone_a (Zone): The current physical zone node.
            zone_b (Zone): The neighboring destination node.

        Returns:
            Connection | None: The connection structural data,
            or None if no link exists.
        """

        for connection in self.map_data.connections:

            if connection.connects(zone_a.name, zone_b.name):
                return connection

        return None

    def reset_connections(self) -> None:
        """
        Clears out transient bottleneck trackers to
        reset path capabilities for the next step.
        """

        for connection in self.map_data.connections:
            connection.current_transit = 0

    def all_drones_arrived(self) -> bool:
        """
        Checks if every machine inside the simulation tracker
        has safely hit its target.

        Returns:
            bool: True if the entire fleet has reached the finish line.
        """

        for drone in self.drones:

            if drone.current_zone != self.map_data.end_zone:
                return False

        return True
