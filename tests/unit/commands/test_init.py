"""Unit tests for init command."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from amplifier.cli.commands import init


class TestInitCommand:
    """Test init command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project directory."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project

    def test_init_creates_directory_structure(self, runner, temp_project):
        """Test init creates all required directories."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            assert (Path.cwd() / ".claude").exists()
            assert (Path.cwd() / ".claude" / "agents").exists()
            assert (Path.cwd() / ".claude" / "tools").exists()
            assert (Path.cwd() / ".claude" / "commands").exists()
            assert (Path.cwd() / ".claude" / "mcp-servers").exists()
            assert (Path.cwd() / ".amplifier").exists()

    def test_init_creates_manifest_file(self, runner, temp_project):
        """Test init creates valid manifest.json."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            manifest_path = Path.cwd() / ".amplifier" / "manifest.json"
            assert manifest_path.exists()

            # Verify manifest content
            import json

            with open(manifest_path) as f:
                manifest = json.load(f)

            assert "metadata" in manifest
            assert "resources" in manifest
            assert manifest["metadata"]["amplifier_version"] == "3.0.0"
            assert isinstance(manifest["resources"], list)

    def test_init_creates_settings_file(self, runner, temp_project):
        """Test init creates settings.json."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            settings_path = Path.cwd() / ".amplifier" / "settings.json"
            assert settings_path.exists()

            # Verify settings content
            import json

            with open(settings_path) as f:
                settings = json.load(f)

            assert "auto_update" in settings
            assert "github_token" in settings
            assert "default_ref" in settings

    def test_init_creates_ai_context_files(self, runner, temp_project):
        """Test init creates AI context documentation files."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            assert (Path.cwd() / "CLAUDE.md").exists()
            assert (Path.cwd() / "AGENTS.md").exists()
            assert (Path.cwd() / "DISCOVERIES.md").exists()
            assert (Path.cwd() / "ai_context").exists()
            assert (Path.cwd() / "ai_context" / "IMPLEMENTATION_PHILOSOPHY.md").exists()
            assert (Path.cwd() / "ai_context" / "MODULAR_DESIGN_PHILOSOPHY.md").exists()

    def test_init_existing_project_without_force(self, runner, temp_project):
        """Test init refuses to overwrite without --force."""
        # Arrange
        with runner.isolated_filesystem(temp_dir=temp_project):
            # Create existing structure
            (Path.cwd() / ".claude").mkdir()

            # Act
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            assert "already initialized" in result.output.lower()

    def test_init_with_force_flag(self, runner, temp_project):
        """Test init --force overwrites existing project."""
        # Arrange
        with runner.isolated_filesystem(temp_dir=temp_project):
            # Create existing files
            (Path.cwd() / ".claude").mkdir()
            existing_file = Path.cwd() / ".claude" / "test.txt"
            existing_file.write_text("existing content")

            # Act
            result = runner.invoke(init.cmd, ["--force"])

            # Assert
            assert result.exit_code == 0
            # Directory should be recreated
            assert (Path.cwd() / ".claude").exists()
            assert (Path.cwd() / ".claude" / "agents").exists()
            # Old file should be gone
            assert not existing_file.exists()

    def test_init_repair_mode_fixes_missing_directories(self, runner, temp_project):
        """Test init --repair adds missing directories."""
        # Arrange
        with runner.isolated_filesystem(temp_dir=temp_project):
            # Create partial structure
            (Path.cwd() / ".claude").mkdir()
            (Path.cwd() / ".claude" / "agents").mkdir()
            # Missing: tools, commands, mcp-servers

            # Act
            result = runner.invoke(init.cmd, ["--repair"])

            # Assert
            assert result.exit_code == 0
            assert (Path.cwd() / ".claude" / "tools").exists()
            assert (Path.cwd() / ".claude" / "commands").exists()
            assert (Path.cwd() / ".claude" / "mcp-servers").exists()

    def test_init_repair_mode_fixes_corrupted_manifest(self, runner, temp_project):
        """Test init --repair fixes corrupted manifest."""
        # Arrange
        with runner.isolated_filesystem(temp_dir=temp_project):
            # Create structure with corrupted manifest
            (Path.cwd() / ".claude").mkdir()
            (Path.cwd() / ".amplifier").mkdir()

            manifest_path = Path.cwd() / ".amplifier" / "manifest.json"
            manifest_path.write_text("invalid json{")

            # Act
            result = runner.invoke(init.cmd, ["--repair"])

            # Assert
            assert result.exit_code == 0

            # Manifest should be valid now
            import json

            with open(manifest_path) as f:
                manifest = json.load(f)  # Should not raise

            assert "metadata" in manifest
            assert "resources" in manifest

    def test_init_preserves_existing_ai_context_files(self, runner, temp_project):
        """Test init preserves existing AI context files when not forced."""
        # Arrange
        with runner.isolated_filesystem(temp_dir=temp_project):
            # Create existing CLAUDE.md with custom content
            claude_md = Path.cwd() / "CLAUDE.md"
            claude_md.write_text("# Custom CLAUDE.md\n\nCustom content here")

            # Act
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            # Original content should be preserved
            assert "Custom content here" in claude_md.read_text()
            # But other files should be created
            assert (Path.cwd() / "AGENTS.md").exists()

    @patch("amplifier.cli.commands.init._create_project_files")
    def test_init_handles_permission_error(self, mock_create, runner, temp_project):
        """Test init handles permission errors gracefully."""
        # Arrange
        mock_create.side_effect = PermissionError("Cannot write files")

        with runner.isolated_filesystem(temp_dir=temp_project):
            # Act
            result = runner.invoke(init.cmd)

            # Assert
            # Should handle error without crashing
            assert result.exit_code != 0
            assert "permission" in result.output.lower() or "error" in result.output.lower()

    def test_init_with_quiet_flag(self, runner, temp_project):
        """Test init --quiet minimizes output."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd, ["--quiet"])

            # Assert
            assert result.exit_code == 0
            # Output should be minimal
            assert len(result.output.strip().split("\n")) < 5
            # But still create everything
            assert (Path.cwd() / ".claude").exists()
            assert (Path.cwd() / ".amplifier" / "manifest.json").exists()

    def test_init_with_debug_flag(self, runner, temp_project):
        """Test init --debug provides verbose output."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd, ["--debug"])

            # Assert
            assert result.exit_code == 0
            # Should have debug output
            assert "debug" in result.output.lower() or len(result.output) > 500

    def test_init_creates_mcp_json_when_missing(self, runner, temp_project):
        """Test init creates .mcp.json if it doesn't exist."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            mcp_path = Path.cwd() / ".mcp.json"
            if mcp_path.exists():
                # Verify it's valid JSON
                import json

                with open(mcp_path) as f:
                    mcp_config = json.load(f)
                assert isinstance(mcp_config, dict)

    def test_init_idempotency(self, runner, temp_project):
        """Test init can be run multiple times safely."""
        # Arrange & Act
        with runner.isolated_filesystem(temp_dir=temp_project):
            # First init
            result1 = runner.invoke(init.cmd)
            assert result1.exit_code == 0

            # Second init
            result2 = runner.invoke(init.cmd)
            assert result2.exit_code == 0
            assert "already initialized" in result2.output.lower()

            # Third init with force
            result3 = runner.invoke(init.cmd, ["--force"])
            assert result3.exit_code == 0

            # All directories should still exist
            assert (Path.cwd() / ".claude").exists()
            assert (Path.cwd() / ".amplifier").exists()

    @patch("amplifier.cli.core.output.get_output_manager")
    def test_init_uses_output_manager(self, mock_output, runner, temp_project):
        """Test init uses output manager for all output."""
        # Arrange
        mock_manager = MagicMock()
        mock_output.return_value = mock_manager

        with runner.isolated_filesystem(temp_dir=temp_project):
            # Act
            result = runner.invoke(init.cmd)

            # Assert
            assert result.exit_code == 0
            # Should have called output manager methods
            mock_manager.info.assert_called()
            mock_manager.section_header.assert_called()
            mock_manager.success.assert_called()

    def test_init_handles_partial_failure(self, runner, temp_project):
        """Test init handles partial creation failures gracefully."""
        # Arrange
        with runner.isolated_filesystem(temp_dir=temp_project):
            # Create .claude as a file, not directory (will cause error)
            (Path.cwd() / ".claude").write_text("not a directory")

            # Act
            result = runner.invoke(init.cmd)

            # Assert
            # Should handle error gracefully
            assert result.exit_code != 0
            assert "error" in result.output.lower()
