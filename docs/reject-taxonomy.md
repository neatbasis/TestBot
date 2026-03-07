# Reject taxonomy and partition tagging

## Purpose

Decision-stage reject outcomes now use stable machine-oriented fields in `debug.policy`:

- `reject_code` (canonical code)
- `partition` (`intent`, `retrieval`, `rerank`, `contract`, `policy`, `temporal`, `none`)
- numeric context (`score`, `threshold`, `margin`)
- human-readable text in `reason` (and mirrored in `blocker_reason` for backward compatibility)

## Canonical reject codes

| reject_code | partition | Meaning | Example trigger |
| --- | --- | --- | --- |
| `CONTEXT_CONF_BELOW_THRESHOLD` | `rerank` | Context confidence gate did not clear threshold. | Top candidate score/margin does not support direct answer. |
| `TEMPORAL_REFERENCE_UNRESOLVED` | `temporal` | Temporal request could not be resolved reliably. | Time query falls back to clarify/unknown due to unresolved reference. |
| `NO_CITABLE_MEMORY_EVIDENCE` | `retrieval` | No reliable memory evidence for citation-backed answer. | Zero relevant memory hits or unknown fallback for missing evidence. |
| `AMBIGUOUS_MEMORY_CANDIDATES` | `rerank` | Retrieved memories conflict or remain ambiguous. | Clarify flow with ambiguity detected. |
| `ANSWER_CONTRACT_GROUNDING_FAIL` | `contract` | Memory-grounded answer contract failed grounding/citation checks. | Draft answer rejected by answer contract gate. |
| `GK_CONTRACT_MARKER_FAIL` | `contract` | General-knowledge contract marker/confidence support failed. | Missing marker or insufficient support for GK fallback answer. |
| `POLICY_SAFETY_DENY` | `policy` | Policy/safety denial path. | Deny mode selected by policy checks. |
| `NONE` | `none` | No reject condition active. | Memory-grounded or compliant direct answer path. |

## Example payload fragment

```json
{
  "debug.policy": {
    "answer_mode": "assist",
    "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
    "reject_code": "CONTEXT_CONF_BELOW_THRESHOLD",
    "partition": "rerank",
    "score": 0.78,
    "threshold": 1.0,
    "margin": -0.22,
    "reason": "retrieved memory fragments were low-confidence for a direct answer",
    "blocker_reason": "retrieved memory fragments were low-confidence for a direct answer"
  }
}
```

`blocker_reason` remains available for existing log parsers; new machine integrations should use `reject_code` + `partition` + numeric fields.
