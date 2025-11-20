from sqlglot import exp
from src.parser.sp_parser import SPParser

class DependencyResolver:
    """
    Analyzes a T-SQL AST to extract dependencies (tables, views, other SPs).
    """
    def __init__(self):
        pass

    def get_dependencies(self, ast) -> dict:
        """
        Extracts dependencies from the AST.
        
        Args:
            ast (sqlglot.exp.Expression or list): The AST to analyze.
            
        Returns:
            dict: A dictionary containing lists of dependencies by type.
                  e.g., {'tables': [], 'procedures': []}
        """
        dependencies = {
            'tables': set(),
            'procedures': set()
        }

        # Helper to traverse nodes
        def collect_deps(node):
            if isinstance(node, list):
                for item in node:
                    collect_deps(item)
                return

            if not isinstance(node, exp.Expression):
                return

            # Find all Table expressions
            for table in node.find_all(exp.Table):
                table_name = table.name
                # Handle schema/db qualification if present
                if table.db:
                    table_name = f"{table.db}.{table_name}"
                if table.catalog:
                    table_name = f"{table.catalog}.{table_name}"
                
                dependencies['tables'].add(table_name)

            for n in node.walk():
                if isinstance(n, exp.Command):
                    # Check if it's an EXEC command
                    # Based on exploration, node.this is 'EXEC' or 'EXECUTE'
                    # and the rest is in node.expression (as a Literal) or just part of the command
                    
                    command_keyword = n.this.upper() if n.this else ""
                    
                    if command_keyword in ('EXEC', 'EXECUTE'):
                        # The rest of the command is usually in the expression
                        # It might be a Literal string
                        cmd_content = ""
                        if n.expression:
                            if isinstance(n.expression, exp.Literal):
                                cmd_content = n.expression.this
                            else:
                                cmd_content = n.expression.sql()
                        
                        if cmd_content:
                            # cmd_content is like "dbo.AnotherProc @id = 1"
                            # We need to extract the procedure name
                            parts = cmd_content.split()
                            if parts:
                                proc_name = parts[0]
                                # Handle @return_status = ...
                                if proc_name.startswith('@') and len(parts) > 2 and parts[1] == '=':
                                    proc_name = parts[2]
                                
                                # Clean up
                                if proc_name.endswith(';'):
                                    proc_name = proc_name[:-1]
                                    
                                dependencies['procedures'].add(proc_name)

        collect_deps(ast)
        
        return {k: list(v) for k, v in dependencies.items()}
