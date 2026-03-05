# Codex Agent Context - NoteBrew

Last updated: 2026-03-06

## Mission
Maintain a production-ready, end-to-end paper-to-notebook product where backend agent telemetry, frontend status UX, and notebook launch flows are tightly integrated.

## Product Snapshot
- Backend: FastAPI + custom tool-calling orchestrator (`backend/app`)
- Frontend: Next.js 14 + TypeScript + shadcn/ui (`frontend/src`)
- Core flow:
  1. Upload PDF or submit arXiv URL
  2. Agent runs tools (`parse_* -> plan_notebook -> generate_code -> validate_code -> assemble_notebook`)
  3. Frontend polls status and renders timeline
  4. User downloads notebook and opens it in external notebook platforms

## Ground Truth from Code
- API routes in `backend/app/main.py`
- Tool loop in `backend/app/agent/orchestrator.py`
- Runtime task state is in-memory (`tasks` dict)
- Brew progress UI consumes `/api/status/{task_id}` from `frontend/src/app/brew/[id]/page.tsx`

## Confirmed Gaps Before This Session
1. Timeline telemetry gap:
- Backend progress callback did not populate `current_tool`.
- Brew timeline step highlight depended on `current_tool` and could be inaccurate.

2. arXiv state propagation gap:
- `parse_arxiv` results were not mapped into `state.paper_structure` in orchestrator state updates.

3. Metadata completeness gap:
- Parser output included fields (references, key contributions, key findings, doi) not fully represented in Pydantic models.

4. Upload UX gap:
- File drag/drop logic lived inline in `UploadCard`.
- Error UX could be clearer and more reusable.

5. Launch-link gap:
- Completed page used generic Colab/Kaggle home links instead of result-aware deep links.

## Engineering Principles for Follow-up Work
- Keep backend and frontend contracts explicit and version-aligned.
- Prefer additive API changes over breaking ones.
- Expose launch links and readiness from backend; avoid hardcoding platform URLs in UI.
- Keep upload UI composable (`FileDropzone`), testable, and accessible.
- Preserve existing Cream Codex design language.

## Validation Checklist
- Backend commands run with project venv (`backend\\venv\\Scripts\\python.exe`).
- Backend boots and health endpoint responds.
- Frontend builds/lints without TS errors.
- `/api/status/{task_id}` returns tool telemetry fields used by brew timeline.
- arXiv flow keeps metadata through final task status.
- Completed brew view uses backend-provided launch links.

## Notes for Future Agents
- User expects deep project context continuity and explicit handoff quality.
- Keep `.agent/context.md` and this file synced after substantial architecture/API changes.
- Existing repo may be dirty; do not revert unrelated user changes.
