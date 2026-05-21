from webcolors import name_to_hex
from rich import print


class Colorizer:
    """
    Handle terminal colors for zones and drones.
    Supports:
    - rainbow text
    - normal named colors
    - hex colors
    """

    rainbow_colors = [
        "red",
        "orange",
        "yellow",
        "green",
        "blue",
        "indigo",
        "violet"
    ]

    def __init__(self) -> None:
        pass

    def rainbow(self, text: str) -> str:
        """
        Return rainbow-colored text.
        """

        result = ""

        for i, char in enumerate(text):
            color = self.rainbow_colors[i % len(self.rainbow_colors)]
            hex_color = name_to_hex(color)
            result += f"[{hex_color}]{char}[/]"

        return result

    def color(self, text: str, color: str | None) -> str:
        """
        Color text using:
        - rainbow
        - css color name
        - hex
        """

        if color is None:
            return text

        if color == "rainbow":
            return self.rainbow(text)

        # if already hex
        if color.startswith("#"):
            return f"[{color}]{text}[/]"

        # css name → hex
        try:
            hex_color = name_to_hex(color)
            return f"[{hex_color}]{text}[/]"
        except Exception:
            return text