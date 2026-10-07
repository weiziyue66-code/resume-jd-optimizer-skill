#!/usr/bin/env python3
"""Validate a local fact store JSON file.

Usage:
    python validate_fact_store.py <fact-store.json>

Exit code is 0 when valid, 1 otherwise. Checks schema_version, candidate ids,
fact required fields, enums, referential integrity of supersedes_fact_id, and
confirmed_at ISO parsing.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

SUPPORTED_SCHEMA_MAJOR = 1
FACT_STATUS_VALUES = ("extracted", "inferred", "user_confirmed", "conflicted", "rejected", "superseded")
SCOPE_VALUES = ("reusable", "role_specific", "jd_specific", "writing_preference")
FACT_REQUIRED_STRINGS = (
    "fact_id", "candidate_id", "source_id", "source_hash",
    "source_version", "fact_value", "fact_status", "source_location", "scope",
)


def _check_str_field(fact, field, errors):
    v = fact.get(field)
    if v is None:
        errors.append("%s: missing required field" % field)
    elif not isinstance(v, str) or not v.strip():
        errors.append("%s: must be a non-empty string" % field)


def validate(path):
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
    except json.JSONDecodeError as exc:
        return ["invalid JSON: %s" % exc]
    except OSError as exc:
        return ["cannot read file: %s" % exc]

    if not isinstance(obj, dict):
        return ["root must be a JSON object"]

    sv = obj.get("schema_version")
    if not isinstance(sv, str):
        errors.append("schema_version: missing or not a string")
    else:
        try:
            major = int(sv.split(".", 1)[0])
        except ValueError:
            major = -1
        if major != SUPPORTED_SCHEMA_MAJOR:
            errors.append("schema_version: unsupported major version %r (expected %d.x)" % (sv, SUPPORTED_SCHEMA_MAJOR))

    candidates = obj.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates: missing or not an array")
        return errors

    candidate_ids = []
    for ci, cand in enumerate(candidates):
        path = "candidates[%d]" % ci
        if not isinstance(cand, dict):
            errors.append("%s: must be an object" % path)
            continue
        cid = cand.get("candidate_id")
        if not isinstance(cid, str) or not cid.strip():
            errors.append("%s.candidate_id: must be a non-empty string" % path)
            continue
        if cid in candidate_ids:
            errors.append("%s.candidate_id: duplicate %r" % (path, cid))
        else:
            candidate_ids.append(cid)

        facts = cand.get("facts")
        if not isinstance(facts, list):
            errors.append("%s.facts: missing or not an array" % path)
            continue

        # First pass: collect fact_ids and detect duplicates.
        fact_ids = set()
        for fi, fact in enumerate(facts):
            if isinstance(fact, dict):
                fid = fact.get("fact_id")
                if isinstance(fid, str) and fid.strip():
                    if fid in fact_ids:
                        errors.append("%s.facts[%d].fact_id: duplicate %r" % (path, fi, fid))
                    else:
                        fact_ids.add(fid)

        # Second pass: validate fields and referential integrity.
        for fi, fact in enumerate(facts):
            fpath = "%s.facts[%d]" % (path, fi)
            if not isinstance(fact, dict):
                errors.append("%s: must be an object" % fpath)
                continue
            for field in FACT_REQUIRED_STRINGS:
                _check_str_field(fact, field, errors)

            if fact.get("candidate_id") != cid:
                errors.append("%s.candidate_id: must equal enclosing candidate_id %r" % (fpath, cid))

            status = fact.get("fact_status")
            if isinstance(status, str) and status not in FACT_STATUS_VALUES:
                errors.append("%s.fact_status: must be one of %s" % (fpath, (FACT_STATUS_VALUES,)))

            scope = fact.get("scope")
            if isinstance(scope, str) and scope not in SCOPE_VALUES:
                errors.append("%s.scope: must be one of %s" % (fpath, (SCOPE_VALUES,)))

            confirmed = fact.get("confirmed_at")
            if confirmed is not None:
                if not isinstance(confirmed, str):
                    errors.append("%s.confirmed_at: must be a string or null" % fpath)
                else:
                    try:
                        datetime.fromisoformat(confirmed)
                    except ValueError:
                        errors.append("%s.confirmed_at: not a parseable ISO 8601 datetime" % fpath)

            supersedes = fact.get("supersedes_fact_id")
            if supersedes is not None:
                if not isinstance(supersedes, str) or not supersedes.strip():
                    errors.append("%s.supersedes_fact_id: must be a string or null" % fpath)
                elif supersedes not in fact_ids:
                    errors.append("%s.supersedes_fact_id: references unknown fact_id %r" % (fpath, supersedes))

    return errors


def main(argv):
    if len(argv) < 2:
        print("usage: python validate_fact_store.py <fact-store.json>")
        return 2
    path = argv[1]
    errors = validate(path)
    if errors:
        print("[x] %s" % path)
        for e in errors:
            print("      - %s" % e)
        print("invalid")
        return 1
    print("[ok] %s" % path)
    print("valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
