from pathlib import Path

from parser import Parser
from graph import build_graph
from simulation import Simulation


class Main:
    """
    Main application class.
    """

    def __init__(self, file_path: str = "file.txt") -> None:
        self.file_path = file_path
        self.parser = Parser()

    def run(self) -> None:
        """
        Run the application.
        """

        # Parse map file
        self.parser.parse(self.file_path)

        data = self.parser.build_map_data()

        # Build graph objects
        map_data = build_graph(data)

        # Create simulation
        simulation = Simulation(map_data)

        # Run simulation
        simulation.run()


if __name__ == "__main__":
    try:
        app = Main()
        app.run()

    except (KeyboardInterrupt, FileNotFoundError, Exception) as error:
        print(f"\nERROR: {error}\n")