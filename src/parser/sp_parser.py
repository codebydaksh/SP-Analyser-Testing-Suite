import sqlglot
from sqlglot import exp, parse_one

class SPParser:
    """
    A parser for T-SQL Stored Procedures using sqlglot.
    """
    def __init__(self):
        self.dialect = "tsql"

    def parse(self, sql_code: str):
        """
        Parses the given T-SQL code and returns the AST.
        
        Args:
            sql_code (str): The T-SQL code to parse.
            
        Returns:
            sqlglot.exp.Expression: The root of the AST.
            
        Raises:
            sqlglot.errors.ParseError: If the SQL is invalid.
        """
        try:
            # parse returns a list of expressions.
            # We return the list if multiple, or single expression if one.
            # This handles cases where T-SQL body is parsed as multiple statements.
            expressions = sqlglot.parse(sql_code, read=self.dialect)
            if not expressions:
                return None
            if len(expressions) == 1:
                return expressions[0]
            return expressions
        except Exception as e:
            raise ValueError(f"Failed to parse SQL: {e}")

    def validate(self, sql_code: str) -> bool:
        """
        Validates the syntax of the given T-SQL code.
        
        Args:
            sql_code (str): The T-SQL code to validate.
            
        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            self.parse(sql_code)
            return True
        except ValueError:
            return False
