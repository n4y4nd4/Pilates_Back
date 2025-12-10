"""
Tests for utility functions.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta

from cobranca_app.core.utilitarios import (
    calcular_data_vencimento,
    formatar_data_para_exibicao,
    normalizar_numero_telefone,
    obter_atributo_seguro
)


class UtilsTest(TestCase):
    """Tests for utility functions."""
    
    def test_calcular_data_vencimento_future(self):
        """Test due date calculation for future date."""
        start_date = timezone.localdate()
        due_date = calcular_data_vencimento(start_date, 1)
        expected = start_date + timedelta(days=30)
        self.assertEqual(due_date, expected)
    
    def test_calcular_data_vencimento_past(self):
        """Test due date calculation when calculated date is in the past."""
        start_date = timezone.localdate() - timedelta(days=60)
        due_date = calcular_data_vencimento(start_date, 1)
        # Should calculate from today, not from start_date
        today = timezone.localdate()
        expected = today + timedelta(days=30)
        self.assertEqual(due_date, expected)
    
    def test_formatar_data_para_exibicao(self):
        """Test date formatting."""
        test_date = date(2025, 12, 25)
        formatted = formatar_data_para_exibicao(test_date)
        self.assertEqual(formatted, "25/12/2025")
    
    def test_formatar_data_para_exibicao_none(self):
        """Test date formatting with None."""
        formatted = formatar_data_para_exibicao(None)
        self.assertEqual(formatted, "")
    
    def test_normalizar_numero_telefone(self):
        """Test phone number normalization."""
        test_cases = [
            ("+55 (21) 9 8765-4321", "5521987654321"),
            ("5521999887766", "5521999887766"),
            ("(21) 98765-4321", "21987654321"),
            ("", ""),
            (None, ""),
        ]
        
        for input_phone, expected in test_cases:
            result = normalizar_numero_telefone(input_phone)
            self.assertEqual(result, expected, f"Failed for input: {input_phone}")
    
    def test_obter_atributo_seguro(self):
        """Test safe attribute access."""
        class TestObj:
            def __init__(self):
                self.existing_attr = "value"
        
        obj = TestObj()
        self.assertEqual(obter_atributo_seguro(obj, "existing_attr"), "value")
        self.assertEqual(obter_atributo_seguro(obj, "non_existing", "default"), "default")
        self.assertIsNone(obter_atributo_seguro(obj, "non_existing"))

