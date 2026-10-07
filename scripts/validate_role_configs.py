#!/usr/bin/env python3
"""Validate role config files under references/role-configs/.

Usage:
    python validate_role_configs.py [role-configs-dir]

Exit code is 0 when every config is valid, 1 otherwise. A single invalid
config is reported and isolated; remaining configs are still checked.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

SUPPORTED_SCHEMA_MAJOR = 1
TIER_VALUES = ("primary", "secondary")
SCOPE_VALUES = ("distinctive", "generic")
ROLE_ID_RE = re.compile(r"^[a-z0-9_]+$")
CLUSTER_ID_RE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")

STRING_FIELDS = ("schema_version", "role_id", "name_zh", "tier", "expression_focus")
STRING_LIST_FIELDS = ("action_verbs", "typical_responsibilities", "typical_deliverables", "metric_examples")
CLUSTER_STRING_FIELDS = ("cluster_id", "name_zh", "scope")


def _check_string_list(value, field, errors):
    if not isinstance(value, list):
        errors.append("%s: must be an array" % field)
        return
    for i, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append("%s[%d]: must be a non-empty string" % (field, i))


def _check_optional_weight(value, path, errors):
    # "非法权重" guard: any optional numeric weight field must be finite.
    for key in ("weight", "weights"):
        if key in value:
            w = value[key]
            if isinstance(w, bool) or not isinstance(w, (int, float)):
                errors.append("%s.%s: must be a finite number" % (path, key))
            elif not math.isfinite(w):
                errors.append("%s.%s: must be finite" % (path, key))


def validate_config(obj):
    errors = []
    if not isinstance(obj, dict):
        return ["root must be a JSON object"]

    for field in STRING_FIELDS:
        if field not in obj:
            errors.append("%s: missing required field" % field)
        elif not isinstance(obj[field], str) or not obj[field].strip():
            errors.append("%s: must be a non-empty string" % field)

    sv = obj.get("schema_version")
    if isinstance(sv, str):
        try:
            major = int(sv.split(".", 1)[0])
        except ValueError:
            major = -1
        if major != SUPPORTED_SCHEMA_MAJOR:
            errors.append("schema_version: unsupported major version %r (expected %d.x)" % (sv, SUPPORTED_SCHEMA_MAJOR))

    role_id = obj.get("role_id")
    if isinstance(role_id, str):
        if not ROLE_ID_RE.match(role_id):
            errors.append("role_id: must match %s" % ROLE_ID_RE.pattern)
        elif len(role_id) > 64:
            errors.append("role_id: must be <= 64 characters")

    tier = obj.get("tier")
    if isinstance(tier, str) and tier not in TIER_VALUES:
        errors.append("tier: must be one of %s" % (TIER_VALUES,))

    for field in STRING_LIST_FIELDS:
        _check_string_list(obj.get(field), field, errors)

    confusable = obj.get("confusable_roles")
    if confusable is None:
        errors.append("confusable_roles: missing required field")
    elif not isinstance(confusable, dict):
        errors.append("confusable_roles: must be an object")
    else:
        for k, v in confusable.items():
            if not isinstance(k, str) or not k.strip():
                errors.append("confusable_roles: keys must be non-empty role_id strings")
            if not isinstance(v, str) or not v.strip():
                errors.append("confusable_roles.%s: value must be a non-empty string" % k)

    clusters = obj.get("clusters")
    if clusters is None:
        errors.append("clusters: missing required field")
    elif not isinstance(clusters, list) or len(clusters) == 0:
        errors.append("clusters: must be a non-empty array")
    else:
        for i, cluster in enumerate(clusters):
            path = "clusters[%d]" % i
            if not isinstance(cluster, dict):
                errors.append("%s: must be an object" % path)
                continue
            for field in CLUSTER_STRING_FIELDS:
                if field not in cluster:
                    errors.append("%s.%s: missing required field" % (path, field))
                elif not isinstance(cluster[field], str) or not cluster[field].strip():
                    errors.append("%s.%s: must be a non-empty string" % (path, field))

            cid = cluster.get("cluster_id")
            if isinstance(cid, str):
                if not CLUSTER_ID_RE.match(cid):
                    errors.append("%s.cluster_id: must match %s" % (path, CLUSTER_ID_RE.pattern))
                elif isinstance(role_id, str) and not cid.startswith(role_id + "."):
                    errors.append("%s.cluster_id: must be prefixed by role_id %r" % (path, role_id))

            scope = cluster.get("scope")
            if isinstance(scope, str) and scope not in SCOPE_VALUES:
                errors.append("%s.scope: must be one of %s" % (path, (SCOPE_VALUES,)))

            keywords = cluster.get("keywords")
            if keywords is None:
                errors.append("%s.keywords: missing required field" % path)
            elif not isinstance(keywords, list) or len(keywords) == 0:
                errors.append("%s.keywords: must be a non-empty array" % path)
            else:
                seen = set()
                for j, kw in enumerate(keywords):
                    if not isinstance(kw, str) or not kw.strip():
                        errors.append("%s.keywords[%d]: must be a non-empty string" % (path, j))
                    else:
                        norm = kw.strip()
                        if norm in seen:
                            errors.append("%s.keywords[%d]: duplicate keyword %r" % (path, j, norm))
                        seen.add(norm)

            _check_optional_weight(cluster, path, errors)

    _check_optional_weight(obj, "root", errors)
    return errors


def main(argv):
    if len(argv) > 1:
        role_dir = argv[1]
    else:
        skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        role_dir = os.path.join(skill_root, "references", "role-configs")

    if not os.path.isdir(role_dir):
        print("role configs directory not found: %s" % role_dir)
        return 2

    files = sorted(
        os.path.join(role_dir, f)
        for f in os.listdir(role_dir)
        if f.endswith(".json")
    )
    if not files:
        print("no *.json files found in %s" % role_dir)
        return 1

    role_ids = {}
    cluster_ids = {}
    per_file = []

    for path in files:
        name = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                obj = json.load(fh)
        except json.JSONDecodeError as exc:
            per_file.append((name, ["invalid JSON: %s" % exc]))
            continue
        except OSError as exc:
            per_file.append((name, ["cannot read file: %s" % exc]))
            continue

        errors = validate_config(obj)
        if isinstance(obj, dict):
            rid = obj.get("role_id")
            if isinstance(rid, str) and rid:
                if rid in role_ids:
                    errors.append("duplicate role_id %r (also in %s)" % (rid, role_ids[rid]))
                else:
                    role_ids[rid] = name
            clusters = obj.get("clusters")
            if isinstance(clusters, list):
                for cluster in clusters:
                    if isinstance(cluster, dict):
                        cid = cluster.get("cluster_id")
                        if isinstance(cid, str) and cid:
                            if cid in cluster_ids:
                                errors.append("duplicate cluster_id %r (also in %s)" % (cid, cluster_ids[cid]))
                            else:
                                cluster_ids[cid] = name

        per_file.append((name, errors))

    for name, errors in per_file:
        if errors:
            print("[x] %s" % name)
            for e in errors:
                print("      - %s" % e)
        else:
            print("[ok] %s" % name)

    total = len(per_file)
    invalid = sum(1 for _, e in per_file if e)
    print()
    print("validated %d file(s): %d valid, %d invalid" % (total, total - invalid, invalid))
    return 0 if invalid == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
