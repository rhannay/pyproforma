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
