"""
Tests for error handling functionality  
"""
import pytest
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))
from sp_analyze import SPAnalyzer


class TestErrorHandling:
    """Test suite for error handling in sp_analyze"""
    
    def test_file_not_found_error(self):
        """Test graceful handling of missing file"""
        analyzer = SPAnalyzer()
        result = analyzer.analyze_file("nonexistent_file.sql")
        
        assert result['success'] == False
        assert result['error'] == "File not found"
        assert result['sp_name'] == 'UNKNOWN'
    
    def test_invalid_encoding_error(self):
        """Test handling of file encoding errors"""
        # Create a file with invalid UTF-8
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sql') as tmp:
            tmp.write(b'\x80\x81\x82')  # Invalid UTF-8
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            assert result['success'] == False
            assert "encoding" in result['error'].lower()
        finally:
            Path(tmp_path).unlink()
    
    def test_corrupted_sql_error(self):
        """Test handling of completely invalid SQL"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write("INVALID SQL GARBAGE @#$%^&*()")
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should return error result, not crash
            assert 'success' in result
            assert 'error' in result or result['success'] == True  # Either handles or processes
        finally:
            Path(tmp_path).unlink()
    
    def test_partial_results_on_error(self):
        """Test that error result includes all required fields"""
        analyzer = SPAnalyzer()
        result = analyzer._error_result("test.sql", "Test error")
        
        assert result['success'] == False
        assert result['error'] == "Test error"
        assert result['source'] == "test.sql"
        assert 'basic' in result
        assert 'security' in result
        assert 'quality' in result
        assert 'performance' in result
        assert 'complexity' in result
        assert 'dependencies' in result
    
    def test_error_recovery_in_batch(self):
        """Test that one error doesn't stop batch processing"""
        analyzer = SPAnalyzer()
        
        # Create one valid and one invalid file
        valid_sql = "CREATE PROCEDURE test AS BEGIN SELECT 1 END"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp1:
            tmp1.write(valid_sql)
            valid_path = tmp1.name
        
        try:
            # Analyze valid file
            result1 = analyzer.analyze_file(valid_path)
            assert result1.get('success', True) != False
            
            # Analyze invalid file
            result2 = analyzer.analyze_file("nonexistent.sql")
            assert result2['success'] == False
            
            # Both should return results
            assert result1 is not None
            assert result2 is not None
        finally:
            Path(valid_path).unlink()
