"""Documentation boundary contracts; these are not fresh-agent execution evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hermes_reviewer_cannot_reuse_globally_pinned_worker():
    text = (ROOT / 'skills/engineering-wal/references/canon-orchestration.md').read_text()
    assert 'globally Luna-pinned `delegate_task` is not a reviewer override' in text
    assert 'Do not toggle shared config' in text


def test_missing_route_telemetry_is_not_fabricated_or_a_mismatch():
    text = (ROOT / 'skills/engineering-wal/references/canon-orchestration.md').read_text()
    assert 'reject an observed effective-route mismatch' in text
    assert 'per-request telemetry' in text
    assert 'claiming an effective-route readback or treating its absence as a mismatch' in text


def test_narrow_audit_preserves_original_and_uses_existing_schema():
    text = (ROOT / 'skills/batch-complete-independent-review/SKILL.md').read_text()
    assert '`batch-review-cross-audit.v1`' in text
    assert '`batch-narrow-audit.v1` report is not validator-compatible' in text
    assert 'non-native report unchanged as raw evidence' in text
    assert 'validate it through `validate-synthesis`' in text


def test_financial_savings_do_not_require_fewer_tokens_or_latency_gain():
    text = (ROOT / 'skills/engineering-wal/references/canon-orchestration.md').read_text()
    normalized = ' '.join(text.split())
    assert 'estimated monetary cost as well as latency' in normalized
    assert 'model-specific input/output/cached-token prices' in normalized
    assert 'more total tokens can still cost less' in normalized
    assert 'Financial savings can justify bounded delegation without a speed gain' in normalized
    assert 'estimated saving as measured billing evidence' in normalized
