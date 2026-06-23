"""Dataset-excel extractive RAG rule system (baseline v5 freeze + generalization hardening)."""

from dataset_excel.constants import BASELINE_VERSION
from dataset_excel.family_router import infer_question_profile
from dataset_excel.profile import QuestionProfile
from dataset_excel.rule_registry import FAMILY_SPECS, RULE_INVENTORY, export_rule_inventory

__all__ = [
    "BASELINE_VERSION",
    "FAMILY_SPECS",
    "RULE_INVENTORY",
    "QuestionProfile",
    "export_rule_inventory",
    "infer_question_profile",
]
