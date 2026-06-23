"""Enterprise / internal-document RAG lane (separate from dataset_excel public-source lane)."""

from enterprise_docs.cross_doc_retriever import build_index_from_units, retrieve_for_plan
from enterprise_docs.doc_router import build_evidence_plan, route_documents
from enterprise_docs.ingest import ingest_tree, scan_documents
from enterprise_docs.models import AnswerMode, EvidencePlan, EvidenceUnit

__all__ = [
    "AnswerMode",
    "EvidencePlan",
    "EvidenceUnit",
    "build_evidence_plan",
    "build_index_from_units",
    "ingest_tree",
    "retrieve_for_plan",
    "route_documents",
    "scan_documents",
]
