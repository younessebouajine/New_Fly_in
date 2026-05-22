from parser import Parser
from graph import GraphBuilder
from simulation import Simulation


class Main:
    """
    The main application manager that coordinates the entire program.

    It controls the core workflow: reading the input text file, building
    the virtual map graph, and running the drone simulation engine.
    """

    def __init__(self, file_path: str = "file.txt") -> None:
        """
        Sets up the main application with the path to the map
        configuration file.

        Args:
            file_path (str): The system path to the map configuration
            text file.
        """
        self.file_path = file_path
        self.parser = Parser()

    def run(self) -> None:
        """
        Executes the step-by-step pipeline to run the application.

        It parses the raw file text, converts that text data into structured
        graph models, loads them into the simulation, and kicks off the run.
        """

        # Parse map file
        self.parser.parse(self.file_path)

        data = self.parser.build_map_data()

        # Build graph objects
        graph = GraphBuilder()
        map_data = graph.build_graph(data)

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
