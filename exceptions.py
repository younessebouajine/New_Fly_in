class ParseError(Exception):
    """Raised when the text file has incorrect formatting or syntax errors."""
    pass


class ValidationError(Exception):
    """Raised when the file data is readable but breaks system logic rules."""
    pass
