from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_ARCH_REPORT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "architecture_boundary_report.py"
_spec = importlib.util.spec_from_file_location("architecture_boundary_report", _ARCH_REPORT_PATH)
assert _spec and _spec.loader
reporter = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = reporter
_spec.loader.exec_module(reporter)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "architecture_boundaries"


def _load_exception_fixture(name: str) -> dict[str, str]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_generate_architecture_boundary_report_classifies_all_statuses(tmp_path: Path) -> None:
    src_dir = tmp_path / "src" / "testbot"
    (src_dir / "entrypoints").mkdir(parents=True)
    (src_dir / "application" / "services").mkdir(parents=True)
    (src_dir / "logic").mkdir(parents=True)
    (src_dir / "domain").mkdir(parents=True)
    (src_dir / "ports").mkdir(parents=True)
    (src_dir / "adapters").mkdir(parents=True)
    (src_dir / "observability").mkdir(parents=True)

    for package in [
        src_dir,
        src_dir / "entrypoints",
        src_dir / "application",
        src_dir / "application" / "services",
        src_dir / "logic",
        src_dir / "domain",
        src_dir / "ports",
        src_dir / "adapters",
        src_dir / "observability",
    ]:
        (package / "__init__.py").write_text("", encoding="utf-8")

    (src_dir / "domain" / "model.py").write_text("VALUE = 1\n", encoding="utf-8")
    (src_dir / "domain" / "internal.py").write_text("SECRET = 1\n", encoding="utf-8")
    (src_dir / "ports" / "contracts.py").write_text("CONTRACT = 1\n", encoding="utf-8")
    (src_dir / "logic" / "core.py").write_text(
        "from testbot.domain import model\n"
        "from testbot.domain import internal\n",
        encoding="utf-8",
    )
    (src_dir / "application" / "services" / "turn_service.py").write_text(
        "from testbot.logic import core\n"
        "from testbot.answer_render import compat\n",
        encoding="utf-8",
    )
    (src_dir / "entrypoints" / "cli.py").write_text(
        "from testbot.application.services import turn_service\n",
        encoding="utf-8",
    )
    (src_dir / "adapters" / "http.py").write_text(
        "from testbot.observability import telemetry\n",
        encoding="utf-8",
    )
    (src_dir / "observability" / "telemetry.py").write_text("EVENT = 1\n", encoding="utf-8")
    (src_dir / "answer_render.py").write_text("compat = True\n", encoding="utf-8")

    config = {
        "version": 1,
        "package_name": "testbot",
        "package_root": str(src_dir),
        "areas": [
            {
                "name": "entrypoints",
                "module_globs": ["testbot.entrypoints", "testbot.entrypoints.*"],
                "allowed_dependencies": ["entrypoints", "application"],
                "public_surface": {"modules": ["testbot.entrypoints"], "module_prefixes": ["testbot.entrypoints"]},
            },
            {
                "name": "application",
                "module_globs": ["testbot.application", "testbot.application.*"],
                "allowed_dependencies": ["application", "logic", "domain"],
                "public_surface": {
                    "modules": ["testbot.application", "testbot.application.services", "testbot.application.services.turn_service"],
                    "module_prefixes": ["testbot.application.services"],
                },
            },
            {
                "name": "logic",
                "module_globs": ["testbot.logic", "testbot.logic.*"],
                "allowed_dependencies": ["logic", "domain"],
                "public_surface": {"modules": ["testbot.logic"], "module_prefixes": ["testbot.logic"]},
            },
            {
                "name": "domain",
                "module_globs": ["testbot.domain", "testbot.domain.*"],
                "allowed_dependencies": ["domain"],
                "public_surface": {"modules": ["testbot.domain", "testbot.domain.model"], "module_prefixes": ["testbot.domain.model"]},
            },
            {
                "name": "ports",
                "module_globs": ["testbot.ports", "testbot.ports.*"],
                "allowed_dependencies": ["ports", "domain"],
                "public_surface": {"modules": ["testbot.ports"], "module_prefixes": ["testbot.ports"]},
            },
            {
                "name": "adapters",
                "module_globs": ["testbot.adapters", "testbot.adapters.*"],
                "allowed_dependencies": ["adapters", "ports", "domain", "observability"],
                "public_surface": {"modules": ["testbot.adapters"], "module_prefixes": ["testbot.adapters"]},
            },
            {
                "name": "observability",
                "module_globs": ["testbot.observability", "testbot.observability.*"],
                "allowed_dependencies": ["observability", "domain"],
                "public_surface": {"modules": ["testbot.observability"], "module_prefixes": ["testbot.observability"]},
            },
        ],
        "temporary_exceptions": [_load_exception_fixture("temporary_exception_valid.json")],
        "deprecated_compatibility": {"module_globs": ["testbot.answer_render"]},
    }

    original_repo_root = reporter.REPO_ROOT
    reporter.REPO_ROOT = tmp_path
    try:
        report = reporter.generate_architecture_boundary_report(config)
    finally:
        reporter.REPO_ROOT = original_repo_root

    classes = {finding["classification"] for finding in report["findings"]}
    assert classes >= {"allowed", "violation", "temporary_exception", "deprecated_compatibility"}

    area_names = {area["name"] for area in report["areas"]}
    assert area_names == {
        "entrypoints",
        "application",
        "logic",
        "domain",
        "ports",
        "adapters",
        "observability",
    }


def test_main_writes_machine_readable_output(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "architecture-boundaries.json"
    output_path = tmp_path / "architecture-boundary-report.json"
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "package_name": "testbot",
                "package_root": "src/testbot",
                "areas": [
                    {
                        "name": "entrypoints",
                        "module_globs": ["testbot.*"],
                        "allowed_dependencies": ["entrypoints"],
                        "public_surface": {"modules": ["testbot"], "module_prefixes": ["testbot"]},
                    },
                    {
                        "name": "application",
                        "module_globs": [],
                        "allowed_dependencies": ["application"],
                        "public_surface": {"modules": [], "module_prefixes": []},
                    },
                    {
                        "name": "logic",
                        "module_globs": [],
                        "allowed_dependencies": ["logic"],
                        "public_surface": {"modules": [], "module_prefixes": []},
                    },
                    {
                        "name": "domain",
                        "module_globs": [],
                        "allowed_dependencies": ["domain"],
                        "public_surface": {"modules": [], "module_prefixes": []},
                    },
                    {
                        "name": "ports",
                        "module_globs": [],
                        "allowed_dependencies": ["ports"],
                        "public_surface": {"modules": [], "module_prefixes": []},
                    },
                    {
                        "name": "adapters",
                        "module_globs": [],
                        "allowed_dependencies": ["adapters"],
                        "public_surface": {"modules": [], "module_prefixes": []},
                    },
                    {
                        "name": "observability",
                        "module_globs": [],
                        "allowed_dependencies": ["observability"],
                        "public_surface": {"modules": [], "module_prefixes": []},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "architecture_boundary_report.py",
            "--config",
            str(config_path),
            "--output",
            str(output_path),
        ],
    )

    exit_code = reporter.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["summary"]["counts_by_classification"]["allowed"] >= 0
    assert isinstance(payload["findings"], list)


def test_expired_temporary_exception_is_downgraded_to_violation(tmp_path: Path) -> None:
    src_dir = tmp_path / "src" / "testbot"
    (src_dir / "adapters").mkdir(parents=True)
    (src_dir / "observability").mkdir(parents=True)

    for package in [src_dir, src_dir / "adapters", src_dir / "observability"]:
        (package / "__init__.py").write_text("", encoding="utf-8")

    (src_dir / "adapters" / "http.py").write_text(
        "from testbot.observability import telemetry\n",
        encoding="utf-8",
    )
    (src_dir / "observability" / "telemetry.py").write_text("EVENT = 1\n", encoding="utf-8")

    config = {
        "version": 1,
        "package_name": "testbot",
        "package_root": str(src_dir),
        "areas": [
            {
                "name": "adapters",
                "module_globs": ["testbot.adapters", "testbot.adapters.*"],
                "allowed_dependencies": ["adapters", "observability"],
                "public_surface": {"modules": ["testbot.adapters"], "module_prefixes": ["testbot.adapters"]},
            },
            {
                "name": "observability",
                "module_globs": ["testbot.observability", "testbot.observability.*"],
                "allowed_dependencies": ["observability"],
                "public_surface": {"modules": ["testbot.observability"], "module_prefixes": ["testbot.observability"]},
            },
        ],
        "temporary_exceptions": [_load_exception_fixture("temporary_exception_expired.json")],
    }

    original_repo_root = reporter.REPO_ROOT
    reporter.REPO_ROOT = tmp_path
    try:
        report = reporter.generate_architecture_boundary_report(config)
    finally:
        reporter.REPO_ROOT = original_repo_root

    downgraded_finding = next(
        finding
        for finding in report["findings"]
        if finding["importer"] == "testbot.adapters.http" and finding["imported"] == "testbot.observability.telemetry"
    )
    assert downgraded_finding["classification"] == "violation"
    assert downgraded_finding["reason"] == "expired_temporary_exception"
    assert downgraded_finding["metadata"]["downgraded_from"] == "temporary_exception"
    assert downgraded_finding["metadata"]["expiry_enforcement"] == "temporary_exception_expired"
    assert downgraded_finding["metadata"]["expires_on"] == "2020-01-01"
    assert report["summary"]["counts_by_classification"]["violation"] == 1
    assert report["summary"]["counts_by_classification"]["temporary_exception"] == 0


def test_valid_temporary_exception_remains_non_violation(tmp_path: Path) -> None:
    src_dir = tmp_path / "src" / "testbot"
    (src_dir / "adapters").mkdir(parents=True)
    (src_dir / "observability").mkdir(parents=True)

    for package in [src_dir, src_dir / "adapters", src_dir / "observability"]:
        (package / "__init__.py").write_text("", encoding="utf-8")

    (src_dir / "adapters" / "http.py").write_text(
        "from testbot.observability import telemetry\n",
        encoding="utf-8",
    )
    (src_dir / "observability" / "telemetry.py").write_text("EVENT = 1\n", encoding="utf-8")

    config = {
        "version": 1,
        "package_name": "testbot",
        "package_root": str(src_dir),
        "areas": [
            {
                "name": "adapters",
                "module_globs": ["testbot.adapters", "testbot.adapters.*"],
                "allowed_dependencies": ["adapters", "observability"],
                "public_surface": {"modules": ["testbot.adapters"], "module_prefixes": ["testbot.adapters"]},
            },
            {
                "name": "observability",
                "module_globs": ["testbot.observability", "testbot.observability.*"],
                "allowed_dependencies": ["observability"],
                "public_surface": {"modules": ["testbot.observability"], "module_prefixes": ["testbot.observability"]},
            },
        ],
        "temporary_exceptions": [_load_exception_fixture("temporary_exception_valid.json")],
    }

    original_repo_root = reporter.REPO_ROOT
    reporter.REPO_ROOT = tmp_path
    try:
        report = reporter.generate_architecture_boundary_report(config)
    finally:
        reporter.REPO_ROOT = original_repo_root

    finding = next(
        candidate
        for candidate in report["findings"]
        if candidate["importer"] == "testbot.adapters.http" and candidate["imported"] == "testbot.observability.telemetry"
    )
    assert finding["classification"] == "temporary_exception"
    assert finding["reason"] == "explicit_temporary_exception"
    assert finding["metadata"]["issue"] == "ISSUE-VALID-0001"
    assert finding["metadata"]["owner"] == "platform-architecture"
    assert finding["metadata"]["removal_plan"].startswith("Remove adapter->observability shim")
