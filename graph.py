from models import Zone, Connection, MapData


class GraphBuilder:
    """
    Converts raw map dictionary data into structured Python object models.

    It processes raw data fields to generate Zone, Connection, and
    comprehensive MapData objects for the application to use.
    """

    def __init__(self) -> None:
        """Does nothing since this class does not need initial variables."""
        pass

    def build_graph(self, data: dict) -> MapData:
        """
        Transforms a raw data dictionary into a complete MapData object.

        It creates individual Zone objects, links them together into Connection
        objects, and packages everything nicely with the global drone settings.

        Args:
            data (dict): The raw parsed map data dictionary.

        Returns:
            MapData: An object containing all ready-to-use map
            and zone structures.
        """
        zones = {}
        for name, z in data["zones"].items():
            zone = Zone(
                name=z["name"],
                x=z["x"],
                y=z["y"],
                max_drones=z["max_drones"],
                zone_type=z["zone_type"],
                color=z["color"]
            )
            zones[name] = zone

        connections = []
        for c in data["connections"]:
            zoneA = zones[c["from"]]
            zoneB = zones[c["to"]]
            connection = Connection(
                zoneA=zoneA,
                zoneB=zoneB,
                max_link_capacity=c["max_link_capacity"]
            )
            connections.append(connection)

        map_data = MapData(
            nb_drones=data["nb_drones"],
            zones=zones,
            connections=connections,
            start=data["start"],
            end=data["end"]
        )
        return map_data
