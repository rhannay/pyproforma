import pytest

from pyproforma.models._utils import validate_name


class TestValidateName:
    @pytest.mark.parametrize(
        "name",
        [
            "valid_name",
            "anotherValidName123",
            "name-with-dash",
            "name_with_underscore",
            "123name",
            "_leading_underscore",
            "trailing_underscore_",
        ],
    )
    def test_validate_name_valid_names(self, name):
        # Should not raise an exception for valid names
        validate_name(name)

    @pytest.mark.parametrize(
        "name",
        [
            "",
            "name with spaces",
            "name.with.dot",
            "name$",
            "name!",
        ],
    )
    def test_validate_name_invalid_names(self, name):
        # Should raise ValueError for invalid names
        with pytest.raises(
            ValueError, match="Name must only contain letters, numbers, underscores"
        ):
            validate_name(name)
