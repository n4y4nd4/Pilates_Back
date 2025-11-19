"""
Tests for utility functions.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta

from cobranca_app.core.utils import (
    calculate_due_date,
    format_date_for_display,
    normalize_phone_number,
    get_safe_attribute
)


class UtilsTest(TestCase):
    """Tests for utility functions."""
    
    def test_calculate_due_date_future(self):
        """Test due date calculation for future date."""
        start_date = timezone.localdate()
        due_date = calculate_due_date(start_date, 1)
        expected = start_date + timedelta(days=30)
        self.assertEqual(due_date, expected)
    
    def test_calculate_due_date_past(self):
        """Test due date calculation when calculated date is in the past."""
        start_date = timezone.localdate() - timedelta(days=60)
        due_date = calculate_due_date(start_date, 1)
        # Should calculate from today, not from start_date
        today = timezone.localdate()
        expected = today + timedelta(days=30)
        self.assertEqual(due_date, expected)
    
    def test_format_date_for_display(self):
        """Test date formatting."""
        test_date = date(2025, 12, 25)
        formatted = format_date_for_display(test_date)
        self.assertEqual(formatted, "25/12/2025")
    
    def test_format_date_for_display_none(self):
        """Test date formatting with None."""
        formatted = format_date_for_display(None)
        self.assertEqual(formatted, "")
    
    def test_normalize_phone_number(self):
        """Test phone number normalization."""
        test_cases = [
            ("+55 (21) 9 8765-4321", "5521987654321"),
            ("5521999887766", "5521999887766"),
            ("(21) 98765-4321", "21987654321"),
            ("", ""),
            (None, ""),
        ]
        
        for input_phone, expected in test_cases:
            result = normalize_phone_number(input_phone)
            self.assertEqual(result, expected, f"Failed for input: {input_phone}")
    
    def test_get_safe_attribute(self):
        """Test safe attribute access."""
        class TestObj:
            def __init__(self):
                self.existing_attr = "value"
        
        obj = TestObj()
        self.assertEqual(get_safe_attribute(obj, "existing_attr"), "value")
        self.assertEqual(get_safe_attribute(obj, "non_existing", "default"), "default")
        self.assertIsNone(get_safe_attribute(obj, "non_existing"))

