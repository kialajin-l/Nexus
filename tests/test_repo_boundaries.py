from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_pytest_ini_points_to_public_tests_only():
    pytest_ini = ROOT / "pytest.ini"
    text = pytest_ini.read_text(encoding="utf-8")

    assert "testpaths = tests" in text
    assert "nexus-mvp/tests" not in text


def test_nexus_mvp_directory_is_not_part_of_public_release_surface():
    path = ROOT / "nexus-mvp"
    tracked = subprocess.run(
        ["git", "ls-files", "nexus-mvp"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    ignored = subprocess.run(
        ["git", "check-ignore", "nexus-mvp"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if path.exists():
        assert tracked.stdout.strip() == ""
        assert ignored.returncode == 0
    else:
        assert True


def test_legacy_public_module_directories_are_moved_out_of_root_entrypoints():
    forbidden = [
        ROOT / "src" / "anchor",
        ROOT / "src" / "compress",
        ROOT / "src" / "guard",
        ROOT / "src" / "pipeline",
        ROOT / "src" / "refiner",
        ROOT / "src" / "ruleforge",
    ]
    expected_legacy = [
        ROOT / "legacy" / "skill-v0" / "anchor",
        ROOT / "legacy" / "skill-v0" / "compress",
        ROOT / "legacy" / "skill-v0" / "guard",
        ROOT / "legacy" / "skill-v0" / "pipeline",
        ROOT / "legacy" / "skill-v0" / "refiner",
        ROOT / "legacy" / "skill-v0" / "ruleforge",
    ]

    assert all(not path.exists() for path in forbidden)
    assert all(path.exists() for path in expected_legacy)
