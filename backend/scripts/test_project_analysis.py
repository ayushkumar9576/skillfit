"""
scripts/test_project_analysis.py
--------------------------------
Verification suite for Phase 3.7 — Project Analysis Engine.

Mock-only: NO network calls and NO real API key are required. The LLM boundary is
exercised through an injected ``FakeProvider`` (a :class:`BaseLLMProvider` that
returns a canned, fully-populated ``ProjectIntelligence`` payload in the **compact
wire format**), while the rest of the stack — the rule-based extractor, the real
``LLMService`` orchestration, the real shipped ``project_analysis`` prompt, the
Pydantic→dataclass reconstruction — runs for real. Async code is driven by
``asyncio.run`` ONLY here in the harness (via the sanctioned sync wrapper
``ProjectAnalysisEngine.analyze``); never inside the ``app`` package.

The canned payload deliberately mirrors what the prompt now asks a model for:

    - evidence cited as ``"ev": [7, 8]`` (line numbers), never re-quoted text;
    - ONE merged ``skills_and_tech`` array instead of ``technology_usage`` +
      ``skill_evidence``;
    - no ``max_score`` / ``confidence_level`` / ``source_section`` — the engine
      derives all three.

So these tests cover both directions: that the small wire validates, and that the
engine reconstructs the *full* ``ProjectIntelligenceReport`` from it.

Run from the ``backend`` directory:

    python scripts/test_project_analysis.py

Mirrors the standalone-script convention (errors[] / PASS-FAIL / sys.exit(1))
used by scripts/test_llm_integration.py.
"""

import json
import os
import sys
from dataclasses import asdict, is_dataclass

sys.path.insert(0, ".")

from app.analysis.engines.project_analysis_engine import (
    ANALYZER_NAME,
    DEFAULT_ANALYSIS_MAX_TOKENS,
    ProjectAnalysisEngine,
    _confidence_band,
    _context_adds_signal,
    _resolve_max_tokens,
)
from app.analysis.engines.project_schemas import (
    ProjectIntelligence,
    coerce_evidence_refs,
)
from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.project_models import ProjectIntelligenceReport
from app.services.llm.base import BaseLLMProvider, LLMCompletion
from app.services.llm.config import LLMSettings
from app.services.llm.exceptions import LLMProviderError, LLMResponseError
from app.services.llm.prompt_manager import default_prompt_manager
from app.services.llm.schemas import LLMUsage, _repair_truncated_json, validate_response
from app.services.llm.service import LLMService
from app.services.resume.project_extractor import (
    RuleBasedProjectExtractor,
    extract_projects_from_text,
    get_project_extractor,
)

errors = []


def check(label, cond, detail=""):
    ok = bool(cond)
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        errors.append(f"{label}: {detail}" if detail else label)


def expect_raises(label, exc_type, thunk):
    """Assert that calling ``thunk()`` raises ``exc_type`` (or a subclass)."""
    try:
        thunk()
    except exc_type:
        print(f"PASS  {label}")
    except Exception as exc:  # wrong exception type
        print(f"FAIL  {label}")
        errors.append(
            f"{label}: expected {exc_type.__name__}, got {type(exc).__name__}: {exc}"
        )
    else:  # nothing raised
        print(f"FAIL  {label}")
        errors.append(f"{label}: expected {exc_type.__name__}, nothing raised")


# ---------------------------------------------------------------------------
# Sample resume fixtures (raw text — blank lines are meaningful boundaries).
# ---------------------------------------------------------------------------

MULTI_PROJECT_RESUME = """John Doe
Bangalore, India

PROJECTS

Distributed Task Queue
- Built a high-throughput task scheduler processing 10k tasks/sec
- Ensured zero data loss with write-ahead logging
Technologies: Go, Redis, Docker
https://github.com/example/queue

Real-Time Chat Application
- Implemented WebSocket messaging with presence tracking
Technologies: Node.js, Socket.IO, PostgreSQL

SKILLS
Python, Go, JavaScript
"""

TITLE_ONLY_RESUME = """PROJECTS

Portfolio Website

SKILLS
HTML, CSS
"""

NO_PROJECTS_RESUME = """EDUCATION
B.Tech in Computer Science

SKILLS
Python
"""

#: Line numbers the extractor assigns to project #0 of MULTI_PROJECT_RESUME
#: (title, bullet, bullet, Technologies:, URL). Asserted in section 1, so a change
#: in the extractor surfaces there rather than as a confusing mapping failure.
PROJECT0_LINES = (6, 7, 8, 9, 10)


# ---------------------------------------------------------------------------
# Canned LLM payload — the COMPACT WIRE shape.
#
# Every scored object carries a NON-EMPTY "ev" array of line numbers, so the
# mandatory evidence-traceability contract can be asserted after the engine
# rehydrates them. Note what is deliberately ABSENT: max_score, confidence_level,
# source_section, quoted evidence text, technology_usage, and the four
# skill_evidence lists — all reconstructed by the engine.
# ---------------------------------------------------------------------------


def canned_intelligence(lines=PROJECT0_LINES):
    """
    A fresh, fully-populated ``ProjectIntelligence`` wire dict on each call.

    ``lines`` are the evidence line numbers actually available for the project
    being analyzed — a real model can only cite lines it was given, so the fake
    provider passes through the ones from its own payload. Refs are picked
    modulo the list length, so the payload stays valid for a one-line project too.
    """
    available = [n for n in lines] or list(PROJECT0_LINES)

    def ref(*positions):
        return [available[p % len(available)] for p in positions]

    def scored(label, score=70.0, conf=0.8, at=(1,)):
        return {
            "score": score,
            "confidence": conf,
            "reasoning": f"{label} reasoning grounded in cited evidence.",
            "ev": ref(*at),
        }

    return {
        "understanding": {
            "purpose": "Process asynchronous jobs at scale.",
            "problem_solved": "Reliable task delivery with no data loss.",
            "intended_users": "Backend services.",
            "domain": "Distributed systems.",
            "project_type": "backend service",
            "business_value": "Improves throughput.",
            "confidence": 0.8,
            "ev": ref(0, 1),
        },
        "architecture": [
            {
                "area": "backend",
                "assessment": "Queue-based worker architecture with a write-ahead log.",
                "score": 72.0,
                "confidence": 0.8,
                "ev": ref(2),
            }
        ],
        "complexity": {
            "overall": scored("overall"),
            "backend": scored("backend"),
            # A facet the evidence does not support is OMITTED, not padded with a
            # placeholder: "frontend" and "deployment" are absent on purpose and
            # must map to score 0 / cannot_verify.
            "database": scored("database"),
            "system_design": scored("system_design", at=(1, 2)),
            "integration": scored("integration"),
        },
        "engineering_depth": scored("engineering_depth", at=(1, 2)),
        "skills_and_tech": [
            {
                # Explicit kind="tech" -> routed to technology_usage for EVERY
                # project, regardless of that project's technology list.
                "name": "Go",
                "kind": "tech",
                "depth": 68.0,
                "status": "demonstrated",
                "sophistication": "moderate",
                "understanding": "Concurrency primitives applied to a scheduler core.",
                "confidence": 0.75,
                "reasoning": "Go named alongside the throughput figure it delivers.",
                "ev": ref(1),
            },
            {
                # No kind -> inferred by matching the project's extracted tech list.
                "name": "Redis",
                "depth": 40.0,
                "status": "claimed",
                "sophistication": "shallow",
                "understanding": "Listed but no usage described.",
                "confidence": 0.35,
                "reasoning": "Named in the technology line only.",
                "ev": ref(3),
            },
            {
                # kind="skill" -> skill_evidence only, never technology_usage.
                "name": "REST API design",
                "kind": "skill",
                "depth": 55.0,
                "status": "verified",
                "sophistication": "moderate",
                "understanding": "Interface boundaries described concretely.",
                "confidence": 0.8,
                "reasoning": "Interface behaviour is described, not just named.",
                "ev": ref(1),
            },
            {
                "name": "Observability",
                "kind": "skill",
                "depth": 0.0,
                "status": "unverified",
                "confidence": 0.0,
                "reasoning": "No metrics, logging, or tracing described.",
                "ev": ref(0),
            },
        ],
        "competencies": [
            {
                "name": "Concurrency",
                "score": 70.0,
                "confidence": 0.75,
                "reasoning": "Demonstrated via a concrete throughput figure.",
                "ev": ref(1),
            }
        ],
        "industry_relevance": scored("industry_relevance"),
        "technical_maturity": {
            "classification": "portfolio",
            "score": 60.0,
            "confidence": 0.7,
            "reasoning": "Durability handled, but no deployment or test evidence.",
            "ev": ref(0, 2),
        },
        "evidence_strength": scored("evidence_strength"),
        "hiring_signal": scored("hiring_signal", score=64.0, conf=0.7, at=(1, 2)),
        "strengths": [
            {
                "statement": "Strong concurrency handling.",
                "reasoning": "A specific throughput figure is cited.",
                "confidence": 0.75,
                "ev": ref(1),
            }
        ],
        "weaknesses": [
            {
                "statement": "Durability claim rests on one line.",
                "reasoning": "Write-ahead logging is named without mechanism.",
                "confidence": 0.6,
                "ev": ref(2),
            }
        ],
        "missing_evidence": [
            {
                "aspect": "testing",
                "description": "No tests, coverage, or CI described anywhere.",
                "impact": "Lowers confidence in the reliability claims.",
            },
            {
                "aspect": "deployment",
                "description": "No hosting, container orchestration, or release process.",
                "impact": "Production-readiness cannot be assessed.",
            },
        ],
        "risks": [
            {
                "statement": "Unverified scalability claim.",
                "reasoning": "The throughput figure is not independently supported.",
                "confidence": 0.5,
                "ev": ref(1),
            }
        ],
        "executive_assessment": {
            "overall_impression": "Competent backend project with real durability thinking.",
            "demonstrates": ["Concurrency", "Reliability design"],
            "does_not_demonstrate": ["Testing", "Deployment"],
            "strongest_signals": ["Throughput handling"],
            "weakest_signals": ["No tests"],
            "overall_confidence": 0.72,
        },
        "overall_confidence": 0.72,
        "caveats": ["Assessment limited to resume evidence."],
    }


# ---------------------------------------------------------------------------
# Fake provider (no network / no key). Captures the per-call kwargs so the
# provider-agnostic model contract and max_tokens precedence can be verified,
# and keys the captured payloads by project title so assertions do not depend
# on asyncio.gather scheduling order.
# ---------------------------------------------------------------------------


class FakeProvider(BaseLLMProvider):
    def __init__(self, payload_factory=None):
        self.calls = 0
        self.last_model = "UNSET"
        self.last_max_tokens = "UNSET"
        self.last_temperature = "UNSET"
        self.last_system_prompt = None
        self.last_user_content = None
        self.payloads = {}  # project_title -> parsed request payload
        self._payload_factory = payload_factory

    async def complete_structured(
        self,
        *,
        system_prompt,
        user_content,
        response_schema,
        model=None,
        temperature=0.0,
        max_tokens=None,
        timeout=None,
    ):
        self.calls += 1
        self.last_model = model
        self.last_max_tokens = max_tokens
        self.last_temperature = temperature
        self.last_system_prompt = system_prompt
        self.last_user_content = user_content

        request = json.loads(user_content)
        self.payloads[request.get("project_title")] = request

        if self._payload_factory is not None:
            data = self._payload_factory()
        else:
            # Cite only lines this project actually supplied, as a real model must.
            lines = [
                e["line"]
                for e in request.get("evidence", [])
                if isinstance(e.get("line"), int)
            ]
            data = canned_intelligence(lines or PROJECT0_LINES)

        parsed = response_schema.model_validate(data)
        usage = LLMUsage(
            provider="fakeprov",
            model="fake-model-1",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        return LLMCompletion(
            parsed=parsed,
            raw_text="{}",
            usage=usage,
            provider="fakeprov",
            model="fake-model-1",
        )


class FlakyByTitleProvider(FakeProvider):
    """Raises for any project whose payload mentions ``fail_marker``."""

    def __init__(self, fail_marker):
        super().__init__()
        self._fail_marker = fail_marker

    async def complete_structured(
        self, *, system_prompt, user_content, response_schema, **kwargs
    ):
        if self._fail_marker in user_content:
            self.calls += 1
            raise LLMProviderError("simulated provider failure", transient=False)
        return await super().complete_structured(
            system_prompt=system_prompt,
            user_content=user_content,
            response_schema=response_schema,
            **kwargs,
        )


def make_service(provider, settings=None):
    """Build a real LLMService over an injected provider + the REAL prompts."""
    return LLMService(provider=provider, settings=settings or LLMSettings())


def _collect_scored_evidence(report):
    """Every scored element that MUST carry traceable evidence -> (label, list)."""
    pairs = [
        ("understanding", report.understanding.evidence),
        ("engineering_depth", report.engineering_depth.evidence),
        ("industry_relevance", report.industry_relevance.evidence),
        ("technical_maturity", report.technical_maturity.evidence),
        ("evidence_strength", report.evidence_strength.evidence),
        ("hiring_signal", report.hiring_signal.evidence),
    ]
    c = report.complexity
    # frontend/deployment are omitted by the canned payload on purpose (the
    # omission-as-signal rule), so they are excluded from the must-cite set.
    for facet in ("overall", "backend", "database", "system_design", "integration"):
        pairs.append((f"complexity.{facet}", getattr(c, facet).evidence))
    for i, a in enumerate(report.architecture):
        pairs.append((f"architecture[{i}]", a.evidence))
    for i, t in enumerate(report.technology_usage):
        pairs.append((f"technology_usage[{i}]", t.evidence))
    for i, comp in enumerate(report.competencies):
        pairs.append((f"competencies[{i}]", comp.evidence))
    for i, it in enumerate(report.skill_evidence.items):
        pairs.append((f"skill_evidence.items[{i}]", it.evidence))
    for i, s in enumerate(report.strengths):
        pairs.append((f"strengths[{i}]", s.evidence))
    for i, w in enumerate(report.weaknesses):
        pairs.append((f"weaknesses[{i}]", w.evidence))
    for i, r in enumerate(report.risks):
        pairs.append((f"risks[{i}]", r.evidence))
    return pairs


# ---------------------------------------------------------------------------
print("\n--- 1. RuleBasedProjectExtractor: multi-project segmentation ---")

extractor = get_project_extractor("rule_based")
check("factory returns RuleBasedProjectExtractor",
      isinstance(extractor, RuleBasedProjectExtractor))

res = extractor.extract(MULTI_PROJECT_RESUME)
check("multi: two projects extracted",
      res.total_projects_count == 2 and len(res.projects) == 2,
      detail=f"count={res.total_projects_count} projects={[p.title for p in res.projects]}")
check("multi: extraction leaves reports empty (engine fills later)",
      res.reports == [])

p0 = res.projects[0] if res.projects else None
p1 = res.projects[1] if len(res.projects) > 1 else None

check("multi: project 0 title parsed",
      p0 is not None and p0.title == "Distributed Task Queue",
      detail=repr(getattr(p0, "title", None)))
check("multi: project 0 technologies parsed",
      p0 is not None and p0.technologies == ["Go", "Redis", "Docker"],
      detail=repr(getattr(p0, "technologies", None)))
check("multi: project 0 highlights parsed (2 bullets)",
      p0 is not None and len(p0.highlights) == 2 and p0.highlights[0].startswith("Built"),
      detail=repr(getattr(p0, "highlights", None)))
check("multi: project 0 URL parsed",
      p0 is not None and p0.project_url == "https://github.com/example/queue",
      detail=repr(getattr(p0, "project_url", None)))
check("multi: project 0 full-evidence confidence == 1.0",
      p0 is not None and p0.confidence == 1.0,
      detail=repr(getattr(p0, "confidence", None)))
check("multi: project 1 title parsed",
      p1 is not None and p1.title == "Real-Time Chat Application",
      detail=repr(getattr(p1, "title", None)))
check("multi: project 1 technologies parsed",
      p1 is not None and p1.technologies == ["Node.js", "Socket.IO", "PostgreSQL"],
      detail=repr(getattr(p1, "technologies", None)))

# Evidence traceability at extraction time.
ev_ok = (
    p0 is not None
    and len(p0.evidences) > 0
    and all(isinstance(e, AnalysisEvidence) for e in p0.evidences)
    and all(e.source_section == "projects" for e in p0.evidences)
    and all(e.line_number is not None for e in p0.evidences)
)
check("multi: every extracted evidence has section + line number", ev_ok)

# The whole citation-by-reference scheme rests on these line numbers, so pin them.
check("multi: project 0 line numbers are the expected spine",
      p0 is not None
      and tuple(e.line_number for e in p0.evidences) == PROJECT0_LINES,
      detail=repr([e.line_number for e in p0.evidences] if p0 else None))

# Convenience wrapper agrees.
res_conv = extract_projects_from_text(MULTI_PROJECT_RESUME)
check("extract_projects_from_text agrees on count",
      res_conv.total_projects_count == 2)

expect_raises(
    "factory: unknown extractor type -> ValueError",
    ValueError,
    lambda: get_project_extractor("bogus"),
)


# ---------------------------------------------------------------------------
print("\n--- 2. Extractor: title-only and empty-section handling ---")

res_title = extractor.extract(TITLE_ONLY_RESUME)
check("title-only: one project extracted",
      res_title.total_projects_count == 1 and len(res_title.projects) == 1,
      detail=f"count={res_title.total_projects_count}")
check("title-only: title parsed",
      res_title.projects and res_title.projects[0].title == "Portfolio Website",
      detail=repr([p.title for p in res_title.projects]))
check("title-only: no highlights / tech / url",
      res_title.projects
      and not res_title.projects[0].highlights
      and not res_title.projects[0].technologies
      and res_title.projects[0].project_url is None)
check("title-only: lower confidence for a bare title",
      res_title.projects and res_title.projects[0].confidence <= 0.5,
      detail=repr(res_title.projects[0].confidence if res_title.projects else None))

res_none = extractor.extract(NO_PROJECTS_RESUME)
check("no-projects-section: empty result",
      res_none.total_projects_count == 0 and res_none.projects == [] and res_none.reports == [])

res_empty = extractor.extract("")
check("empty string: empty result",
      res_empty.total_projects_count == 0 and res_empty.projects == [])


# ---------------------------------------------------------------------------
print("\n--- 3. _resolve_max_tokens precedence (explicit > env > default) ---")

os.environ.pop("LLM_MAX_TOKENS", None)
check("resolve: default is 8000 when unset",
      _resolve_max_tokens(None) == DEFAULT_ANALYSIS_MAX_TOKENS == 8000,
      detail=str(_resolve_max_tokens(None)))
check("resolve: explicit arg wins when env unset",
      _resolve_max_tokens(555) == 555)

os.environ["LLM_MAX_TOKENS"] = "1234"
check("resolve: env used when no explicit arg",
      _resolve_max_tokens(None) == 1234)
check("resolve: explicit arg still overrides env",
      _resolve_max_tokens(999) == 999)

os.environ["LLM_MAX_TOKENS"] = "not-a-number"
check("resolve: malformed env falls back to default",
      _resolve_max_tokens(None) == DEFAULT_ANALYSIS_MAX_TOKENS)
os.environ["LLM_MAX_TOKENS"] = "0"
check("resolve: non-positive env (0) falls back to default",
      _resolve_max_tokens(None) == DEFAULT_ANALYSIS_MAX_TOKENS)
os.environ["LLM_MAX_TOKENS"] = "-5"
check("resolve: negative env falls back to default",
      _resolve_max_tokens(None) == DEFAULT_ANALYSIS_MAX_TOKENS)
os.environ.pop("LLM_MAX_TOKENS", None)


# ---------------------------------------------------------------------------
print("\n--- 4. Engine end-to-end: compact wire -> ProjectIntelligenceReport ---")

os.environ.pop("LLM_MAX_TOKENS", None)  # deterministic 8000 default
fake = FakeProvider()
service = make_service(fake)
engine = ProjectAnalysisEngine(llm_service=service)  # model=None (agnostic)

result = engine.analyze(resume_id="resume-e2e", raw_text=MULTI_PROJECT_RESUME)

check("engine: analyzer name is 'project'", ANALYZER_NAME == "project")
check("engine: two provider calls (one per project)", fake.calls == 2,
      detail=f"calls={fake.calls}")
check("engine: two reports generated", len(result.reports) == 2,
      detail=f"reports={len(result.reports)}")
check("engine: extraction count preserved on result",
      result.total_projects_count == 2)

report0 = result.reports[0] if result.reports else None
check("engine: report is a ProjectIntelligenceReport",
      isinstance(report0, ProjectIntelligenceReport))
check("engine: report linked to its source project (title + object)",
      report0 is not None
      and report0.project_title == "Distributed Task Queue"
      and report0.source_project is result.projects[0])
check("engine: second report linked to second project",
      len(result.reports) > 1
      and result.reports[1].project_title == "Real-Time Chat Application")

# Mapped scalar fields.
check("map: complexity.overall.score",
      report0 is not None and report0.complexity.overall.score == 70.0,
      detail=repr(report0.complexity.overall.score if report0 else None))
check("map: 7 complexity facets present + named by the engine",
      report0 is not None
      and report0.complexity.overall.name == "overall"
      and report0.complexity.deployment.name == "deployment")
check("map: engineering_depth is a scored dimension",
      report0 is not None and report0.engineering_depth.score == 70.0)
check("map: technical_maturity classification kept verbatim (string)",
      report0 is not None and report0.technical_maturity.classification == "portfolio")
check("map: hiring_signal named + scored (NOT a placement score)",
      report0 is not None
      and report0.hiring_signal.name == "hiring_signal"
      and report0.hiring_signal.score == 64.0)
check("map: executive_assessment mapped",
      report0 is not None
      and report0.executive_assessment.overall_impression.startswith("Competent backend project")
      and report0.executive_assessment.demonstrates == ["Concurrency", "Reliability design"])
check("map: understanding mapped",
      report0 is not None
      and report0.understanding.purpose == "Process asynchronous jobs at scale.")
check("map: missing_evidence mapped (the ONE place absences are recorded)",
      report0 is not None
      and [m.aspect for m in report0.missing_evidence] == ["testing", "deployment"],
      detail=repr([m.aspect for m in report0.missing_evidence] if report0 else None))
check("map: overall confidence + caveats mapped",
      report0 is not None
      and report0.overall_confidence == 0.72
      and report0.caveats == ["Assessment limited to resume evidence."])

# Provider-agnostic model + generous token budget were honored on the call.
check("engine: model passed to provider is None (provider-agnostic)",
      fake.last_model is None, detail=repr(fake.last_model))
check("engine: default max_tokens forwarded to provider is 8000",
      fake.last_max_tokens == 8000, detail=repr(fake.last_max_tokens))
check("engine: temperature forwarded is 0.0 (deterministic)",
      fake.last_temperature == 0.0, detail=repr(fake.last_temperature))

# The REAL shipped prompt was rendered with the schema name and reached provider.
check("engine: rendered system prompt names the response schema",
      fake.last_system_prompt is not None
      and "ProjectIntelligence" in fake.last_system_prompt)


# ---------------------------------------------------------------------------
print("\n--- 5. Request payload is line-indexed and free of duplication ---")

payload0 = fake.payloads.get("Distributed Task Queue", {})
payload1 = fake.payloads.get("Real-Time Chat Application", {})

check("payload: both projects captured by title (order-independent)",
      bool(payload0) and bool(payload1),
      detail=repr(sorted(fake.payloads)))
check("payload: 'evidence' is the line-numbered spine",
      [e.get("line") for e in payload0.get("evidence", [])] == list(PROJECT0_LINES),
      detail=repr(payload0.get("evidence")))
check("payload: every evidence entry carries its text",
      payload0.get("evidence")
      and all(e.get("text") for e in payload0["evidence"]))
check("payload: bullets flagged by line, not re-sent as text",
      payload0.get("highlight_lines") == [7, 8]
      and "highlights" not in payload0
      and "description" not in payload0,
      detail=repr({k: payload0.get(k) for k in ("highlight_lines", "highlights", "description")}))
check("payload: redundant bullet 'context' omitted (differs only by '- ')",
      payload0.get("evidence")
      and not any("context" in e for e in payload0["evidence"]),
      detail=repr([e for e in payload0.get("evidence", []) if "context" in e]))
check("payload: absent optional fields not sent as nulls",
      "role" not in payload1 and "project_url" not in payload1,
      detail=repr(sorted(payload1)))
check("payload: project_url sent when the extractor found one",
      payload0.get("project_url") == "https://github.com/example/queue")

check("_context_adds_signal: bullet-marker-only difference is not signal",
      _context_adds_signal("Built an API", "- Built an API") is False)
check("_context_adds_signal: identical text is not signal",
      _context_adds_signal("Built an API", "Built an API") is False)
check("_context_adds_signal: genuinely wider context IS signal",
      _context_adds_signal("Built an API", "Backend: Built an API in FastAPI") is True)
check("_context_adds_signal: empty context is not signal",
      _context_adds_signal("Built an API", "") is False)


# ---------------------------------------------------------------------------
print("\n--- 6. Evidence rehydration from line references ---")

u_ev = report0.understanding.evidence if report0 else []
line6 = p0.evidences[0]
line7 = p0.evidences[1]

check("rehydrate: 'ev': [6, 7] became two AnalysisEvidence records",
      len(u_ev) == 2 and all(isinstance(e, AnalysisEvidence) for e in u_ev),
      detail=repr(u_ev))
check("rehydrate: text restored VERBATIM from the extractor (not the model)",
      len(u_ev) == 2
      and u_ev[0].evidence_text == line6.evidence_text
      and u_ev[1].evidence_text == line7.evidence_text,
      detail=repr([e.evidence_text for e in u_ev]))
check("rehydrate: line_number populated (was empty in the old inlined format)",
      len(u_ev) == 2 and [e.line_number for e in u_ev] == [6, 7],
      detail=repr([e.line_number for e in u_ev]))
check("rehydrate: context_snippet populated from the extractor's record",
      len(u_ev) == 2 and u_ev[1].context_snippet == line7.context_snippet,
      detail=repr(u_ev[1].context_snippet if len(u_ev) == 2 else None))
check("rehydrate: source_section derived, not transmitted",
      all(e.source_section == "projects" for e in u_ev))
check("rehydrate: extraction confidence carried over",
      len(u_ev) == 2 and u_ev[0].confidence == line6.confidence,
      detail=repr([e.confidence for e in u_ev]))
check("rehydrate: independent instances per finding (no shared mutable state)",
      report0 is not None
      and report0.understanding.evidence[1] is not report0.hiring_signal.evidence[0])

# Report #1 cites its OWN lines (12-14) — proof the index is per-project.
report1 = result.reports[1] if len(result.reports) > 1 else None
check("rehydrate: project 1 resolved against its own line index",
      report1 is not None
      and [e.line_number for e in report1.understanding.evidence] == [12, 13],
      detail=repr([e.line_number for e in report1.understanding.evidence] if report1 else None))

# Direct unit coverage of the resolver's edge cases.
index0 = ProjectAnalysisEngine._build_line_index(p0)
eng = ProjectAnalysisEngine(llm_service=service)

check("_build_line_index: keyed by every extracted line",
      sorted(index0) == list(PROJECT0_LINES), detail=repr(sorted(index0)))

resolved_mixed = eng._resolve_refs([7, 999, 8], index0, 0.5)
check("resolve: unresolvable line ref is dropped, siblings survive",
      [e.line_number for e in resolved_mixed] == [7, 8],
      detail=repr([e.line_number for e in resolved_mixed]))

resolved_dupes = eng._resolve_refs([7, 7, 7], index0, 0.5)
check("resolve: duplicate refs collapse to one record",
      len(resolved_dupes) == 1, detail=repr(len(resolved_dupes)))

resolved_quote = eng._resolve_refs(["Built a REST API by hand"], index0, 0.42)
check("resolve: bare quote string kept verbatim as a fallback",
      len(resolved_quote) == 1
      and resolved_quote[0].evidence_text == "Built a REST API by hand"
      and resolved_quote[0].line_number is None
      and resolved_quote[0].confidence == 0.42,
      detail=repr(resolved_quote))
check("resolve: empty ref list yields no evidence",
      eng._resolve_refs([], index0, 0.5) == [])

# The tolerant coercion layer that feeds the resolver.
check("coerce: int / numeric string / {'line': n} all become line refs",
      coerce_evidence_refs([4, "5", {"line": 6}, {"line_number": "7"}]) == [4, 5, 6, 7],
      detail=repr(coerce_evidence_refs([4, "5", {"line": 6}, {"line_number": "7"}])))
check("coerce: legacy quote object and bare quote become text refs",
      coerce_evidence_refs([{"text": "Built an API"}, "Shipped it"])
      == ["Built an API", "Shipped it"])
check("coerce: a single unwrapped ref is promoted to a list",
      coerce_evidence_refs(4) == [4] and coerce_evidence_refs("4") == [4])
check("coerce: None / bools / empties are dropped, never raised",
      coerce_evidence_refs(None) == []
      and coerce_evidence_refs([True, False, "", "   ", {}]) == [])


# ---------------------------------------------------------------------------
print("\n--- 7. Derived fields: max_score, confidence_level, omission ---")

check("_confidence_band: 0.0 -> cannot_verify",
      _confidence_band(0.0) == "cannot_verify")
check("_confidence_band: 0.2 -> uncertain",
      _confidence_band(0.2) == "uncertain")
check("_confidence_band: 0.40 boundary -> likely",
      _confidence_band(0.40) == "likely" and _confidence_band(0.74) == "likely")
check("_confidence_band: 0.75 boundary -> verified",
      _confidence_band(0.75) == "verified" and _confidence_band(1.0) == "verified")

scored_objs = [
    ("complexity.overall", report0.complexity.overall),
    ("engineering_depth", report0.engineering_depth),
    ("industry_relevance", report0.industry_relevance),
    ("technical_maturity", report0.technical_maturity),
    ("evidence_strength", report0.evidence_strength),
    ("hiring_signal", report0.hiring_signal),
    ("architecture[0]", report0.architecture[0]),
    ("competencies[0]", report0.competencies[0]),
]
bad_max = [label for label, obj in scored_objs if obj.max_score != 100.0]
check("derive: max_score == 100.0 supplied on every scored object",
      not bad_max, detail=f"wrong max_score on: {bad_max}")

check("derive: confidence_level matches the band of confidence",
      all(obj.confidence_level == _confidence_band(obj.confidence)
          for _, obj in scored_objs),
      detail=repr([(l, o.confidence, o.confidence_level) for l, o in scored_objs]))
check("derive: overall_confidence_level derived from overall_confidence",
      report0.overall_confidence_level == "likely",
      detail=repr(report0.overall_confidence_level))
check("derive: executive_assessment confidence_level derived",
      report0.executive_assessment.confidence_level == "likely",
      detail=repr(report0.executive_assessment.confidence_level))

# Omission-as-signal: the canned payload leaves out frontend + deployment.
check("omission: an omitted complexity facet maps to score 0",
      report0.complexity.frontend.score == 0.0
      and report0.complexity.deployment.score == 0.0)
check("omission: an omitted facet maps to cannot_verify (no placeholder prose)",
      report0.complexity.frontend.confidence_level == "cannot_verify"
      and report0.complexity.deployment.confidence_level == "cannot_verify"
      and report0.complexity.frontend.reasoning == ""
      and report0.complexity.frontend.evidence == [],
      detail=repr(report0.complexity.frontend))
check("omission: the facet still exists and is named (report shape unchanged)",
      report0.complexity.frontend.name == "frontend"
      and report0.complexity.frontend.max_score == 100.0)


# ---------------------------------------------------------------------------
print("\n--- 8. skills_and_tech fan-out into BOTH report views ---")

se = report0.skill_evidence
tu = report0.technology_usage

check("fan-out: every wire entry became a skill_evidence item",
      [i.skill for i in se.items] == ["Go", "Redis", "REST API design", "Observability"],
      detail=repr([i.skill for i in se.items]))
check("fan-out: the four status lists are grouped from items[].status",
      se.demonstrated == ["Go"]
      and se.claimed == ["Redis"]
      and se.verified == ["REST API design"]
      and se.unverified == ["Observability"],
      detail=repr((se.claimed, se.demonstrated, se.verified, se.unverified)))
check("fan-out: kind='tech' routed to technology_usage",
      "Go" in [t.technology for t in tu], detail=repr([t.technology for t in tu]))
check("fan-out: missing kind inferred from the project's technology list",
      "Redis" in [t.technology for t in tu], detail=repr([t.technology for t in tu]))
check("fan-out: kind='skill' never reaches technology_usage",
      "REST API design" not in [t.technology for t in tu]
      and "Observability" not in [t.technology for t in tu],
      detail=repr([t.technology for t in tu]))
check("fan-out: technology_usage carries the depth facet",
      tu and tu[0].technology == "Go"
      and tu[0].usage_depth_score == 68.0
      and tu[0].sophistication == "moderate"
      and tu[0].demonstrated_understanding.startswith("Concurrency primitives"),
      detail=repr(tu[0] if tu else None))
check("fan-out: skill_evidence item carries the verification facet",
      se.items and se.items[0].skill == "Go"
      and se.items[0].status == "demonstrated"
      and se.items[0].confidence == 0.75)
check("fan-out: both views cite the same line but hold separate instances",
      tu and se.items
      and [e.line_number for e in tu[0].evidence] == [e.line_number for e in se.items[0].evidence]
      and tu[0].evidence[0] is not se.items[0].evidence[0])

# Project 1's technology list does NOT contain Redis, so inference must exclude it
# there while the explicit kind="tech" on Go still applies.
tu1 = report1.technology_usage if report1 else []
check("fan-out: inference is per-project (Redis absent for project 1)",
      [t.technology for t in tu1] == ["Go"],
      detail=repr([t.technology for t in tu1]))
check("fan-out: project 1 still keeps all four skills",
      report1 is not None and len(report1.skill_evidence.items) == 4)


# ---------------------------------------------------------------------------
print("\n--- 9. Mandatory evidence traceability (every scored element) ---")

pairs = _collect_scored_evidence(report0)
missing = [label for label, evs in pairs if not evs]
check("traceability: every scored element carries non-empty evidence",
      not missing, detail=f"missing evidence on: {missing}")

flat = [e for _, evs in pairs for e in evs]
check("traceability: all evidence entries are AnalysisEvidence with text",
      len(flat) > 0
      and all(isinstance(e, AnalysisEvidence) and e.evidence_text for e in flat),
      detail=f"n={len(flat)}")
check("traceability: every rehydrated entry is anchored to a real resume line",
      all(e.line_number in PROJECT0_LINES for e in flat),
      detail=repr(sorted({e.line_number for e in flat})))

pairs1 = _collect_scored_evidence(report1) if report1 else []
missing1 = [label for label, evs in pairs1 if not evs]
check("traceability: holds for project 1 as well",
      pairs1 and not missing1, detail=f"missing evidence on: {missing1}")


# ---------------------------------------------------------------------------
print("\n--- 10. Output-token budget guard (the point of the compact wire) ---")

wire_bytes = len(json.dumps(canned_intelligence()))
#: Ceiling for the canned wire payload. Deliberately close to the current size so
#: a schema addition that re-inflates the response fails HERE rather than as a
#: truncated response in production. Raise it consciously, not reflexively.
WIRE_BYTE_CEILING = 4500
check(f"budget: canned wire payload is {wire_bytes} bytes (<= {WIRE_BYTE_CEILING})",
      wire_bytes <= WIRE_BYTE_CEILING,
      detail=f"{wire_bytes} > {WIRE_BYTE_CEILING} — output grew; see docs §3a")

# Evidence must never be re-quoted on the wire: that was the original blowup.
wire_text = json.dumps(canned_intelligence())
check("budget: wire carries no 'source_section' (derived server-side)",
      "source_section" not in wire_text)
check("budget: wire carries no 'max_score' (constant 100.0)",
      "max_score" not in wire_text)
check("budget: wire carries no 'confidence_level' (band of confidence)",
      "confidence_level" not in wire_text)
check("budget: wire carries no separate 'technology_usage' / 'skill_evidence'",
      "technology_usage" not in wire_text and "skill_evidence" not in wire_text)

check("budget: request payload stays compact too",
      len(json.dumps(payload0)) < 700,
      detail=f"{len(json.dumps(payload0))} bytes")


# ---------------------------------------------------------------------------
print("\n--- 11. Truncated-response salvage (_repair_truncated_json) ---")

full_json = json.dumps(canned_intelligence())

# Cut the response at every offset and confirm each one either salvages into a
# valid ProjectIntelligence or is honestly rejected — never a crash.
salvaged = 0
unsalvageable = []
for cut in range(1, len(full_json)):
    fragment = full_json[:cut]
    try:
        json.loads(fragment)
        continue  # a complete prefix (rare) needs no repair
    except json.JSONDecodeError:
        pass
    repaired = _repair_truncated_json(fragment)
    if repaired is None:
        continue  # nothing salvageable this early — acceptable
    try:
        ProjectIntelligence.model_validate(json.loads(repaired))
        salvaged += 1
    except Exception as exc:  # noqa: BLE001
        unsalvageable.append((cut, type(exc).__name__))

check("salvage: every repairable cut point yields a valid ProjectIntelligence",
      not unsalvageable,
      detail=f"{len(unsalvageable)} bad cut(s), first: {unsalvageable[:3]}")
check(f"salvage: {salvaged} cut points recovered across the payload",
      salvaged > len(full_json) // 4, detail=f"salvaged={salvaged}")

# Graceful degradation: fields completed before the cut survive intact.
half_cut = full_json[: full_json.index('"engineering_depth"') + 60]
repaired_half = _repair_truncated_json(half_cut)
partial = ProjectIntelligence.model_validate(json.loads(repaired_half))
check("salvage: fields before the cut are preserved",
      partial.understanding.purpose == "Process asynchronous jobs at scale."
      and partial.complexity.overall.score == 70.0
      and partial.complexity.overall.ev == [7])
check("salvage: fields after the cut fall back to schema defaults",
      partial.skills_and_tech == []
      and partial.hiring_signal.score == 0.0
      and partial.overall_confidence == 0.0)

# validate_response wires the salvage in, and still rejects genuine garbage.
salvaged_obj = validate_response(half_cut, ProjectIntelligence)
check("salvage: validate_response returns a partial instead of raising",
      isinstance(salvaged_obj, ProjectIntelligence)
      and salvaged_obj.understanding.domain == "Distributed systems.")
expect_raises(
    "salvage: non-JSON prose is still rejected (not silently salvaged)",
    LLMResponseError,
    lambda: validate_response("I cannot help with that request.", ProjectIntelligence),
)
expect_raises(
    "salvage: empty response is still rejected",
    LLMResponseError,
    lambda: validate_response("   ", ProjectIntelligence),
)
check("salvage: repair of a bare fragment with no closable point returns None",
      _repair_truncated_json('{"understanding') is None)


# ---------------------------------------------------------------------------
print("\n--- 12. max_tokens precedence on the live analyze() call ---")

# Explicit arg wins even when the env var is set.
os.environ["LLM_MAX_TOKENS"] = "4096"
fake_x = FakeProvider()
ProjectAnalysisEngine(llm_service=make_service(fake_x), max_tokens=333).analyze(
    resume_id="r", raw_text=TITLE_ONLY_RESUME
)
check("call: explicit max_tokens=333 forwarded (beats env)",
      fake_x.last_max_tokens == 333, detail=repr(fake_x.last_max_tokens))

# Env var used when no explicit arg.
fake_e = FakeProvider()
ProjectAnalysisEngine(llm_service=make_service(fake_e)).analyze(
    resume_id="r", raw_text=TITLE_ONLY_RESUME
)
check("call: LLM_MAX_TOKENS=4096 forwarded when no explicit arg",
      fake_e.last_max_tokens == 4096, detail=repr(fake_e.last_max_tokens))

# Neither -> 8000 default.
os.environ.pop("LLM_MAX_TOKENS", None)
fake_d = FakeProvider()
res_single = ProjectAnalysisEngine(llm_service=make_service(fake_d)).analyze(
    resume_id="r", raw_text=TITLE_ONLY_RESUME
)
check("call: default 8000 forwarded when neither set",
      fake_d.last_max_tokens == 8000, detail=repr(fake_d.last_max_tokens))
# A one-line project still resolves every citation (refs picked modulo the index).
check("call: single-line project still produces traceable evidence",
      res_single.reports
      and all(e.line_number == 3 for e in res_single.reports[0].understanding.evidence),
      detail=repr([e.line_number for e in res_single.reports[0].understanding.evidence]
                  if res_single.reports else None))

# Model override flows straight through (still no hardcoding in the engine).
fake_m = FakeProvider()
ProjectAnalysisEngine(llm_service=make_service(fake_m), model="acme-model-9").analyze(
    resume_id="r", raw_text=TITLE_ONLY_RESUME
)
check("call: explicit model override forwarded verbatim",
      fake_m.last_model == "acme-model-9", detail=repr(fake_m.last_model))


# ---------------------------------------------------------------------------
print("\n--- 13. No projects -> 0 reports and 0 provider calls ---")

fake_zero = FakeProvider()
res_zero = ProjectAnalysisEngine(llm_service=make_service(fake_zero)).analyze(
    resume_id="r", raw_text=NO_PROJECTS_RESUME
)
check("empty section: 0 reports",
      res_zero.reports == [] and res_zero.total_projects_count == 0)
check("empty section: provider never called (0 calls)",
      fake_zero.calls == 0, detail=f"calls={fake_zero.calls}")

# Keyless robustness: with no injected service AND no API key, the no-projects
# path must NOT construct the LLM service (which would raise), and must not raise.
saved_key = os.environ.pop("OPENAI_API_KEY", None)
try:
    keyless_ok = True
    try:
        res_kl = ProjectAnalysisEngine().analyze(
            resume_id="r", raw_text=NO_PROJECTS_RESUME
        )
    except Exception as exc:  # noqa: BLE001 - the whole point is that none escapes
        keyless_ok = False
        res_kl = None
        errors.append(f"keyless no-projects raised {type(exc).__name__}: {exc}")
    check("keyless: no-projects path skips LLM construction (no raise)",
          keyless_ok and res_kl is not None and res_kl.reports == [])
finally:
    if saved_key is not None:
        os.environ["OPENAI_API_KEY"] = saved_key


# ---------------------------------------------------------------------------
print("\n--- 14. Per-project resilience: one failure never sinks the rest ---")

flaky = FlakyByTitleProvider(fail_marker="Real-Time Chat Application")
fast = LLMSettings(retry_base_delay=0.0, retry_max_delay=0.0, max_retries=1)
res_flaky = ProjectAnalysisEngine(
    llm_service=make_service(flaky, settings=fast)
).analyze(resume_id="r", raw_text=MULTI_PROJECT_RESUME)

check("resilience: still extracts both projects",
      res_flaky.total_projects_count == 2)
check("resilience: only the surviving project produced a report",
      len(res_flaky.reports) == 1
      and res_flaky.reports[0].project_title == "Distributed Task Queue",
      detail=f"reports={[r.project_title for r in res_flaky.reports]}")


# ---------------------------------------------------------------------------
print("\n--- 15. Sync wrapper + dataclasses.asdict round-trip ---")

# `engine.analyze(...)` above already exercised the sync asyncio.run bridge.
check("sync wrapper: returned a dataclass result", is_dataclass(result))

d = asdict(report0)
check("asdict: serializes to a nested dict", isinstance(d, dict))
check("asdict: project_title round-trips",
      d.get("project_title") == "Distributed Task Queue")
check("asdict: nested complexity score round-trips",
      d["complexity"]["overall"]["score"] == 70.0)
check("asdict: rehydrated evidence round-trips with its line number",
      d["hiring_signal"]["evidence"][0]["evidence_text"] == line7.evidence_text
      and d["hiring_signal"]["evidence"][0]["line_number"] == 7,
      detail=repr(d["hiring_signal"]["evidence"][0]))
check("asdict: technical_maturity classification round-trips",
      d["technical_maturity"]["classification"] == "portfolio")
check("asdict: derived max_score / confidence_level are present in the artifact",
      d["complexity"]["overall"]["max_score"] == 100.0
      and d["complexity"]["overall"]["confidence_level"] == "verified")


# ---------------------------------------------------------------------------
print("\n--- 16. Shipped project_analysis prompt renders cleanly ---")

check("prompt: project_analysis template exists",
      default_prompt_manager.exists("project_analysis"))
try:
    rendered = default_prompt_manager.render(
        "project_analysis", schema_name="ProjectIntelligence"
    )
    # Collapse whitespace so a line-wrapped phrase still matches as a substring.
    normalized = " ".join(rendered.lower().split())

    check("prompt: renders with schema_name substituted",
          "ProjectIntelligence" in rendered)
    check("prompt: instructs citation by line number",
          "cite evidence by line number" in normalized
          and '"ev"' in rendered)
    check("prompt: forbids re-quoting evidence text",
          "never quote text" in normalized)
    check("prompt: instructs omission instead of a placeholder",
          "omit what you cannot support" in normalized
          and "missing_evidence" in rendered)
    check("prompt: no longer asks for the cannot-verify sentinel",
          "cannot be verified from available evidence." not in normalized.replace(
              'never write "cannot be verified from available evidence."', ""),
          detail="the sentinel should only appear inside the prohibition")
    check("prompt: forbids emitting derived fields",
          "confidence_level" in rendered and "max_score" in rendered
          and "derived server-side" in normalized)
    check("prompt: states the tiered length budget",
          "length discipline" in normalized and "at most 2 sentences" in normalized)
    check("prompt: documents the merged skills_and_tech array",
          "skills_and_tech" in rendered)
    check("prompt: defines hiring_signal as NOT a placement score",
          "hiring_signal" in rendered and "not a placement score" in normalized)
    check("prompt: covers all 16 areas (numbered list intact)",
          all(f"\n{n}." in rendered for n in range(1, 16)),
          detail="an area heading went missing from the numbered list")
    # ~1,850 tokens, billed as input on every project. It cannot shrink much
    # further: the JSON shape example is load-bearing, because OpenAI-compatible
    # `response_format={"type": "json_object"}` does NOT transmit the schema — the
    # prompt is the only place the key names are stated. Guard against
    # re-inflation rather than chasing a smaller number.
    check("prompt: stayed small (it is billed as input on every call)",
          len(rendered) < 7600, detail=f"len={len(rendered)}")
except Exception as exc:  # a stray single brace would surface here
    check("prompt: renders with schema_name substituted", False, detail=str(exc))


# ---------------------------------------------------------------------------
print("\n--- 17. Architecture documentation exists & is populated ---")

doc_path = os.path.join("..", "docs", "architecture", "phase_3_7_project_analysis.md")
check("doc: phase_3_7 architecture doc exists",
      os.path.isfile(doc_path), detail=doc_path)
if os.path.isfile(doc_path):
    with open(doc_path, "r", encoding="utf-8") as fh:
        doc = fh.read()
    check("doc: is comprehensive (>1000 chars)", len(doc) > 1000,
          detail=f"len={len(doc)}")
    check("doc: references ProjectIntelligenceReport", "ProjectIntelligenceReport" in doc)
    check("doc: references hiring_signal", "hiring_signal" in doc)
    check("doc: documents the omission-as-signal rule",
          "cannot_verify" in doc and "missing_evidence" in doc)
    check("doc: documents citation by line reference",
          "line reference" in doc and "_resolve_refs" in doc)
    check("doc: documents the derived (not transmitted) fields",
          "_confidence_band" in doc and "_MAX_SCORE" in doc)
    check("doc: documents truncation salvage",
          "_repair_truncated_json" in doc)


# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if errors:
    print(f"FAILURES ({len(errors)}):")
    for item in errors:
        print(f"  - {item}")
    print("=" * 60)
    sys.exit(1)
else:
    print("ALL PHASE 3.7 PROJECT ANALYSIS TESTS PASSED")
    print("=" * 60)
    sys.exit(0)
