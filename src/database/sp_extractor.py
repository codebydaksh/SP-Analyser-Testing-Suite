"""
Stored Procedure Extractor
Extracts SP definitions from SQL Server databases
"""
import pyodbc
from typing import List, Dict, Optional
import logging


class SPExtractor:
    """Extract stored procedure definitions from SQL Server"""
    
    def __init__(self, connection):
        """
        Initialize extractor with database connection.
        
        Args:
            connection: SQLServerConnection instance or pyodbc.Connection
        """
        # Handle both SQLServerConnection and raw pyodbc.Connection
        if hasattr(connection, 'get_connection'):
            self.connection = connection.get_connection()
        else:
            self.connection = connection
            
        self.logger = logging.getLogger('sp_analyzer.database')
    
    def list_procedures(self, schema: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get list of all stored procedures in database.
        
        Args:
            schema: Filter by schema name (e.g., 'dbo'). If None, returns all schemas.
            
        Returns:
            List of dicts with 'schema' and 'name' keys
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    SCHEMA_NAME(schema_id) AS schema_name,
                    name AS procedure_name
                FROM sys.procedures
                WHERE is_ms_shipped = 0
            """
            
            if schema:
                query += " AND SCHEMA_NAME(schema_id) = ?"
                cursor.execute(query, (schema,))
            else:
                cursor.execute(query)
            
            procedures = []
            for row in cursor.fetchall():
                procedures.append({
                    'schema': row.schema_name,
                    'name': row.procedure_name,
                    'full_name': f"{row.schema_name}.{row.procedure_name}"
                })
            
            cursor.close()
            self.logger.info(f"Found {len(procedures)} stored procedures")
            
            return procedures
            
        except pyodbc.Error as e:
            self.logger.error(f"Failed to list procedures: {str(e)}")
            raise
    
    def get_procedure_definition(self, proc_name: str) -> str:
        """
        Get the T-SQL definition of a stored procedure.
        
        Args:
            proc_name: Procedure name (can include schema, e.g., 'dbo.uspGetEmployees')
            
        Returns:
            T-SQL source code as string
            
        Raises:
            ValueError: If procedure not found
        """
        try:
            cursor = self.connection.cursor()
            
            # Use OBJECT_DEFINITION to get SP source
            query = """
                SELECT OBJECT_DEFINITION(OBJECT_ID(?)) AS definition
            """
            
            cursor.execute(query, (proc_name,))
            row = cursor.fetchone()
            cursor.close()
            
            if not row or not row.definition:
                raise ValueError(f"Procedure '{proc_name}' not found or has no definition")
            
            self.logger.info(f"Retrieved definition for {proc_name}")
            return row.definition
            
        except pyodbc.Error as e:
            self.logger.error(f"Failed to get procedure definition: {str(e)}")
            raise
    
    def extract_all(self, schema: Optional[str] = None) -> Dict[str, str]:
        """
        Extract all stored procedure definitions.
        
        Args:
            schema: Filter by schema name
            
        Returns:
            Dict mapping full procedure names to their definitions
        """
        procedures = self.list_procedures(schema)
        definitions = {}
        
        for proc in procedures:
            try:
                full_name = proc['full_name']
                definition = self.get_procedure_definition(full_name)
                definitions[full_name] = definition
            except Exception as e:
                self.logger.warning(f"Skipping {proc['full_name']}: {str(e)}")
                continue
        
        self.logger.info(f"Extracted {len(definitions)} procedure definitions")
        return definitions
    
    def extract_by_pattern(self, pattern: str) -> Dict[str, str]:
        """
        Extract procedures matching a name pattern.
        
        Args:
            pattern: SQL LIKE pattern (e.g., 'usp%', '%Order%')
            
        Returns:
            Dict mapping procedure names to definitions
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    SCHEMA_NAME(schema_id) AS schema_name,
                    name AS procedure_name
                FROM sys.procedures
                WHERE is_ms_shipped = 0
                  AND name LIKE ?
            """
            
            cursor.execute(query, (pattern,))
            
            definitions = {}
            for row in cursor.fetchall():
                full_name = f"{row.schema_name}.{row.procedure_name}"
                try:
                    definition = self.get_procedure_definition(full_name)
                    definitions[full_name] = definition
                except Exception as e:
                    self.logger.warning(f"Skipping {full_name}: {str(e)}")
            
            cursor.close()
            self.logger.info(f"Found {len(definitions)} procedures matching pattern '{pattern}'")
            
            return definitions
            
        except pyodbc.Error as e:
            self.logger.error(f"Failed to extract by pattern: {str(e)}")
            raise
