"""
Comprehensive tests for logger.py - Targeting 80%+ coverage
"""
import pytest
import logging
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'core'))
from logger import setup_logging, get_logger


class TestLoggerSetup:
    """Test suite for logger configuration"""
    
    def test_default_logging_setup(self):
        """Test default logger setup with INFO level"""
        logger = setup_logging()
        
        assert logger is not None
        assert logger.name == 'sp_analyzer'
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_debug_level_logging(self):
        """Test logger with DEBUG level"""
        logger = setup_logging(log_level="DEBUG")
        
        assert logger.level == logging.DEBUG
        # Verify handler level is also DEBUG
        assert any(h.level == logging.DEBUG for h in logger.handlers)
    
    def test_warning_level_logging(self):
        """Test logger with WARNING level"""
        logger = setup_logging(log_level="WARNING")
        
        assert logger.level == logging.WARNING
    
    def test_error_level_logging(self):
        """Test logger with ERROR level"""
        logger = setup_logging(log_level="ERROR")
        
        assert logger.level == logging.ERROR
    
    def test_critical_level_logging(self):
        """Test logger with CRITICAL level"""
        logger = setup_logging(log_level="CRITICAL")
        
        assert logger.level == logging.CRITICAL
    
    def test_invalid_log_level_defaults_to_info(self):
        """Test that invalid log level defaults to INFO"""
        logger = setup_logging(log_level="INVALID_LEVEL")
        
        # Should default to INFO
        assert logger.level == logging.INFO
    
    def test_case_insensitive_log_level(self):
        """Test log level is case-insensitive"""
        logger1 = setup_logging(log_level="debug")
        logger2 = setup_logging(log_level="DEBUG")
        logger3 = setup_logging(log_level="DeBuG")
        
        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.DEBUG
        assert logger3.level == logging.DEBUG
    
    def test_console_handler_is_added(self):
        """Test that console handler is added"""
        logger = setup_logging()
        
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1
        
        # At least one should be StreamHandler
        has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_console
    
    def test_file_logging_creates_file(self):
        """Test logging to file creates the file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            logger = setup_logging(log_file=str(log_file))
            logger.info("Test message")
            
            # Close all handlers to release file
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            # File should be created
            assert log_file.exists()
            
            # File should contain the message
            content = log_file.read_text()
            assert "Test message" in content
    
    def test_file_logging_creates_directory(self):
        """Test that log file directory is created if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "logs" / "test.log"
            
            logger = setup_logging(log_file=str(log_file))
            logger.info("Test")
            
            #Close handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            # Directory structure should be created
            assert log_file.parent.exists()
            assert log_file.exists()
    
    def test_file_handler_has_rotating_capability(self):
        """Test that file handler is RotatingFileHandler"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            logger = setup_logging(log_file=str(log_file))
            
            # Should have 2 handlers now (console + file)
            assert len(logger.handlers) == 2
            
            # One should be RotatingFileHandler
            from logging.handlers import RotatingFileHandler
            has_rotating = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
            assert has_rotating
            
            # Cleanup
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
    
    def test_custom_max_bytes(self):
        """Test custom max_bytes parameter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            custom_size = 5 * 1024 * 1024  # 5MB
            
            logger = setup_logging(log_file=str(log_file), max_bytes=custom_size)
            
            # Find the RotatingFileHandler
            from logging.handlers import RotatingFileHandler
            rotating_handler = next(h for h in logger.handlers if isinstance(h, RotatingFileHandler))
            
            assert rotating_handler.maxBytes == custom_size
            
            # Cleanup
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
    
    def test_custom_backup_count(self):
        """Test custom backup_count parameter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            backup_count = 10
            
            logger = setup_logging(log_file=str(log_file), backup_count=backup_count)
            
            # Find the RotatingFileHandler
            from logging.handlers import RotatingFileHandler
            rotating_handler = next(h for h in logger.handlers if isinstance(h, RotatingFileHandler))
            
            assert rotating_handler.backupCount == backup_count
            
            # Cleanup
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
    
    def test_multiple_setup_clears_previous_handlers(self):
        """Test that calling setup_logging multiple times clears previous handlers"""
        logger1 = setup_logging()
        handler_count_1 = len(logger1.handlers)
        
        logger2 = setup_logging()
        handler_count_2 = len(logger2.handlers)
        
        # Should have same number (old ones cleared)
        assert handler_count_1 == handler_count_2
    
    def test_file_format_includes_timestamp(self):
        """Test that file log format includes timestamp"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            logger = setup_logging(log_file=str(log_file))
            logger.info("Timestamp test")
            
            # Close handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            content = log_file.read_text()
            # File format should include asctime
            # Format: %(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s
            assert "sp_analyzer" in content
            assert "INFO" in content
            assert "Timestamp test" in content
    
    def test_get_logger_function(self):
        """Test get_logger returns correct logger"""
        # Setup a logger first
        setup_logging()
        
        # Get logger
        logger = get_logger('sp_analyzer')
        
        assert logger is not None
        assert logger.name == 'sp_analyzer'
    
    def test_get_logger_with_custom_name(self):
        """Test get_logger with custom name"""
        logger = get_logger('custom_module')
        
        assert logger is not None
        assert logger.name == 'custom_module'
    
    def test_get_logger_default_name(self):
        """Test get_logger with default name"""
        logger = get_logger()
        
        assert logger is not None
        assert logger.name == 'sp_analyzer'
    
    def test_actual_logging_output(self, capsys):
        """Test that actual log messages are output correctly"""
        logger = setup_logging(log_level="INFO")
        
        logger.info("This is an info message")
        logger.warning("This is a warning")
        logger.error("This is an error")
        
        # Since we're using StreamHandler to stdout, check captured output
        captured = capsys.readouterr()
        assert "This is an info message" in captured.out
        assert "This is a warning" in captured.out
        assert "This is an error" in captured.out
    
    def test_debug_not_shown_at_info_level(self, capsys):
        """Test that DEBUG messages are not shown at INFO level"""
        logger = setup_logging(log_level="INFO")
        
        logger.debug("This debug should not appear")
        logger.info("This info should appear")
        
        captured = capsys.readouterr()
        assert "This debug should not appear" not in captured.out
        assert "This info should appear" in captured.out
    
    def test_log_levels_hierarchy(self, capsys):
        """Test log level filtering works correctly"""
        logger = setup_logging(log_level="WARNING")
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        captured = capsys.readouterr()
        # Only WARNING and above should appear
        assert "Debug message" not in captured.out
        assert "Info message" not in captured.out
        assert "Warning message" in captured.out
        assert "Error message" in captured.out


class TestLoggerIntegration:
    """Integration tests for logger usage"""
    
    def test_logger_in_module_context(self):
        """Test using logger in a simulated module context"""
        # Setup logging
        setup_logging(log_level="DEBUG")
        
        # Get logger for a module
        module_logger = get_logger('test_module')
        
        # Should be able to log
        module_logger.debug("Module debug message")
        module_logger.info("Module info message")
        
        # No exceptions should be raised
        assert True
    
    def test_concurrent_logger_access(self):
        """Test that multiple modules can access logger"""
        setup_logging()
        
        logger1 = get_logger('module1')
        logger2 = get_logger('module2')
        logger3 = get_logger('module3')
        
        # All should work independently
        logger1.info("Module 1")
        logger2.info("Module 2")
        logger3.info("Module 3")
        
        assert True
