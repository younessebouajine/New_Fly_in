from parser import Parser
from pathlib import Path


def main():
    file_path = "file.txt"
    parser = Parser()
    parser.parse(file_path)

    data = parser.build_map_data()

    print("NB DRONES:", data["nb_drones"])
    print("START:", data["start"])
    print("END:", data["end"])

    print("\nZONES:")
    for name, zone in data["zones"].items():
        print(name, zone)

    print("\nCONNECTIONS:")
    for conn in data["connections"]:
        print(conn)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)