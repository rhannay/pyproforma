"""Tests for color utilities in colors.py."""

import pytest

from pyproforma.table.colors import (
    CSS_COLORS,
    _find_similar_colors,
    color_to_hex,
    color_to_rgb,
    is_valid_color,
)


class TestIsValidColor:
    """Tests for is_valid_color function."""

    def test_valid_css_color_name(self):
        """Test that valid CSS color names are recognized."""
        assert is_valid_color('red')
        assert is_valid_color('blue')
        assert is_valid_color('lightgray')
        assert is_valid_color('darkblue')

    def test_valid_css_color_name_case_insensitive(self):
        """Test that color names are case insensitive."""
        assert is_valid_color('RED')
        assert is_valid_color('Blue')
        assert is_valid_color('LightGray')

    def test_valid_css_color_name_with_whitespace(self):
        """Test that whitespace is stripped."""
        assert is_valid_color('  red  ')
        assert is_valid_color('\tblue\n')

    def test_valid_hex_with_hash(self):
        """Test that hex codes with # are valid."""
        assert is_valid_color('#FF0000')
        assert is_valid_color('#00FF00')
        assert is_valid_color('#0000FF')

    def test_valid_hex_without_hash(self):
        """Test that hex codes without # are valid."""
        assert is_valid_color('FF0000')
        assert is_valid_color('00FF00')
        assert is_valid_color('0000FF')

    def test_valid_hex_lowercase(self):
        """Test that hex codes can be lowercase."""
        assert is_valid_color('#ff0000')
        assert is_valid_color('ff0000')

    def test_invalid_color_name(self):
        """Test that invalid color names return False."""
        assert not is_valid_color('notacolor')
        assert not is_valid_color('lightblu')  # Typo

    def test_invalid_hex_too_short(self):
        """Test that short hex codes are invalid."""
        assert not is_valid_color('#FFF')
        assert not is_valid_color('FFF')

    def test_invalid_hex_too_long(self):
        """Test that long hex codes are invalid."""
        assert not is_valid_color('#FF00000')
        assert not is_valid_color('FF00000')

    def test_invalid_hex_non_hex_chars(self):
        """Test that non-hex characters are invalid."""
        assert not is_valid_color('#GGGGGG')
        assert not is_valid_color('ZZZZZZ')

    def test_empty_string(self):
        """Test that empty string is invalid."""
        assert not is_valid_color('')
        assert not is_valid_color('   ')


class TestFindSimilarColors:
    """Tests for _find_similar_colors helper function."""

    def test_find_similar_typo(self):
        """Test finding similar colors for common typos."""
        suggestions = _find_similar_colors('lightblu')
        assert 'lightblue' in suggestions

    def test_find_similar_partial_match(self):
        """Test finding colors that contain the input."""
        suggestions = _find_similar_colors('blue')
        # Should find colors containing 'blue'
        assert any('blue' in s for s in suggestions)

    def test_find_similar_start_match_priority(self):
        """Test that colors starting with input are prioritized."""
        suggestions = _find_similar_colors('dark')
        # First suggestion should start with 'dark'
        if suggestions:
            assert suggestions[0].startswith('dark')

    def test_max_suggestions(self):
        """Test that max_suggestions parameter works."""
        suggestions = _find_similar_colors('blue', max_suggestions=2)
        assert len(suggestions) <= 2

    def test_no_similar_colors(self):
        """Test when no similar colors exist."""
        suggestions = _find_similar_colors('xyz123')
        assert len(suggestions) == 0


class TestColorToHex:
    """Tests for color_to_hex function."""

    def test_css_color_name_to_hex(self):
        """Test converting CSS color names to hex."""
        assert color_to_hex('red') == '#FF0000'
        assert color_to_hex('blue') == '#0000FF'
        assert color_to_hex('green') == '#008000'

    def test_css_color_name_case_insensitive(self):
        """Test that color names are case insensitive."""
        assert color_to_hex('RED') == '#FF0000'
        assert color_to_hex('Blue') == '#0000FF'

    def test_css_color_name_with_whitespace(self):
        """Test that whitespace is stripped."""
        assert color_to_hex('  red  ') == '#FF0000'

    def test_hex_with_hash(self):
        """Test that hex codes with # are normalized."""
        assert color_to_hex('#ff0000') == '#FF0000'
        assert color_to_hex('#00FF00') == '#00FF00'

    def test_hex_without_hash(self):
        """Test that hex codes without # get # added."""
        assert color_to_hex('FF0000') == '#FF0000'
        assert color_to_hex('00ff00') == '#00FF00'

    def test_invalid_color_raises_error(self):
        """Test that invalid colors raise ValueError."""
        with pytest.raises(ValueError, match="Invalid color"):
            color_to_hex('notacolor')

    def test_invalid_color_with_suggestions(self):
        """Test that invalid colors show suggestions."""
        with pytest.raises(ValueError, match="Did you mean"):
            color_to_hex('lightblu')

    def test_invalid_hex_raises_error(self):
        """Test that invalid hex codes raise ValueError."""
        with pytest.raises(ValueError, match="Invalid color"):
            color_to_hex('GGGGGG')

    def test_empty_color_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Color cannot be empty"):
            color_to_hex('')

    def test_all_css_colors_valid(self):
        """Test that all CSS_COLORS can be converted."""
        for color_name in CSS_COLORS.keys():
            result = color_to_hex(color_name)
            assert result.startswith('#')
            assert len(result) == 7


class TestColorToRgb:
    """Tests for color_to_rgb function."""

    def test_css_color_name_to_rgb(self):
        """Test converting CSS color names to RGB."""
        assert color_to_rgb('red') == (255, 0, 0)
        assert color_to_rgb('blue') == (0, 0, 255)
        assert color_to_rgb('green') == (0, 128, 0)

    def test_hex_with_hash_to_rgb(self):
        """Test converting hex codes with # to RGB."""
        assert color_to_rgb('#FF0000') == (255, 0, 0)
        assert color_to_rgb('#00FF00') == (0, 255, 0)
        assert color_to_rgb('#0000FF') == (0, 0, 255)

    def test_hex_without_hash_to_rgb(self):
        """Test converting hex codes without # to RGB."""
        assert color_to_rgb('FF0000') == (255, 0, 0)
        assert color_to_rgb('00FF00') == (0, 255, 0)

    def test_hex_lowercase_to_rgb(self):
        """Test converting lowercase hex codes."""
        assert color_to_rgb('#ff0000') == (255, 0, 0)
        assert color_to_rgb('00ff00') == (0, 255, 0)

    def test_gray_colors_to_rgb(self):
        """Test converting gray colors."""
        assert color_to_rgb('gray') == (128, 128, 128)
        assert color_to_rgb('lightgray') == (211, 211, 211)
        assert color_to_rgb('darkgray') == (169, 169, 169)

    def test_white_and_black_to_rgb(self):
        """Test converting white and black."""
        assert color_to_rgb('white') == (255, 255, 255)
        assert color_to_rgb('black') == (0, 0, 0)

    def test_invalid_color_raises_error(self):
        """Test that invalid colors raise ValueError."""
        with pytest.raises(ValueError):
            color_to_rgb('notacolor')

    def test_all_css_colors_to_rgb(self):
        """Test that all CSS_COLORS can be converted to RGB."""
        for color_name in CSS_COLORS.keys():
            r, g, b = color_to_rgb(color_name)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


class TestCellColorValidation:
    """Tests for Cell class color validation."""

    def test_valid_background_color(self):
        """Test that valid background colors work."""
        from pyproforma.table import Cell
        
        cell = Cell(value="Test", background_color="red")
        assert cell.background_color == "red"
        
        cell = Cell(value="Test", background_color="#FF0000")
        assert cell.background_color == "#FF0000"

    def test_valid_font_color(self):
        """Test that valid font colors work."""
        from pyproforma.table import Cell
        
        cell = Cell(value="Test", font_color="blue")
        assert cell.font_color == "blue"
        
        cell = Cell(value="Test", font_color="00FF00")
        assert cell.font_color == "00FF00"

    def test_invalid_background_color_raises_error(self):
        """Test that invalid background color raises ValueError."""
        from pyproforma.table import Cell
        
        with pytest.raises(ValueError, match="Invalid color"):
            Cell(value="Test", background_color="notacolor")

    def test_invalid_font_color_raises_error(self):
        """Test that invalid font color raises ValueError."""
        from pyproforma.table import Cell
        
        with pytest.raises(ValueError, match="Invalid color"):
            Cell(value="Test", font_color="notacolor")

    def test_typo_in_color_shows_suggestions(self):
        """Test that color typos show helpful suggestions."""
        from pyproforma.table import Cell
        
        with pytest.raises(ValueError, match="Did you mean"):
            Cell(value="Test", background_color="lightblu")

    def test_none_colors_are_valid(self):
        """Test that None is valid for colors."""
        from pyproforma.table import Cell
        
        cell = Cell(value="Test", background_color=None, font_color=None)
        assert cell.background_color is None
        assert cell.font_color is None


class TestColorRendering:
    """Tests for color rendering in different formats."""

    def test_html_rendering_with_colors(self):
        """Test that HTML renderer uses color_to_hex."""
        from pyproforma.table import Cell, Table
        
        cell = Cell(value="Test", background_color="red", font_color="blue")
        table = Table(cells=[[cell]])
        
        html = table.to_html()
        # Should have hex colors in the HTML
        assert '#FF0000' in html  # red background
        assert '#0000FF' in html  # blue font

    def test_df_css_with_colors(self):
        """Test that df_css property uses color_to_hex."""
        from pyproforma.table import Cell
        
        cell = Cell(value="Test", background_color="lightgray", font_color="darkblue")
        css = cell.df_css
        
        # Should have hex colors in CSS
        assert '#D3D3D3' in css  # lightgray
        assert '#00008B' in css  # darkblue

    def test_excel_export_with_colors(self):
        """Test that Excel export handles colors correctly."""
        from pyproforma.table import Cell, Table
        import tempfile
        import os
        
        cell = Cell(value="Test", background_color="red", font_color="blue")
        table = Table(cells=[[cell]])
        
        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            table.to_excel(tmp_path)
            # Just verify it doesn't raise an error
            assert os.path.exists(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
