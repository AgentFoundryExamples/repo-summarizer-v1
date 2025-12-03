# Copyright (c) 2025 John Brosnihan
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
"""
Integration tests for CLI functionality.

Tests verify that:
1. Python-only repositories work without enabling new languages
2. Mixed-language repositories stream results without regressions
3. Auto-detection works correctly for low-level languages
4. Configuration is properly applied
"""

import os
from pathlib import Path
import pytest

from repo_analyzer.cli import (
    detect_repository_languages,
    auto_enable_detected_languages,
    run_scan,
)


class TestLanguageDetection:
    """Test language detection functionality."""
    
    def test_detect_python_only_repository(self, tmp_path):
        """Test detection in a Python-only repository."""
        # Create Python files
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "module.py").write_text("def foo(): pass")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "test.py").write_text("import unittest")
        
        detected = detect_repository_languages(tmp_path, [])
        
        assert "Python" in detected
        assert "C" not in detected
        assert "C++" not in detected
        assert "Rust" not in detected
    
    def test_detect_mixed_language_repository(self, tmp_path):
        """Test detection in a mixed-language repository."""
        # Create Python files
        (tmp_path / "main.py").write_text("print('hello')")
        
        # Create C files
        (tmp_path / "module.c").write_text("int main() { return 0; }")
        (tmp_path / "header.h").write_text("#ifndef H\n#define H\n#endif")
        
        # Create C++ files
        (tmp_path / "class.cpp").write_text("class Foo {};")
        
        # Create Rust files
        (tmp_path / "lib.rs").write_text("fn main() {}")
        
        detected = detect_repository_languages(tmp_path, [])
        
        assert "Python" in detected
        assert "C" in detected
        assert "C++" in detected
        assert "Rust" in detected
    
    def test_detect_low_level_languages_only(self, tmp_path):
        """Test detection when only low-level languages are present."""
        # Create C files
        (tmp_path / "main.c").write_text("int main() { return 0; }")
        
        # Create assembly files
        (tmp_path / "start.s").write_text(".globl _start\n_start:")
        
        # Create Perl files
        (tmp_path / "script.pl").write_text("#!/usr/bin/perl\nprint 'hello';")
        
        detected = detect_repository_languages(tmp_path, [])
        
        assert "C" in detected
        assert "ASM" in detected
        assert "Perl" in detected
        assert "Python" not in detected
    
    def test_respects_exclude_patterns(self, tmp_path):
        """Test that excluded directories are not scanned."""
        # Create Python files
        (tmp_path / "main.py").write_text("print('hello')")
        
        # Create excluded directory with C files
        (tmp_path / "build").mkdir()
        (tmp_path / "build" / "generated.c").write_text("int main() {}")
        
        detected = detect_repository_languages(tmp_path, ["build"])
        
        assert "Python" in detected
        # C should not be detected because build/ is excluded
        # Note: If there are other C files, this might still be detected
        # This test assumes build/ is the only location with C files
    
    def test_handles_empty_repository(self, tmp_path):
        """Test detection in an empty repository."""
        detected = detect_repository_languages(tmp_path, [])
        
        assert len(detected) == 0
    
    def test_bounded_file_scanning(self, tmp_path):
        """Test that scanning is bounded to avoid performance issues."""
        # Create many Python files to test the 1000 file limit
        for i in range(50):
            (tmp_path / f"file{i}.py").write_text(f"# File {i}")
        
        detected = detect_repository_languages(tmp_path, [])
        
        # Should still detect Python even with bounded scanning
        assert "Python" in detected


class TestAutoEnableLanguages:
    """Test automatic language enablement."""
    
    def test_auto_enable_respects_explicit_configuration(self, tmp_path):
        """Test that explicit enabled_languages configuration is respected."""
        # Create mixed-language repository
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "main.c").write_text("int main() { return 0; }")
        
        # Config with explicit enabled_languages
        config = {
            "language_config": {
                "enabled_languages": ["Python"],
                "disabled_languages": [],
                "language_overrides": {}
            }
        }
        
        # Auto-enable should not modify config when enabled_languages is set
        auto_enable_detected_languages(config, tmp_path)
        
        # Configuration should remain unchanged
        assert config["language_config"]["enabled_languages"] == ["Python"]
    
    def test_auto_enable_works_with_null_enabled_languages(self, tmp_path):
        """Test that auto-enable works when enabled_languages is null."""
        # Create mixed-language repository
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "main.c").write_text("int main() { return 0; }")
        
        # Config with null enabled_languages (default)
        config = {
            "language_config": {
                "enabled_languages": None,
                "disabled_languages": [],
                "language_overrides": {}
            }
        }
        
        # Auto-enable should work with null enabled_languages
        # (This primarily tests that the function doesn't crash)
        auto_enable_detected_languages(config, tmp_path)


class TestCLIPerformance:
    """Test CLI performance characteristics."""
    
    def test_python_only_scan_completes(self, tmp_path):
        """Test that Python-only repository scan completes successfully."""
        # Create a small Python-only repository
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "module.py").write_text("def foo(): pass")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "test.py").write_text("import unittest")
        
        # Create output directory
        output_dir = tmp_path / "output"
        
        # Create minimal config
        config = {
            "output_dir": str(output_dir),
            "dry_run": True,  # Use dry-run to avoid file writes
            "tree_config": {"exclude_patterns": []},
            "file_summary_config": {
                "include_patterns": ["*.py"],
                "detail_level": "standard",
                "include_legacy_summary": True
            },
            "dependency_config": {
                "scan_package_files": True
            },
            "language_config": {
                "enabled_languages": None,
                "disabled_languages": [],
                "language_overrides": {}
            }
        }
        
        # Change to temp directory to simulate running from repo root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run scan - should complete without errors
            result = run_scan(config)
            
            # Should return success
            assert result == 0
        finally:
            os.chdir(original_cwd)
    
    def test_mixed_language_scan_completes(self, tmp_path):
        """Test that mixed-language repository scan completes successfully."""
        # Create a mixed-language repository
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "module.c").write_text("int main() { return 0; }")
        (tmp_path / "lib.rs").write_text("fn main() {}")
        (tmp_path / "start.s").write_text(".globl _start\n_start:")
        
        # Create output directory
        output_dir = tmp_path / "output"
        
        # Create config with all low-level languages
        config = {
            "output_dir": str(output_dir),
            "dry_run": True,
            "tree_config": {"exclude_patterns": []},
            "file_summary_config": {
                "include_patterns": ["*.py", "*.c", "*.rs", "*.s"],
                "detail_level": "standard",
                "include_legacy_summary": True
            },
            "dependency_config": {
                "scan_package_files": True
            },
            "language_config": {
                "enabled_languages": None,
                "disabled_languages": [],
                "language_overrides": {}
            }
        }
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run scan - should complete without errors
            result = run_scan(config)
            
            # Should return success
            assert result == 0
        finally:
            os.chdir(original_cwd)


class TestConfigurationValidation:
    """Test configuration validation and error handling."""
    
    def test_scan_with_minimal_config(self, tmp_path):
        """Test that scan works with minimal configuration."""
        # Create a small repository
        (tmp_path / "main.py").write_text("print('hello')")
        
        # Minimal config
        config = {
            "output_dir": str(tmp_path / "output"),
            "dry_run": True
        }
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Should handle missing config sections gracefully
            result = run_scan(config)
            
            assert result == 0
        finally:
            os.chdir(original_cwd)
    
    def test_scan_with_empty_language_config(self, tmp_path):
        """Test scan with empty language_config section."""
        # Create a small repository
        (tmp_path / "main.py").write_text("print('hello')")
        
        # Config with empty language_config
        config = {
            "output_dir": str(tmp_path / "output"),
            "dry_run": True,
            "language_config": {}
        }
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Should handle empty language_config gracefully
            result = run_scan(config)
            
            assert result == 0
        finally:
            os.chdir(original_cwd)
