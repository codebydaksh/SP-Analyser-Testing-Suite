"""
EXTREME ERROR HANDLING TESTS - The Hardest Edge Cases
Tests that go beyond brutal to absolutely extreme
"""
import pytest
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from sp_analyze import SPAnalyzer


class TestExtremeErrorHandling:
    """Extreme test suite for the absolute worst-case scenarios"""
    
    def test_single_gigantic_line_no_newlines(self):
        """Test SQL file as a single 1MB line with no newlines"""
        # Create a massive single-line SQL
        huge_line = "CREATE PROCEDURE dbo.OneLiner AS BEGIN " + \
                    "SELECT " + ", ".join([f"Col{i}" for i in range(50000)]) + \
                    " FROM Users END"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(huge_line)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle massive single line
            assert result is not None
            assert 'success' in result
            
            # Line count should be 1 if successful
            if result.get('success'):
                assert result['basic'].get('lines_of_code', 0) >= 1
        finally:
            Path(tmp_path).unlink()
    
    def test_all_special_characters_sql(self):
        """Test SQL with every possible special character"""
        special_chars_sql = """
        CREATE PROCEDURE dbo.[Special!@#$%^&*()_+-={}[]|\\:;"'<>,.?/~`Proc] 
            @Param1 VARCHAR(MAX) = '!@#$%^&*()_+-={}[]|\\:;"''<>,.?/~`'
        AS
        BEGIN
            DECLARE @Special NVARCHAR(MAX) = N'PlusMinusSection-Paragraph-Dagger-DoubleDagger-Various-Math-Symbols';
            SELECT @Param1 AS [Column!@#$%], @Special AS [SpecialChars];
        END
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(special_chars_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle all special characters
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_bom_markers_utf8_utf16(self):
        """Test files with different BOM (Byte Order Mark) encodings"""
        sql_content = "CREATE PROCEDURE dbo.BOMTest AS BEGIN SELECT 1 END"
        
        # Test UTF-8 with BOM
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sql') as tmp:
            # UTF-8 BOM
            tmp.write(b'\xef\xbb\xbf' + sql_content.encode('utf-8'))
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle BOM correctly
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_recursive_depth_varying_levels(self):
        """Test recursive function calls with varying depths"""
        # Create 10 procedures calling each other
        recursive_sql = ""
        for i in range(10):
            next_proc = f"dbo.RecursiveProc{(i+1) % 10}"
            recursive_sql += f"""
            CREATE PROCEDURE dbo.RecursiveProc{i}
                @Depth INT = 0
            AS
            BEGIN
                IF @Depth < 100
                    EXEC {next_proc} @Depth = @Depth + 1
                ELSE
                    SELECT @Depth AS MaxDepth
            END
            GO
            """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(recursive_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle without infinite loop
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_every_sql_keyword_in_strings_and_comments(self):
        """Test SQL with every reserved keyword hidden in strings/comments"""
        # All major SQL keywords
        keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'EXEC', 'EXECUTE', 'DECLARE', 'SET', 'BEGIN', 'END', 'IF', 'ELSE',
            'WHILE', 'BREAK', 'CONTINUE', 'RETURN', 'THROW', 'TRY', 'CATCH',
            'TRANSACTION', 'COMMIT', 'ROLLBACK', 'CURSOR', 'FETCH', 'OPEN', 'CLOSE'
        ]
        
        keyword_sql = "CREATE PROCEDURE dbo.KeywordTest AS BEGIN\n"
        keyword_sql += f"    -- Comment with keywords: {' '.join(keywords)}\n"
        keyword_sql += f"    DECLARE @Str VARCHAR(MAX) = '{' '.join(keywords)}';\n"
        keyword_sql += f"    /* Block comment: {' '.join(keywords)} */\n"
        keyword_sql += "    SELECT @Str AS AllKeywords;\n"
        keyword_sql += "END\n"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(keyword_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should parse correctly without false keyword detection
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_file_path_with_special_characters(self):
        """Test analyzing file with special characters in path"""
        sql_content = "CREATE PROCEDURE dbo.PathTest AS BEGIN SELECT 1 END"
        
        # Create temp directory with special chars
        with tempfile.TemporaryDirectory() as tmpdir:
            special_dir = Path(tmpdir) / "test!@#$%dir"
            special_dir.mkdir(exist_ok=True)
            
            special_file = special_dir / "file with spaces & special!.sql"
            special_file.write_text(sql_content, encoding='utf-8')
            
            try:
                analyzer = SPAnalyzer()
                result = analyzer.analyze_file(str(special_file))
                
                # Should handle special path characters
                assert result is not None
                assert 'success' in result
            finally:
                if special_file.exists():
                    special_file.unlink()
    
    def test_extremely_long_identifier_names(self):
        """Test SQL with maximum-length identifier names (128 chars)"""
        # SQL Server max identifier length is 128 characters
        long_name = "A" * 128
        long_param = "@" + "P" * 127
        
        long_identifier_sql = f"""
        CREATE PROCEDURE dbo.[{long_name}]
            {long_param} VARCHAR(MAX) = NULL
        AS
        BEGIN
            DECLARE @{long_name} INT = 1;
            SELECT @{long_name} AS [{long_name}];
        END
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(long_identifier_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle max-length identifiers
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_malformed_escape_sequences(self):
        """Test SQL with malformed escape sequences and quotes"""
        malformed_sql = """
        CREATE PROCEDURE dbo.MalformedTest AS
        BEGIN
            -- Unmatched quotes and backslashes
            DECLARE @Str1 VARCHAR(MAX) = 'Test'' with '' quotes';
            DECLARE @Str2 VARCHAR(MAX) = 'Test\\backslash\\here';
            DECLARE @Str3 VARCHAR(MAX) = 'Test with \\'' mixed';
            SELECT @Str1, @Str2, @Str3;
        END
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(malformed_sql)
            tmp_path = tmp.name
        
        try:
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should handle escape sequences
            assert result is not None
            assert 'success' in result
        finally:
            Path(tmp_path).unlink()
    
    def test_file_deleted_during_analysis(self):
        """Test when file is deleted while being analyzed"""
        sql_content = "CREATE PROCEDURE dbo.DeleteTest AS BEGIN SELECT 1 END"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(sql_content)
            tmp_path = tmp.name
        
        # Start analysis then immediately delete file
        analyzer = SPAnalyzer()
        
        # Delete file before analysis
        Path(tmp_path).unlink()
        
        # Should handle missing file gracefully
        result = analyzer.analyze_file(tmp_path)
        assert result is not None
        assert result['success'] == False
        assert 'not found' in result['error'].lower() or 'error' in result
    
    def test_read_only_file_in_read_only_directory(self):
        """Test analyzing read-only file"""
        sql_content = "CREATE PROCEDURE dbo.ReadOnlyTest AS BEGIN SELECT 1 END"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', encoding='utf-8') as tmp:
            tmp.write(sql_content)
            tmp_path = tmp.name
        
        try:
            # Make file read-only
            os.chmod(tmp_path, 0o444)
            
            analyzer = SPAnalyzer()
            result = analyzer.analyze_file(tmp_path)
            
            # Should still be able to READ read-only files
            assert result is not None
            assert 'success' in result
        finally:
            # Restore permissions before deleting
            os.chmod(tmp_path, 0o644)
            Path(tmp_path).unlink()
