from models import Zone, Connection, MapData


def build_graph(data: dict) -> MapData:
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
