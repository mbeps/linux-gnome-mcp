from types import SimpleNamespace

from mcp_server.utils import shell


def test_run_command_success(monkeypatch) -> None:
    def fake_run(command, check, capture_output, text):  # type: ignore[override]
        return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

    monkeypatch.setattr(shell.subprocess, "run", fake_run)
    result = shell.run_command(["echo", "ok"])
    assert result.success is True
    assert result.stdout == "ok"
    assert result.stderr == ""
    assert result.command == "echo ok"
    assert result.returncode == 0


def test_run_command_failure(monkeypatch) -> None:
    def fake_run(command, check, capture_output, text):  # type: ignore[override]
        return SimpleNamespace(stdout="", stderr="boom\n", returncode=1)

    monkeypatch.setattr(shell.subprocess, "run", fake_run)
    result = shell.run_command(["false"])
    assert result.success is False
    assert result.stderr == "boom"
    assert result.returncode == 1
