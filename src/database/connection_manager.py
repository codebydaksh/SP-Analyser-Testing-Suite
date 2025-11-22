"""
SQL Server Connection Manager
Handles database connections with proper error handling and cleanup
"""
import pyodbc
from typing import Optional
import logging


class SQLServerConnection:
    """Manage SQL Server database connections"""
    
    def __init__(self, server: str, database: str, username: Optional[str] = None, 
                 password: Optional[str] = None, trusted: bool = True, timeout: int = 30):
        """
        Initialize connection parameters.
        
        Args:
            server: SQL Server instance name (e.g., 'localhost', '192.168.1.100\\SQLEXPRESS')
            database: Database name
            username: SQL Server username (required if trusted=False)
            password: SQL Server password (required if trusted=False)
            trusted: Use Windows Authentication if True, SQL Authentication if False
            timeout: Connection timeout in seconds
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.trusted = trusted
        self.timeout = timeout
        self.connection = None
        self.logger = logging.getLogger('sp_analyzer.database')
    
    def connect(self) -> pyodbc.Connection:
        """
        Establish connection to SQL Server.
        
        Returns:
            pyodbc.Connection object
            
        Raises:
            pyodbc.Error: If connection fails
        """
        try:
            conn_str = self._build_connection_string()
            self.logger.info(f"Connecting to {self.server}/{self.database}...")
            
            self.connection = pyodbc.connect(conn_str, timeout=self.timeout)
            self.logger.info("Connection established successfully")
            
            return self.connection
            
        except pyodbc.Error as e:
            self.logger.error(f"Connection failed: {str(e)}")
            raise
    
    def _build_connection_string(self) -> str:
        """Build pyodbc connection string based on auth method"""
        driver = '{ODBC Driver 17 for SQL Server}'  # Try latest first
        
        if self.trusted:
            # Windows Authentication
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"Trusted_Connection=yes;"
            )
        else:
            # SQL Server Authentication
            if not self.username or not self.password:
                raise ValueError("Username and password required for SQL Server authentication")
            
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
        
        return conn_str
    
    def test_connection(self) -> bool:
        """
        Test if connection is successful.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("Connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.close()
        return False  # Don't suppress exceptions
    
    def get_connection(self) -> pyodbc.Connection:
        """
        Get the active connection object.
        
        Returns:
            pyodbc.Connection
            
        Raises:
            RuntimeError: If not connected
        """
        if not self.connection:
            raise RuntimeError("Not connected. Call connect() first or use context manager.")
        return self.connection
