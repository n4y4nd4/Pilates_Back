"""
Tests for utility functions.
"""
from django.test import TestCase
from datetime import date

from cobranca_app.core.utilitarios import (
    calcular_data_vencimento,
    formatar_data_para_exibicao,
    normalizar_numero_telefone,
    obter_atributo_seguro
)


class UtilsTest(TestCase):
    """Tests for utility functions."""
    
    def test_calcular_data_vencimento_mensal(self):
        """Test due date calculation for monthly plan."""
        # Teste com data de início 06/11/2025 e plano mensal
        start_date = date(2025, 11, 6)
        due_date = calcular_data_vencimento(start_date, 1)
        # Deve retornar 06/12/2025 (mesmo dia do mês seguinte)
        expected = date(2025, 12, 6)
        self.assertEqual(due_date, expected)
    
    def test_calcular_data_vencimento_mensal_ano_seguinte(self):
        """Test due date calculation when adding months crosses year boundary."""
        # Teste com data de início em dezembro
        start_date = date(2025, 12, 6)
        due_date = calcular_data_vencimento(start_date, 1)
        # Deve retornar 06/01/2026 (mesmo dia do mês seguinte, ano seguinte)
        expected = date(2026, 1, 6)
        self.assertEqual(due_date, expected)
    
    def test_calcular_data_vencimento_trimestral(self):
        """Test due date calculation for quarterly plan (3 months)."""
        start_date = date(2025, 11, 6)
        due_date = calcular_data_vencimento(start_date, 3)
        # Deve retornar 06/02/2026 (3 meses depois)
        expected = date(2026, 2, 6)
        self.assertEqual(due_date, expected)
    
    def test_calcular_data_vencimento_dia_31(self):
        """Test due date calculation when day doesn't exist in target month."""
        # Teste com dia 31 em janeiro (que não existe em fevereiro)
        start_date = date(2025, 1, 31)
        due_date = calcular_data_vencimento(start_date, 1)
        # Deve retornar o último dia de fevereiro (28 ou 29)
        # 2025 não é bissexto, então deve ser 28/02/2025
        expected = date(2025, 2, 28)
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

