import re
from typing import Optional

def format_price(price_str: str) -> Optional[str]:
    """
    Format a price string by removing non-numeric characters.

    Args:
        price_str (str): Raw price string.

    Returns:
        Optional[str]: Formatted price as a string or None if input is invalid.
    """
    try:
        if not price_str:
            return None
        formatted_price = re.sub(r"[^\d.]", "", price_str)
        return formatted_price
    except Exception as e:
        print(f"Error formatting price: {e}")
        return None

def validate_url(url: str) -> bool:
    """
    Validate a given URL string.

    Args:
        url (str): URL to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    regex = re.compile(
        r'^(https?:\/\/)?'  # http:// or https://
        r'(([\da-z.-]+)\.([a-z.]{2,6})|'  # domain...
        r'(([0-9]{1,3}\.){3}[0-9]{1,3}))'  # ...or IPv4
        r'(\:[0-9]{1,5})?'  # optional port
        r'(\/[-a-z\d%_.~+]*)*'  # path
        r'(\?[;&a-z\d%_.~+=-]*)?'  # query string
        r'(\#[-a-z\d_]*)?$', re.IGNORECASE)  # fragment locator
    return re.match(regex, url) is not None

def parse_integer(value: str) -> Optional[int]:
    """
    Parse a string into an integer, if possible.

    Args:
        value (str): Input string to parse.

    Returns:
        Optional[int]: Parsed integer or None if parsing fails.
    """
    try:
        return int(value)
    except ValueError:
        return None

def extract_year(text: str) -> Optional[int]:
    """
    Extract the year from a given text.

    Args:
        text (str): Text containing a year.

    Returns:
        Optional[int]: Extracted year as an integer or None if not found.
    """
    match = re.search(r"\b(19|20)\d{2}\b", text)
    return int(match.group()) if match else None