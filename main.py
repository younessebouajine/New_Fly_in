from pathlib import Path

from parser import Parser
from graph import build_graph
from simulation import Simulation


def main() -> None:
    """
    Main entry point of the project.
    """

    # Map file path
    file_path = "file.txt"
    # Parse map file
    parser = Parser()

    parser.parse(file_path)

    data = parser.build_map_data()

    # Build graph objects
    map_data = build_graph(data)

    # Create simulation
    simulation = Simulation(map_data)

    # Run simulation
    simulation.run()


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(f"\nERROR: {error}\n")
