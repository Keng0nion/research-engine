-- Research Engine v2 storage schema (PART VI)
-- 源文档与衍生解读分表存放；不存任何凭据。

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,
    question      TEXT NOT NULL,
    mode          TEXT NOT NULL CHECK (mode IN ('quick','standard','deep','systematic')),
    status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','completed','aborted')),
    plan_json     TEXT,
    budget_json   TEXT,
    rounds_run    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    notes         TEXT
);

CREATE TABLE IF NOT EXISTS rounds (
    session_id    TEXT NOT NULL REFERENCES sessions(id),
    round         INTEGER NOT NULL,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    plan_json     TEXT,
    outcome       TEXT,
    PRIMARY KEY (session_id, round)
);

CREATE TABLE IF NOT EXISTS queries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT REFERENCES sessions(id),
    round         INTEGER NOT NULL DEFAULT 1,
    provider      TEXT NOT NULL,
    query_text    TEXT NOT NULL,
    params_json   TEXT,
    status        TEXT NOT NULL CHECK (status IN ('ok','error','timeout','rate_limited','skipped')),
    error         TEXT,
    result_count  INTEGER,
    latency_ms    INTEGER,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_queries_session ON queries(session_id);

-- 去重键：canonical_url 优先；无 URL 时用 doi:/arxiv:/pmid: 伪 URL
CREATE TABLE IF NOT EXISTS documents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url  TEXT UNIQUE,
    doi            TEXT,
    arxiv_id       TEXT,
    pmid           TEXT,
    title          TEXT,
    authors_json   TEXT,
    published_at   TEXT,
    platform       TEXT,
    doc_type       TEXT CHECK (doc_type IN ('paper','preprint','webpage','pdf','news','dataset','code','other') OR doc_type IS NULL),
    first_seen_at  TEXT NOT NULL,
    access_status  TEXT NOT NULL DEFAULT 'UNKNOWN',
    fulltext_path  TEXT,
    abstract       TEXT,
    metadata_json  TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_doi ON documents(doi);
CREATE INDEX IF NOT EXISTS idx_documents_arxiv ON documents(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_documents_pmid ON documents(pmid);

CREATE TABLE IF NOT EXISTS doc_hits (
    document_id   INTEGER NOT NULL REFERENCES documents(id),
    query_id      INTEGER NOT NULL REFERENCES queries(id),
    rank          INTEGER,
    snippet       TEXT,
    raw_json      TEXT,
    PRIMARY KEY (document_id, query_id)
);

-- 证据卡（MODULE 7）：草稿由引擎从元数据与摘录生成，认定字段由 Agent 复核填写
CREATE TABLE IF NOT EXISTS evidence (
    id             TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL REFERENCES sessions(id),
    document_id    INTEGER REFERENCES documents(id),
    status         TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','reviewed','rejected')),
    claim          TEXT,
    excerpt        TEXT,
    methodology    TEXT,
    dataset        TEXT,
    conditions     TEXT,
    numbers_json   TEXT,
    limitations    TEXT,
    authority      TEXT,
    relevance      TEXT,
    method_quality TEXT,
    recency        TEXT,
    citation_status TEXT NOT NULL DEFAULT 'unverified' CHECK (citation_status IN ('verified','unverified','suspect')),
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence(session_id);

-- 引文关系（MODULE 6）
CREATE TABLE IF NOT EXISTS citations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT REFERENCES sessions(id),
    citing_document_id INTEGER REFERENCES documents(id),
    cited_doi          TEXT,
    cited_title        TEXT,
    cited_year         INTEGER,
    relationship       TEXT NOT NULL CHECK (relationship IN ('cites','cited_by','related')),
    source_platform    TEXT,
    verified           INTEGER NOT NULL DEFAULT 0,
    created_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_citations_session ON citations(session_id);
CREATE INDEX IF NOT EXISTS idx_citations_doi ON citations(cited_doi);

-- 来源冲突（MODULE 8）
CREATE TABLE IF NOT EXISTS conflicts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT NOT NULL REFERENCES sessions(id),
    topic            TEXT NOT NULL,
    kind             TEXT NOT NULL CHECK (kind IN ('numbers','conditions','datasets','methods','definitions','conclusions','temporal')),
    description      TEXT NOT NULL,
    evidence_ids_json TEXT,
    status           TEXT NOT NULL DEFAULT 'unresolved' CHECK (status IN ('unresolved','explained','resolved')),
    created_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conflicts_session ON conflicts(session_id);

-- 抓取失败/受限记录（MODULE 5 透明化）
CREATE TABLE IF NOT EXISTS fetch_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER REFERENCES documents(id),
    url           TEXT NOT NULL,
    http_status   INTEGER,
    outcome       TEXT NOT NULL,   -- ok | pdf_ok | robots_blocked | login_required | http_error | too_large | extract_failed | network_error
    detail        TEXT,
    bytes         INTEGER,
    fetched_at    TEXT NOT NULL
);
