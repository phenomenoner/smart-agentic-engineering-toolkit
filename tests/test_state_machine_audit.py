from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from scripts.validate_toolkit import build_public_lock

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "engineering-debugging"
CORPUS = ROOT / "evals" / "cases" / "state-machine-audit.json"


def test_hook_is_discoverable_and_the_reference_is_packaged() -> None:
    entry = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(entry.split("---", 2)[1])
    adapter = yaml.safe_load((SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert "@state-audit" in metadata["description"]
    assert "@state-audit" in adapter["interface"]["default_prompt"]
    assert "@state-audit" in plugin["interface"]["defaultPrompt"]
    assert "references/state-machine-audit.md" in entry
    assert (SKILL / "references" / "state-machine-audit.md").is_file()
    released = {row["path"] for row in build_public_lock(ROOT)["files"]}
    assert "skills/engineering-debugging/references/state-machine-audit.md" in released
    assert "evals/cases/state-machine-audit.json" in released


def test_corpus_preserves_routes_authority_and_evidence_origin() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in corpus["cases"]}
    assert len(cases) == len(corpus["cases"]) == 13
    assert corpus["toolkitVersion"] == "0.6.0"
    assert corpus["claimLevel"] == "static-contract-only"
    assert corpus["evidenceStatus"] == "NOT_RUN"
    catalog = json.loads((ROOT / "catalog" / "skills.json").read_text(encoding="utf-8"))
    names = {item["name"] for item in catalog["skills"]}
    for case in cases.values():
        selected, excluded = set(case["expectedSelected"]), set(case["expectedNotSelected"])
        assert selected.isdisjoint(excluded)
        assert selected | excluded <= names
        assert case["observablePass"] and case["prohibitedEffects"]
    assert cases["STATE-HOOK"]["expectedSelected"] == ["engineering-debugging"]
    assert "read-only authority" in cases["STATE-READONLY"]["observablePass"]
    assert "no-change decision" in cases["STATE-NO-CHANGE"]["observablePass"]
    assert "lower state or machine count" in cases["STATE-PRODUCT-GOAL"]["prohibitedEffects"]
    for key in ("STATE-LITERAL-DATA", "STATE-COSMETIC"):
        assert cases[key]["expectedSelected"] == []
        assert cases[key]["expectedNotSelected"] == ["engineering-debugging"]


def test_reference_covers_the_operating_contract_and_direct_path() -> None:
    reference = " ".join((SKILL / "references" / "state-machine-audit.md").read_text(
        encoding="utf-8"
    ).split())
    for required in (
        "Composite flags",
        "Quantity and identity",
        "Time and resources",
        "state representation, owner, events, guards",
        "late success after timeout",
        "final effect check",
        "previously enabled work actually resuming",
        "diagnosis-only, inventory-only or review-only",
        "without asking for the same permission again",
        "An absent index permits ordinary navigation",
        "A justified no-change result is acceptable",
        "A smaller state count is useful only",
        "output or invariant equivalence",
        "reconstructed old-function comparison",
        "concrete behavior deltas",
    ):
        assert required in reference
    assert "does not register an operating-system event handler" in reference


def test_public_examples_avoid_machine_paths() -> None:
    material = CORPUS.read_text(encoding="utf-8")
    material += (SKILL / "references" / "state-machine-audit.md").read_text(encoding="utf-8")
    assert re.search(r"\b[A-Za-z]:[\\/]", material) is None
    assert re.search(r"/(?:home|Users)/[^/\s]+/", material) is None
