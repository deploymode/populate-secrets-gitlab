"""Tests for app.py commands.

Mocks only at the gitlab API boundary (gitlab.Gitlab client / project.variables).
"""

import os
from unittest.mock import MagicMock, patch

import click.testing
import pytest

from populate_secrets_gitlab.app import cli


def _make_variable(key, value, environment_scope="*", masked=False):
    v = MagicMock()
    v.key = key
    v.value = value
    v.environment_scope = environment_scope
    v.masked = masked
    return v


def _make_project(name="test-project", project_id=42, variables=None):
    proj = MagicMock()
    proj.name = name
    proj.id = project_id
    proj.variables.list.return_value = variables or []
    return proj


def _make_gitlab_client(project):
    client = MagicMock()
    client.projects.get.return_value = project
    return client


def _invoke_write(tmp_path, env_content, environment, extra_args=None, variables=None):
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)

    project = _make_project(variables=variables or [])
    client = _make_gitlab_client(project)

    args = [
        "write",
        "--env-file", str(env_file),
        "--environment", environment,
        "--gitlab-host", "gitlab.example.com",
        "--project", "test/project",
    ]
    if extra_args:
        args.extend(extra_args)

    with patch.dict(os.environ, {"GITLAB_TOKEN": "fake-token"}):
        with patch("populate_secrets_gitlab.app.gitlab_client", return_value=client):
            runner = click.testing.CliRunner()
            result = runner.invoke(cli, args)

    return result, project


# --- Task 1 regression: write to a fresh (empty) environment scope ---

class TestWriteFreshEnvironment:
    """The write command must create variables when the target environment
    has zero existing variables (no entry in the scope dict)."""

    def test_create_vars_when_scope_has_no_existing_variables(self, tmp_path):
        result, project = _invoke_write(tmp_path, "APP_NAME=hello\n", "staging")

        assert result.exit_code == 0, result.output
        project.variables.create.assert_called_once_with({
            "key": "APP_NAME",
            "value": "hello",
            "environment_scope": "staging",
        })

    def test_updates_existing_var_in_known_scope(self, tmp_path):
        existing_var = _make_variable("DB_HOST", "old-value", environment_scope="uat")
        result, project = _invoke_write(
            tmp_path, "DB_HOST=localhost\n", "uat", variables=[existing_var],
        )

        assert result.exit_code == 0, result.output
        assert existing_var.value == "localhost"
        existing_var.save.assert_called_once()
        project.variables.create.assert_not_called()


# --- Masking heuristic ---

class TestMaskingHeuristic:
    def test_key_containing_KEY_is_masked(self, tmp_path):
        result, project = _invoke_write(
            tmp_path, "API_KEY=secret123\n", "prod", extra_args=["--mask"],
        )

        assert result.exit_code == 0, result.output
        project.variables.create.assert_called_once()
        payload = project.variables.create.call_args[0][0]
        assert payload["masked"] is True

    def test_key_containing_SECRET_is_masked(self, tmp_path):
        _, project = _invoke_write(
            tmp_path, "MY_SECRET=shhh\n", "prod", extra_args=["--mask"],
        )
        payload = project.variables.create.call_args[0][0]
        assert payload["masked"] is True

    def test_key_containing_TOKEN_is_masked(self, tmp_path):
        _, project = _invoke_write(
            tmp_path, "AUTH_TOKEN=abc\n", "prod", extra_args=["--mask"],
        )
        payload = project.variables.create.call_args[0][0]
        assert payload["masked"] is True

    def test_non_matching_key_is_not_masked(self, tmp_path):
        _, project = _invoke_write(
            tmp_path, "APP_NAME=myapp\n", "prod", extra_args=["--mask"],
        )
        payload = project.variables.create.call_args[0][0]
        assert "masked" not in payload

    def test_masking_not_applied_without_flag(self, tmp_path):
        _, project = _invoke_write(tmp_path, "API_KEY=secret123\n", "prod")
        payload = project.variables.create.call_args[0][0]
        assert "masked" not in payload


# --- Token-missing error consistency (Task 3) ---

class TestMissingTokenError:
    """All four commands should raise click.ClickException (clean exit, no traceback)."""

    @pytest.fixture(autouse=True)
    def _clear_token(self):
        with patch.dict(os.environ, {}, clear=True):
            yield

    def _invoke(self, args):
        runner = click.testing.CliRunner()
        return runner.invoke(cli, args)

    def test_write_missing_token(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("X=1\n")
        result = self._invoke([
            "write", "--env-file", str(env_file),
            "--environment", "uat", "--gitlab-host", "h", "--project", "p",
        ])
        assert result.exit_code == 1
        assert "GITLAB_TOKEN" in result.output
        assert "Traceback" not in result.output

    def test_get_missing_token(self):
        result = self._invoke([
            "get", "--environment", "uat", "--gitlab-host", "h", "--project", "p",
        ])
        assert result.exit_code == 1
        assert "GITLAB_TOKEN" in result.output
        assert "Traceback" not in result.output

    def test_list_missing_token(self):
        result = self._invoke([
            "list", "--environment", "uat", "--gitlab-host", "h", "--project", "p",
        ])
        assert result.exit_code == 1
        assert "GITLAB_TOKEN" in result.output
        assert "Traceback" not in result.output

    def test_download_missing_token(self):
        result = self._invoke([
            "download", "--environment", "uat", "--gitlab-host", "h", "--project", "p",
        ])
        assert result.exit_code == 1
        assert "GITLAB_TOKEN" in result.output
        assert "Traceback" not in result.output


# --- get --export idempotence (Task 4) ---

class TestGetExportOverwrite:
    """Running get --export twice should not duplicate lines."""

    def test_export_does_not_duplicate_on_rerun(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        variables = [
            _make_variable("A_VAR", "1", environment_scope="uat"),
            _make_variable("B_VAR", "2", environment_scope="uat"),
        ]
        project = _make_project(variables=variables)
        client = _make_gitlab_client(project)

        runner = click.testing.CliRunner()
        with patch.dict(os.environ, {"GITLAB_TOKEN": "fake-token"}):
            with patch("populate_secrets_gitlab.app.gitlab_client", return_value=client):
                for _ in range(2):
                    result = runner.invoke(cli, [
                        "get",
                        "--environment", "uat",
                        "--gitlab-host", "gitlab.example.com",
                        "--project", "test/project",
                        "--export",
                    ])
                    assert result.exit_code == 0, result.output

        env_file = tmp_path / "uat.env"
        lines = env_file.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "A_VAR=1" in lines
        assert "B_VAR=2" in lines

    def test_export_writes_global_scope_to_global_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        variables = [
            _make_variable("GLOBAL_VAR", "g", environment_scope="*"),
        ]
        project = _make_project(variables=variables)
        client = _make_gitlab_client(project)

        runner = click.testing.CliRunner()
        with patch.dict(os.environ, {"GITLAB_TOKEN": "fake-token"}):
            with patch("populate_secrets_gitlab.app.gitlab_client", return_value=client):
                result = runner.invoke(cli, [
                    "get",
                    "--environment", "uat",
                    "--gitlab-host", "gitlab.example.com",
                    "--project", "test/project",
                    "--export",
                ])
                assert result.exit_code == 0, result.output

        global_file = tmp_path / "global.env"
        assert global_file.exists()
        assert "GLOBAL_VAR=g" in global_file.read_text()


# --- Scope filtering (used by list/get/download) ---

class TestScopeFiltering:
    """Variables scoped to '*' are treated as global and included for any
    environment. Variables scoped to a specific environment are only included
    for that environment."""

    def test_global_scope_included_for_any_environment(self):
        variables = [
            _make_variable("GLOBAL_VAR", "g", environment_scope="*"),
            _make_variable("UAT_VAR", "u", environment_scope="uat"),
        ]
        project = _make_project(variables=variables)
        client = _make_gitlab_client(project)

        runner = click.testing.CliRunner()
        with patch.dict(os.environ, {"GITLAB_TOKEN": "fake-token"}):
            with patch("populate_secrets_gitlab.app.gitlab_client", return_value=client):
                result = runner.invoke(cli, [
                    "list",
                    "--environment", "uat",
                    "--gitlab-host", "gitlab.example.com",
                    "--project", "test/project",
                ])

        assert result.exit_code == 0
        assert "GLOBAL_VAR" in result.output
        assert "UAT_VAR" in result.output

    def test_other_environment_vars_excluded(self):
        variables = [
            _make_variable("PROD_VAR", "p", environment_scope="prod"),
        ]
        project = _make_project(variables=variables)
        client = _make_gitlab_client(project)

        runner = click.testing.CliRunner()
        with patch.dict(os.environ, {"GITLAB_TOKEN": "fake-token"}):
            with patch("populate_secrets_gitlab.app.gitlab_client", return_value=client):
                result = runner.invoke(cli, [
                    "list",
                    "--environment", "uat",
                    "--gitlab-host", "gitlab.example.com",
                    "--project", "test/project",
                ])

        assert "PROD_VAR" not in result.output
