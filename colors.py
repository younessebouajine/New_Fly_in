from webcolors import name_to_hex
from rich import print


class Colorizer:
    """
    Handle terminal colors for zones and drones.

    Supports:
    - rainbow text
    - css named colors
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

            color = self.rainbow_colors[
                i % len(self.rainbow_colors)
            ]

            hex_color = name_to_hex(color)

            result += (
                f"[{hex_color}]"
                f"{char}"
                f"[/]"
            )

        return result

    def color(
        self,
        text: str,
        color: str | None
    ) -> str:
        """
        Color text using:
        - rainbow
        - css color names
        - hex colors
        """

        if color is None:
            return text

        # rainbow mode
        if color == "rainbow":
            return self.rainbow(text)

        # already hex
        if color.startswith("#"):
            return (
                f"[{color}]"
                f"{text}"
                f"[/]"
            )

        # named css color
        try:

            hex_color = name_to_hex(color)

            return (
                f"[{hex_color}]"
                f"{text}"
                f"[/]"
            )

        except Exception:
            return text

    def drone_and_zone(
        self,
        drone_id: int,
        zone_name: str,
        zone_color: str | None
    ) -> str:
        """
        Example:
        D1-start_hub

        - drone always cyan
        - zone uses its own color
        """

        drone_text = self.color(
            f"D{drone_id}",
            "cyan"
        )

        zone_text = self.color(
            zone_name,
            zone_color
        )

        return f"{drone_text}-{zone_text}"