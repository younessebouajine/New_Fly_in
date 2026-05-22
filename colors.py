from webcolors import name_to_hex


class Colorizer:
    """
    A class to add colors to text for terminal display
    using the rich library format.

    It supports turning text into a rainbow style,
    using standard CSS color names,
    or using custom Hex color codes.
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
        """Does nothing since this class does not need initial variables."""
        pass

    def rainbow(self, text: str) -> str:
        """
        Colors each letter of a string with a different rainbow color.

        Args:
            text (str): The string of text to color.

        Returns:
            str: The text wrapped in rich library color tags.
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
        Applies a specific color style to a string of text.

        It automatically detects if the color should be rainbow, a hex code, 
        or a standard CSS color name. If the color is missing or invalid, 
        it returns the plain text without changes.

        Args:
            text (str): The string of text to color.
            color (str | None): The color name, hex code, or 'rainbow'.

        Returns:
            str: The colored text string.
        """

        if (
            color is None
            or color.lower() == "none"
        ):
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
        Formats and colors a string showing a drone inside a specific zone.
        
        Example output: [cyan]D1[/]-[#FF0000]start_hub[/]

        Args:
            drone_id (int): The ID number of the drone (always colored cyan).
            zone_name (str): The name of the hub or zone.
            zone_color (str | None): The color code or name for the zone.

        Returns:
            str: A combined, colored text line showing 'D<id>-<zone_name>'.
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
