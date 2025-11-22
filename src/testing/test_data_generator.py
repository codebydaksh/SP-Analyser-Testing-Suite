"""
Smart Test Data Generator for T-SQL Unit Tests

Generates realistic test data with:
- Boundary value analysis
- Edge cases (NULL, empty, max length)
- SQL injection test strings
- Valid and invalid data sets
"""
from typing import Dict, List, Any
import re
from datetime import datetime, timedelta
import random


class TestDataGenerator:
    """Generate comprehensive test data for T-SQL parameters."""
    
    # SQL injection test strings
    SQL_INJECTION_TESTS = [
        "'; DROP TABLE Users--",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM sys.tables--",
        "'; EXEC xp_cmdshell('dir')--"
    ]
    
    # Unicode edge cases
    UNICODE_TESTS = [
        "",  # Chinese
        "Tëst",  # Accented
        "Test",  # Emoji
        "תשובה"   # Hebrew
    ]
    
    def generate_test_values(self, param: Dict[str, str]) -> Dict[str, List[Any]]:
        """
        Generate comprehensive test data for a parameter.
        
        Returns:
            {
                'valid': [list of valid values],
                'invalid': [list of invalid values],
                'boundary': [list of boundary values],
                'edge_cases': [list of edge cases]
            }
        """
        param_type = param.get('type', 'VARCHAR').upper().strip()
        base_type = param_type.split('(')[0].strip()
        
        result = {
            'valid': [],
            'invalid': [],
            'boundary': [],
            'edge_cases': []
        }
        
        # Extract size/precision
        size_match = re.search(r'\((\d+)(?:,\s*(\d+))?\)', param_type)
        size = int(size_match.group(1)) if size_match else None
        precision = int(size_match.group(2)) if size_match and size_match.group(2) else None
        
        # Generate based on type
        if base_type in ('INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT'):
            result.update(self._generate_integer_data(base_type))
        elif base_type in ('NUMERIC', 'DECIMAL', 'FLOAT', 'REAL', 'MONEY', 'SMALLMONEY'):
            result.update(self._generate_numeric_data(base_type, size, precision))
        elif base_type in ('VARCHAR', 'CHAR', 'NVARCHAR', 'NCHAR', 'TEXT', 'NTEXT'):
            result.update(self._generate_string_data(base_type, size))
        elif base_type in ('DATE', 'TIME', 'DATETIME', 'DATETIME2', 'SMALLDATETIME'):
            result.update(self._generate_datetime_data(base_type))
        elif base_type == 'BIT':
            result.update(self._generate_bit_data())
        elif base_type == 'UNIQUEIDENTIFIER':
            result.update(self._generate_guid_data())
        
        # Add NULL for all types (important edge case)
        result['edge_cases'].append('NULL')
        
        return result
    
    def _generate_integer_data(self, int_type: str) -> Dict[str, List]:
        """Generate integer test data with boundaries."""
        ranges = {
            'TINYINT': (0, 255),
            'SMALLINT': (-32768, 32767),
            'INT': (-2147483648, 2147483647),
            'INTEGER': (-2147483648, 2147483647),
            'BIGINT': (-9223372036854775808, 9223372036854775807)
        }
        
        min_val, max_val = ranges.get(int_type, (-2147483648, 2147483647))
        
        return {
            'valid': [1, 100, 1000],
            'boundary': [min_val, min_val + 1, 0, max_val - 1, max_val],
            'invalid': [max_val + 1, min_val - 1] if int_type != 'BIGINT' else [],
            'edge_cases': [0, -1]
        }
    
    def _generate_numeric_data(self, num_type: str, size: int, precision: int) -> Dict[str, List]:
        """Generate numeric/decimal test data."""
        if precision:
            # DECIMAL(18,2) style
            max_val = 10 ** (size - precision) - 1
            return {
                'valid': [1.0, 100.50, 999.99],
                'boundary': [0.0, 0.01, max_val - 0.01, max_val],
                'invalid': [max_val + 1],
                'edge_cases': [0.0, -0.01]
            }
        else:
            return {
                'valid': [1.0, 100.5, 1000.99],
                'boundary': [0.0, 0.01, 99999.99],
                'invalid': [],
                'edge_cases': [0.0, -1.0]
            }
    
    def _generate_string_data(self, str_type: str, max_length: int) -> Dict[str, List]:
        """Generate string test data with edge cases."""
        max_len = max_length if max_length else 50
        
        valid = [
            "'test'",
            "'ValidString'",
            "'John Doe'",
            "'test@example.com'" if max_len >= 18 else "'test'"
        ]
        
        boundary = [
            "''",  # Empty string
            f"'{'A' * (max_len - 1)}'",  # Max - 1
            f"'{'A' * max_len}'"  # Exactly max length
        ]
        
        invalid = [
            f"'{'A' * (max_len + 1)}'"  # Exceeds max length
        ]
        
        edge_cases = [
            "'  '",  # Whitespace only
            "' leading'",  # Leading space
            "'trailing '",  # Trailing space
        ] + [f"'{s}'" for s in self.SQL_INJECTION_TESTS[:2]]  # First 2 injection tests
        
        # Add Unicode if NVARCHAR/NCHAR
        if str_type.startswith('N'):
            edge_cases.extend([f"'{u}'" for u in self.UNICODE_TESTS[:2]])
        
        return {
            'valid': valid,
            'boundary': boundary,
            'invalid': invalid,
            'edge_cases': edge_cases
        }
    
    def _generate_datetime_data(self, dt_type: str) -> Dict[str, List]:
        """Generate datetime test data."""
        today = datetime.now()
        
        valid = [
            "'2024-01-01'",
            f"'{today.strftime('%Y-%m-%d')}'",
            "'2025-12-31'"
        ]
        
        boundary = [
            "'1753-01-01'",  # SQL Server minimum for DATETIME
            "'9999-12-31'",  # SQL Server maximum
            f"'{today.strftime('%Y-%m-%d')}'"  # Today
        ]
        
        invalid = [
            "'1752-12-31'",  # Before SQL Server minimum
            "'2024-13-01'",  # Invalid month
            "'2024-02-31'"   # Invalid day
        ]
        
        edge_cases = [
            f"'{(today - timedelta(days=1)).strftime('%Y-%m-%d')}'",  # Yesterday
            f"'{(today + timedelta(days=1)).strftime('%Y-%m-%d')}'",  # Tomorrow
            "'1900-01-01'"  # Historical date
        ]
        
        return {
            'valid': valid,
            'boundary': boundary,
            'invalid': invalid,
            'edge_cases': edge_cases
        }
    
    def _generate_bit_data(self) -> Dict[str, List]:
        """Generate BIT (boolean) test data."""
        return {
            'valid': [0, 1],
            'boundary': [0, 1],
            'invalid': [2, -1],
            'edge_cases': [0, 1]
        }
    
    def _generate_guid_data(self) -> Dict[str, List]:
        """Generate UNIQUEIDENTIFIER test data."""
        return {
            'valid': [
                "'00000000-0000-0000-0000-000000000000'",
                "'12345678-1234-1234-1234-123456789012'",
                "'AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'"
            ],
            'boundary': ["'00000000-0000-0000-0000-000000000000'"],
            'invalid': [
                "'not-a-guid'",
                "'12345678-1234-1234-1234'",  # Too short
                "'ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ'"  # Invalid hex
            ],
            'edge_cases': ["'00000000-0000-0000-0000-000000000000'"]
        }
    
    def get_realistic_value(self, param: Dict[str, str]) -> str:
        """Get a single realistic value for a parameter (for simple positive tests)."""
        param_name = param.get('name', '@param').lower()
        param_type = param.get('type', 'VARCHAR').upper().strip()
        base_type = param_type.split('(')[0].strip()
        
        # Smart defaults based on parameter name
        if 'email' in param_name:
            return "'test@example.com'"
        elif 'name' in param_name or 'firstname' in param_name or 'lastname' in param_name:
            return "'John Doe'"
        elif 'id' in param_name and base_type in ('INT', 'INTEGER', 'BIGINT'):
            return "1"
        elif 'date' in param_name or 'time' in param_name:
            return "'2024-01-01'"
        elif 'amount' in param_name or 'price' in param_name or 'cost' in param_name:
            return "100.00"
        elif 'active' in param_name or 'enabled' in param_name or 'flag' in param_name:
            return "1"
        elif 'phone' in param_name:
            return "'+1234567890'"
        elif 'url' in param_name or 'website' in param_name:
            return "'https://example.com'"
        
        # Fallback to type defaults
        test_values = self.generate_test_values(param)
        if test_values['valid']:
            return str(test_values['valid'][0])
        
        # Ultimate fallback
        if base_type in ('INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT'):
            return "1"
        elif base_type in ('VARCHAR', 'CHAR', 'NVARCHAR', 'NCHAR'):
            return "'test'"
        elif base_type in ('DATE', 'DATETIME', 'DATETIME2'):
            return "'2024-01-01'"
        elif base_type == 'BIT':
            return "1"
        else:
            return "NULL"
