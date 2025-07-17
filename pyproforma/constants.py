from typing import Literal

# Value formats supported by format_value() function
VALUE_FORMATS = [
    None,  # Returns original value
    'str',  # Converts to string
    'no_decimals',  # Rounds and adds commas, no decimals
    'two_decimals',  # Shows 2 decimal places
    'percent',  # Multiplies by 100 and shows as percentage with no decimals
    'percent_one_decimal',  # Multiplies by 100 and shows as percentage with 1 decimal
    'percent_two_decimals',  # Multiplies by 100 and shows as percentage with 2 decimals
]

# Type alias for valid value formats (based on VALUE_FORMATS constant)
# Note: Using explicit Literal since dynamic Literal is not supported at runtime
ValueFormat = Literal[None, 'str', 'no_decimals', 'two_decimals', 'percent', 'percent_one_decimal', 'percent_two_decimals']
