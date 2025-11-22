"""
BRUTAL ERROR HANDLING TESTS - Advanced Edge Cases
Tests the most difficult error scenarios
"""
import pytest
import sys
from pathlib import Path
import tempfile
import threading
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from sp_analyze import SPAnalyzer


class TestBrutalErrorHandling:
    """Brutal test suite for extreme error conditions"""
    
    def test_massive_file_memory_stress(self):
        """Test handling of extremely large SQL file (10MB+)"""
        # Generate a massive valid SP to test memory handling
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            # Write procedure header
            tmp.write("CREATE PROCEDURE dbo.MassiveSP AS BEGIN\n")
            
            # Generate 100,000 lines of SQL
            for i in range(100000):
                tmp.write(f"    SELECT {i} AS Col{i};\n")
            
            tmp.write("END\n")
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should either succeed or fail gracefully (not crash)
            assert 'success' in result
            assert result is not None
            
            # If it succeeded, verify it handled the large file
            if result.get('success'):
                assert result['basic']['lines_of_code'] > 100000
        finally:
            Path(tmp_path).unlink()
    
    def test_deeply_nested_control_flow_stack_overflow(self):
        """Test deeply nested IF statements that could cause stack overflow"""
        # Create SQL with 50 levels of nesting
        nesting_depth = 50
        nested_sql = "CREATE PROCEDURE dbo.DeepNest AS BEGIN\n"
        
        for i in range(nesting_depth):
            nested_sql += "    " * i + f"IF @var{i} = 1 BEGIN\n"
        
        nested_sql += "    " * nesting_depth + "SELECT 'MAX DEPTH';\n"
        
        for i in range(nesting_depth - 1, -1, -1):
            nested_sql += "    " * i + "END\n"
        
        nested_sql += "END\n"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(nested_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle deep nesting without stack overflow
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_special_unicode_characters_edge_cases(self):
        """Test SQL with special Unicode characters that could break parsing"""
        problematic_sql = """
        CREATE PROCEDURE dbo.UnicodeSP 
            @Name NVARCHAR(100) = N'TestUser'
        AS
        BEGIN
            -- Comment with problematic chars: trademark-reg-copyright-symbol-infinity-section-paragraph
            DECLARE @Emoji NVARCHAR(MAX) = N'User: [USER] Status: [OK] Error: [ERROR] Warning: [WARN]';
            SELECT @Name AS , @Emoji AS ;
            -- Right-to-left text: مرحبا العالم
            -- Zero-width chars: ​‌‍
        END
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(problematic_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle unicode without breaking
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_concurrent_file_access_race_condition(self):
        """Test race condition when multiple threads try to analyze same file"""
        valid_sql = "CREATE PROCEDURE dbo.ConcurrentTest AS BEGIN SELECT 1 END"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(valid_sql)
            tmp_path = tmp.name
        
        results = []
        errors = []
        
        def analyze_concurrent():
            try:
                analyzer = SPAnalyzer()
                result = analyzer.analyze_file(tmp_path)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        try:
            # Launch 10 concurrent analyses
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=analyze_concurrent)
                threads.append(thread)
                thread.start()
            
            # Wait for all to complete
            for thread in threads:
                thread.join(timeout=5)
            
            # All should complete without crashes
            assert len(results) + len(errors) == 10
            
            # At least some should succeed
            successful = [r for r in results if r.get('success', False) != False]
            assert len(successful) > 0
        finally:
            Path(tmp_path).unlink()
    
    def test_null_bytes_in_file(self):
        """Test handling of null bytes in SQL file (binary corruption)"""
        # Create file with embedded null bytes
        corrupted_sql = b"CREATE PROCEDURE dbo.CorruptSP AS BEGIN\x00\x00\x00 SELECT 1 END"
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sql') as tmp:
            tmp.write(corrupted_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle null bytes gracefully
            assert result is not None
            assert 'success' in result
            # Will likely fail, but shouldn't crash
        finally:
            Path(tmp_path).unlink()
    
    def test_mixed_line_endings_chaos(self):
        """Test file with mixed line endings (LF, CRLF, CR) and no final newline"""
        # Mix of different line endings
        chaotic_sql = "CREATE PROCEDURE dbo.ChaosProc AS BEGIN\r\nSELECT 1\nSELECT 2\r\nSELECT 3\rEND"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8', newline='') as tmp:
            tmp.write(chaotic_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle mixed line endings
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_circular_dependency_detection(self):
        """Test SP with circular procedure calls (infinite loop potential)"""
        circular_sql = """
        CREATE PROCEDURE dbo.ProcA AS 
        BEGIN
            EXEC dbo.ProcB
        END
        
        CREATE PROCEDURE dbo.ProcB AS
        BEGIN
            EXEC dbo.ProcC
        END
        
        CREATE PROCEDURE dbo.ProcC AS
        BEGIN
            EXEC dbo.ProcA  -- Circular reference back to ProcA
        END
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(circular_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle without infinite loop
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_sql_injection_in_comments(self):
        """Test SQL with injection patterns hidden in comments"""
        injection_sql = """
        CREATE PROCEDURE dbo.InjectionTest 
            @UserId INT
        AS
        BEGIN
            -- '; DROP TABLE Users; --
            /* EXEC xp_cmdshell 'dir' */
            /** <script>alert('xss')</script> **/
            SELECT * FROM Users WHERE UserId = @UserId
            -- Normal execution
        END
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(injection_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should parse correctly and not trigger false positives
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_empty_file_edge_case(self):
        """Test completely empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            # Write nothing
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle empty file gracefully
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_only_whitespace_file(self):
        """Test file with only whitespace and newlines"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write("   \n\n\t\t\t\n   \r\n   ")
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle whitespace-only file
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
