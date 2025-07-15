from pyproforma.models._utils import check_name
import pytest


@pytest.mark.parametrize(
    "name,expected",
    [
        ("valid_name", True),
        ("anotherValidName123", True),
        ("", False),
        ("name with spaces", False),
        ("name-with-dash", True),
        ("name_with_underscore", True),
        ("name.with.dot", False),
        ("name$", False),
        ("123name", True),
        ("_leading_underscore", True),
        ("trailing_underscore_", True),
        ("name!", False),
    ]
)
def test_check_name(name, expected):
    assert check_name(name) == expected
