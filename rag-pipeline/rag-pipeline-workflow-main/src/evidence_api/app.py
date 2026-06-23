from __future__ import annotations

import os
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader

from evidence_api.ingest_jobs import IngestJobStore
from evidence_api.schemas import (
    CompaniesResponse,
    CompanyListItem,
    CompanyNotIndexedError,
    HealthResponse,
    IngestJobResponse,
    IngestJobStatus,
    IngestRequest,
    RetrieveRequest,
    RetrieveResponse,
)
from evidence_api.service import CompanyNotIndexed, EvidenceRetrievalService
from evidence_api.staging_config import indexed_companies, list_registry_companies, load_staging_config

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="Staging API key (LANGGRAPH_API_KEY). /health khong can key.",
)
_job_store = IngestJobStore()
_service: Optional[EvidenceRetrievalService] = None


def get_service() -> EvidenceRetrievalService:
    global _service
    if _service is None:
        _service = EvidenceRetrievalService()
    return _service


def require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    expected = os.getenv("LANGGRAPH_API_KEY", "").strip()
    if not expected:
        return
    if not api_key or api_key != expected:
        raise HTTPException(status_code=401, detail="invalid_api_key")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Evidence Retrieval API",
        description=(
            "LangGraph staging — retrieval-only, rerank off, no GPU.\n\n"
            "**Test nhanh:** mo `/docs` → `GET /health` (khong can API key) "
            "→ nut **Authorize** nhap `X-API-Key` → `POST /retrieve`.\n\n"
            "Neu khong mo duoc URL: can cung LAN/VPN hoac dung tunnel (xem `docs/LANGGRAPH_API_HANDOFF.md`)."
        ),
        version="0.1.0",
        swagger_ui_parameters={"tryItOutEnabled": True, "persistAuthorization": True},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/companies", response_model=CompaniesResponse, tags=["public"])
    def companies() -> CompaniesResponse:
        """Danh sach company_id trong registry + trang thai index (khong can API key)."""
        cfg = get_service().config
        rows = list_registry_companies(cfg)
        items = [CompanyListItem(**row) for row in rows]
        indexed_count = sum(1 for x in items if x.indexed)
        return CompaniesResponse(items=items, count=len(items), indexed_count=indexed_count)

    @app.get("/health", response_model=HealthResponse, tags=["public"])
    def health() -> HealthResponse:
        """Khong can API key — dung de kiem tra server + index."""
        cfg = get_service().config
        ready, pending = indexed_companies(cfg)
        status = "ok" if ready else "degraded"
        stack = cfg.get("stack") or {}
        reranker = (stack.get("reranker") or "none").strip().lower()
        retrieval_mode = (stack.get("retrieval_mode") or "").strip()
        rerank_on = reranker not in ("none", "") or retrieval_mode.endswith("_rerank")
        return HealthResponse(
            status=status,
            mode=cfg.get("mode", "langgraph_staging"),
            rerank_enabled=rerank_on,
            gpu=False,
            index_version=cfg.get("api_id"),
            companies_indexed=ready,
            companies_pending=pending,
        )

    @app.post(
        "/retrieve",
        response_model=RetrieveResponse,
        responses={404: {"model": CompanyNotIndexedError}},
        tags=["retrieve"],
    )
    def retrieve(
        req: RetrieveRequest,
        _: None = Depends(require_api_key),
    ) -> RetrieveResponse:
        svc = get_service()
        if req.company_id not in svc.known_company_ids():
            raise HTTPException(
                status_code=404,
                detail=CompanyNotIndexedError(company_id=req.company_id).model_dump(),
            )
        try:
            return svc.retrieve(req)
        except CompanyNotIndexed:
            raise HTTPException(
                status_code=404,
                detail=CompanyNotIndexedError(company_id=req.company_id).model_dump(),
            )

    @app.post("/ingest", response_model=IngestJobResponse, tags=["admin"])
    def ingest(
        req: IngestRequest,
        background: BackgroundTasks,
        _: None = Depends(require_api_key),
    ) -> IngestJobResponse:
        svc = get_service()
        company_id = req.company_id.strip().lower()
        if company_id not in svc.known_company_ids():
            raise HTTPException(
                status_code=404,
                detail=CompanyNotIndexedError(company_id=company_id).model_dump(),
            )
        job = _job_store.create(company_id)
        background.add_task(_run_ingest_job, job.job_id, company_id)
        return IngestJobResponse(job_id=job.job_id, status="queued")

    @app.get("/ingest/{job_id}", response_model=IngestJobStatus, tags=["admin"])
    def ingest_status(job_id: str, _: None = Depends(require_api_key)) -> IngestJobStatus:
        job = _job_store.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job_not_found")
        return IngestJobStatus(
            job_id=job.job_id,
            status=job.status,
            company_id=job.company_id,
            message=job.message or None,
        )

    def _custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "ApiKeyAuth"
        ] = {"type": "apiKey", "in": "header", "name": "X-API-Key"}
        for path, methods in schema.get("paths", {}).items():
            if path in {"/health", "/companies", "/"}:
                continue
            for _method, op in methods.items():
                if isinstance(op, dict):
                    op["security"] = [{"ApiKeyAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = _custom_openapi
    return app


def _run_ingest_job(job_id: str, company_id: str) -> None:
    _job_store.update(job_id, status="running", message="building index")
    try:
        from evidence_api.env_bootstrap import load_repo_dotenv, sanitize_runtime_env
        from evidence_api.staging_config import apply_company_env, load_staging_config, reset_retrieval_runtime_caches
        from production_config import repo_root

        load_repo_dotenv()
        sanitize_runtime_env()
        cfg = load_staging_config()
        apply_company_env(cfg, company_id, base_dir=repo_root())
        reset_retrieval_runtime_caches()
        from rag_stack import ingest_corpus_files

        os.environ["RAG_FORCE_REBUILD"] = "true"
        ingest_corpus_files()
        os.environ.pop("RAG_FORCE_REBUILD", None)
        _job_store.update(job_id, status="completed", message="index_ready")
    except Exception as exc:
        _job_store.update(job_id, status="failed", message=str(exc)[:500])


app = create_app()
