# Mirayong Studio (Little Learning Studio)

An automated, cost-aware Python modular monolith for producing **Bahasa Indonesia educational YouTube Shorts** with original 3D animation.

Given an educational topic brief, the platform orchestrates the full production lifecycle:
1. **Script & Scene Planning (`script`)** — Generates an age-appropriate Bahasa Indonesia narration script with English 3D visual prompts via Claude or Gemini.
2. **Media Asset Generation (`assets`)** — Synthesizes Indonesian voiceover audio (ElevenLabs) and 3D animated scene clips (Higgsfield) with per-scene idempotency so retries never re-buy completed clips.
3. **Vertical Video Composition (`render`)** — Normalizes and stitches scene video + narration into a 9:16 (`1080x1920`) vertical `.mp4` via FFmpeg.
4. **Technical & Child-Safety Validation (`validate`)** — Verifies file integrity, timeline bounds (`15s`–`40s`), scene completeness, and child-safety content rules.
5. **YouTube Shorts Publishing (`publish`)** — Uploads the validated `.mp4` via the YouTube Data API v3 with Bahasa Indonesia metadata (`defaultLanguage="id"`) and `selfDeclaredMadeForKids=True`.

---

## Tech Stack

| Layer | Technology | Java / Spring Boot Equivalent |
| :--- | :--- | :--- |
| **Web Framework** | FastAPI + Uvicorn | Spring Boot (`@RestController`) |
| **ORM & Database** | SQLAlchemy 2.x (Async) + PostgreSQL 16 | Hibernate / Spring Data JPA |
| **Schema Migrations** | Alembic | Flyway / Liquibase |
| **Validation & Config** | Pydantic v2 + `pydantic-settings` | Jakarta Validation + `@ConfigurationProperties` |
| **Background Queue** | Celery + Redis 7 | Spring `@Async` + RabbitMQ / Redis |
| **AI & Media Providers** | Anthropic Claude / Google Gemini, ElevenLabs, Higgsfield, FFmpeg, YouTube Data API v3 | External REST/CLI Adapters |
| **Testing** | `pytest` + `pytest-asyncio` + `httpx` | JUnit 5 + MockMvc |

---

## Project Structure

```text
mirayong-studio/
├── app/
│   ├── main.py                      # FastAPI entrypoint, routers & lifespan
│   ├── api/
│   │   ├── episode.py               # Episode CRUD & workflow endpoints
│   │   ├── job.py                   # Job status & monthly cost report endpoints
│   │   └── ai.py                    # Direct AI chat test endpoint
│   ├── core/
│   │   ├── config.py                # Environment & budget settings
│   │   ├── state_machine.py         # EpisodeStatus enum & transition validator
│   │   ├── cost_manager.py          # Pre-job cost estimation & $25/mo budget guard
│   │   └── orchestration.py         # Stage runner, retry recovery & pipeline autopilot
│   ├── db/
│   │   ├── base.py                  # SQLAlchemy DeclarativeBase
│   │   └── session.py               # Async engine & session dependency
│   ├── models/
│   │   ├── episode.py               # Episode entity
│   │   ├── scene.py                 # Scene entity (per-scene video/audio paths & cost)
│   │   └── generation_job.py        # GenerationJob entity (stage execution tracking)
│   ├── providers/
│   │   ├── base.py                  # VideoProvider & VoiceProvider protocols
│   │   ├── elevenlabs.py            # ElevenLabs TTS adapter (mock + live)
│   │   ├── higgsfield.py            # Higgsfield text-to-video adapter (mock + live)
│   │   └── youtube.py               # YouTube Data API v3 uploader (mock + live)
│   ├── repositories/                # Data access layer (Episode, Scene, Job)
│   ├── schemas/                     # Pydantic request/response DTOs
│   ├── services/                    # Business logic (Script, Asset, Render, Validate, Publish)
│   └── workers/
│       ├── celery_app.py            # Celery broker/backend config
│       └── tasks.py                 # Async-wrapped background tasks
├── migrations/                      # Alembic database migrations
├── prompts/
│   └── script_writer.md             # System prompt for Indonesian script + English visual prompts
├── storage/                         # Generated audio/, generated/, and renders/ (gitignored)
├── tests/                           # Unit & integration test suite
├── docker-compose.yml               # Local PostgreSQL (port 5433) & Redis (port 6379)
├── alembic.ini                      # Alembic configuration
├── pytest.ini                       # Pytest configuration
└── requirements.txt                 # Python dependencies
```

---

## Quick Start & Local Setup

### 1. Activate Virtual Environment & Install Dependencies
```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start PostgreSQL & Redis (Docker Compose)
Make sure Docker Desktop is running, then run:
```powershell
docker compose up -d
docker compose ps
```
- **PostgreSQL** runs on `localhost:5433` (`episode_db`, user `postgres`, password `password`).
- **Redis** runs on `localhost:6379`.

### 3. Configure `.env`
Create or update `.env` in the project root:
```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5433/episode_db
REDIS_URL=redis://localhost:6379/0

# Script AI Provider ("gemini" or "anthropic")
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-sonnet-4-5
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash

# Media & Publishing Modes ("mock" for $0 local dry-runs)
VOICE_PROVIDER=mock
VIDEO_PROVIDER=mock
RENDER_MODE=mock
YOUTUBE_PROVIDER=mock

# Budget & Automation Controls
MONTHLY_BUDGET_USD=25.0
MAX_EPISODE_COST_USD=10.0
ALLOW_UNATTENDED_PUBLISH=false
```

### 4. Apply Database Migrations (Alembic)
```powershell
alembic upgrade head
```

### 5. Start the FastAPI Server
```powershell
uvicorn app.main:app --reload
```
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **DB Health Check:** [http://localhost:8000/health/db](http://localhost:8000/health/db)

---

## User Guide: How to Produce an Episode

You can drive the studio directly from **Swagger UI (`http://localhost:8000/docs`)** in either **Autopilot Mode** or **Step-by-Step Mode**.

### Option A: One-Click Autopilot Mode (Recommended)

1. **Create a Draft Episode (`POST /api/v1/episodes`):**
   ```json
   {
     "title": "Belajar Warna Merah",
     "topic": "Mengenal warna merah di sekitar kita",
     "target_age_band": "4-6",
     "language": "id",
     "description": "Gunakan karakter rubah kecil yang ramah bernama Rubah Rudi"
   }
   ```
   Copy the returned `"id"` (for example, `1`).

2. **Run the Pipeline (`POST /api/v1/episodes/1/run-pipeline`):**
   - Automatically executes:
     1. `script` → Generates and validates the Bahasa Indonesia script (`status: "script_ready"`).
     2. `assets` → Generates voiceover audio (`storage/audio/`) and 3D scene clips (`storage/generated/`) (`status: "assets_generated"`).
     3. `render` → Stitches scenes into `storage/renders/episode_1_final.mp4` (`status: "rendered"`).
     4. `validate` → Verifies the `.mp4` file, scene timeline, and child-safety rules (`status: "validated"`).
   - **Human Review Gate:** When `ALLOW_UNATTENDED_PUBLISH=false` (the default), the pipeline pauses at `validated` so you can watch `storage/renders/episode_1_final.mp4` on your computer first!

3. **Approve & Publish to YouTube (`POST /api/v1/episodes/1/generate`):**
   - Once you review the `.mp4` video and are happy with it, call `POST /api/v1/episodes/1/generate` one more time.
   - It executes the final `publish` stage, uploads the video to YouTube Shorts, saves `youtube_video_id`, and transitions the episode to `published`!

---

### Option B: Step-by-Step Mode (Manual Control at Every Stage)

Each call to **`POST /api/v1/episodes/{episode_id}/generate`** advances the episode by **one stage** in the state machine:

```text
draft
  ──(POST /generate)──► script_ready
  ──(POST /generate)──► assets_generated
  ──(POST /generate)──► rendered
  ──(POST /generate)──► validated
  ──(POST /generate)──► published
```

- **Want to inspect or regenerate the script before generating video?**
  Call `POST /api/v1/episodes/{id}/script` while the episode is in `draft` or `script_ready` status.
- **Want to inspect generated scene files?**
  Call `GET /api/v1/episodes/{id}/scenes` to see every scene's `video_path`, `audio_path`, `provider_request_id`, and `actual_cost`.
- **What if a stage fails (e.g., network timeout)?**
  The episode moves to `failed` and records the error on the `GenerationJob`. Call **`POST /api/v1/episodes/{id}/retry`** to resume from the exact failed stage without re-running or re-paying for already completed stages or scenes.
- **How do I check my monthly spending?**
  Call **`GET /api/v1/jobs/report/monthly`** to view your current UTC month's spend, remaining budget out of `$25.00`, utilization percentage, and active threshold warnings.

---

## Going Live with Real Media Providers

By default, `VOICE_PROVIDER`, `VIDEO_PROVIDER`, `RENDER_MODE`, and `YOUTUBE_PROVIDER` are set to `"mock"` so you can test the entire workflow locally for **$0.00**.

To switch to real production providers, update `.env`:

```dotenv
# 1. Real Bahasa Indonesia Narration (ElevenLabs Multilingual v2)
VOICE_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb

# 2. Real 3D Video Generation (Higgsfield)
VIDEO_PROVIDER=higgsfield
HIGGSFIELD_API_KEY=your_higgsfield_api_key

# 3. Real 9:16 MP4 Composition (Requires ffmpeg installed on PATH)
RENDER_MODE=ffmpeg
FFMPEG_BINARY=ffmpeg

# 4. Real YouTube Shorts Upload (OAuth 2.0 Bearer Token)
YOUTUBE_PROVIDER=youtube
YOUTUBE_ACCESS_TOKEN=your_google_oauth_access_token
YOUTUBE_PRIVACY_STATUS=private
YOUTUBE_MADE_FOR_KIDS=true
```

---

## Running Tests & Background Worker

### Run the Automated Test Suite
```powershell
pytest -v
```
*(All unit and integration tests use an isolated in-memory SQLite database and mock providers so running `pytest` never costs money.)*

### Run the Celery Background Worker (Optional)
```powershell
celery -A app.workers.celery_app worker --pool=solo -l info
```
