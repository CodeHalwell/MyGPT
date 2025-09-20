"""
Tests for utility functions in routes module.
"""

import re

from routes import generate_random_color


class TestUtilityFunctions:
    """Test cases for utility functions in routes module."""

    def test_generate_random_color_format(self):
        """Test that generate_random_color returns valid hex color."""
        color = generate_random_color()

        # Should return a string
        assert isinstance(color, str)

        # Should be in hex format (#RRGGBB)
        assert len(color) == 7
        assert color.startswith("#")

        # Should match hex color pattern
        hex_pattern = r"^#[0-9a-fA-F]{6}$"
        assert re.match(hex_pattern, color) is not None

    def test_generate_random_color_uniqueness(self):
        """Test that generate_random_color produces different colors."""
        colors = set()

        # Generate multiple colors and check for variety
        for _ in range(20):
            color = generate_random_color()
            colors.add(color)

        # Should have generated some variety (at least a few different colors)
        # We use a conservative threshold since it's random
        assert len(colors) > 5

    def test_generate_random_color_valid_rgb_values(self):
        """Test that generated colors have valid RGB values."""
        for _ in range(10):
            color = generate_random_color()

            # Extract RGB values from hex
            hex_value = color[1:]  # Remove '#'
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)

            # RGB values should be in valid range (0-255)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255

    def test_generate_random_color_no_pure_colors(self):
        """Test that generated colors avoid pure black/white (based on implementation)."""
        for _ in range(10):
            color = generate_random_color()

            # Based on the implementation (saturation 50-90, lightness 35-65),
            # should not generate pure black (#000000) or pure white (#ffffff)
            assert color != "#000000"
            assert color != "#ffffff"

    def test_generate_random_color_consistent_format(self):
        """Test that color format is consistent across multiple calls."""
        colors = [generate_random_color() for _ in range(5)]

        for color in colors:
            # All should start with #
            assert color.startswith("#")
            # All should be 7 characters long
            assert len(color) == 7
            # All should contain only valid hex characters
            hex_chars = color[1:]
            assert all(c in "0123456789abcdefABCDEF" for c in hex_chars)
