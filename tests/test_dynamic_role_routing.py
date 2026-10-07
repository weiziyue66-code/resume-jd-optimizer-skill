#!/usr/bin/env python3
"""Regression checks for JD-driven role routing and dedicated role configs."""
from __future__ import annotations

import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
ROLE_DIR = ROOT / "references" / "role-configs"
SCORING = ROOT / "references" / "scoring.md"


class DynamicRoleRoutingTests(unittest.TestCase):
    def load_config(self, role_id: str) -> dict:
        with (ROLE_DIR / f"{role_id}.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_user_growth_has_distinctive_growth_chain(self):
        config = self.load_config("user_growth")
        cluster_ids = {item["cluster_id"] for item in config["clusters"]}
        self.assertTrue(
            {
                "user_growth.acquisition_conversion",
                "user_growth.activation_retention",
                "user_growth.experiment_funnel",
                "user_growth.referral_mechanism",
            }.issubset(cluster_ids)
        )

    def test_user_operations_separates_lifecycle_community_and_feedback(self):
        config = self.load_config("user_operations")
        cluster_ids = {item["cluster_id"] for item in config["clusters"]}
        self.assertTrue(
            {
                "user_operations.lifecycle_segmentation",
                "user_operations.community_engagement",
                "user_operations.service_feedback",
                "user_operations.retention_referral_ugc",
            }.issubset(cluster_ids)
        )

    def test_role_title_cannot_override_atomic_responsibilities(self):
        text = SCORING.read_text(encoding="utf-8")
        self.assertIn("岗位名称只用于候选配置召回", text)
        self.assertIn("不得覆盖原子要求、职责动作、交付物和业务结果形成的角色判断", text)

    def test_mixed_jd_can_route_to_growth_as_primary(self):
        text = SCORING.read_text(encoding="utf-8")
        self.assertIn("标题为用户运营但增长职责占主导", text)
        self.assertIn("user_growth` 作为主角色", text)

    def test_user_output_translates_internal_role_terms_to_capabilities(self):
        text = SCORING.read_text(encoding="utf-8")
        self.assertIn("对用户展示时，将主角色写为「核心能力」", text)
        self.assertIn("将相邻角色写为「辅助能力」", text)
        self.assertIn("内部角色 ID、计分和原子要求编号不进入普通用户输出", text)


if __name__ == "__main__":
    unittest.main()
