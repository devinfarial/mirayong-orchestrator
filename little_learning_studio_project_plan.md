# Little Learning Studio --- Project Plan

**Project:** Little Learning Studio\
**Version:** 0.1\
**Status:** Planning baseline\
**Implementation language:** Python 3.12+\
**Primary output:** Bahasa Indonesia educational YouTube Shorts with
original 3D animation\
**Initial operating budget:** Up to USD 25/month\
**Initial publishing target:** 1--3 videos per month

------------------------------------------------------------------------

## 1. Executive summary

Little Learning Studio is a small, automated production system for
creating educational YouTube Shorts for children. It will turn a topic
brief into a validated short-form video through a sequence of script
generation, scene planning, visual generation, narration, editing,
quality checks, and YouTube publishing.

The first release should be a **modular monolith**, not a collection of
microservices. Python will coordinate the workflow, external AI services
will generate selected assets, FFmpeg will assemble the final video, and
PostgreSQL will track episodes and production jobs.

The system must be cost-aware. It should estimate generation costs
before starting, enforce a monthly spending limit, avoid uncontrolled
retries, and never automatically top up a provider account.

## 2. Goals and non-goals

### Goals

1.  Generate age-appropriate educational concepts and Bahasa Indonesia
    scripts (narration and on-screen text written natively in
    Indonesian; visual prompts remain in English).
2.  Break scripts into structured scenes with narration and visual
    direction.
3.  Generate original visual assets using a text-to-video provider.
4.  Generate Bahasa Indonesia narration using a text-to-speech provider.
5.  Render vertical videos suitable for YouTube Shorts.
6.  Validate technical output and basic content-safety requirements.
7.  Upload approved videos through the YouTube Data API.
8.  Track status, failures, retries, and estimated/actual costs.
9.  Keep provider integrations replaceable through adapters.

### Non-goals for the first release

-   Real-time interactive video generation.
-   A multi-tenant SaaS product or public customer accounts.
-   A sophisticated browser-based editing suite.
-   Fully autonomous publishing without validation.
-   Training a custom video or voice model.
-   Microservices or Kubernetes deployment.

## 3. Product assumptions and constraints

  -----------------------------------------------------------------------
  Area                                Initial decision
  ----------------------------------- -----------------------------------
  Audience                            Children; define a specific age
                                      band before production

  Language                            Bahasa Indonesia (`id`) for
                                      narration, captions, and
                                      metadata; English for internal
                                      visual prompts

  Format                              Vertical 9:16 YouTube Shorts

  Visual style                        Original, colorful 3D educational
                                      animation

  Topics                              Colors, numbers, alphabet, animals,
                                      shapes, simple science, good habits

  Runtime                             Start with approximately 20--40
                                      seconds; validate against the
                                      content format

  Publishing                          YouTube Data API v3

  Production cadence                  1--3 videos per month initially

  Budget ceiling                      USD 25/month

  Runtime                             Local development first; hosted
                                      deployment later

  Main implementation                 Python modular monolith
  -----------------------------------------------------------------------

**Language policy:** all viewer-facing content is Bahasa Indonesia:
narration, captions/on-screen text, YouTube title, description, and
tags. Internal instructions to Claude (the prompt files) and the
per-scene `visual_prompt` stay in English, because text-to-video models
generally follow English prompts best and viewers never see them.
Narration must be written natively in Indonesian by the script model;
do not write English and translate afterward. Use simple, warm,
standard Indonesian suited to the age band, and have a native speaker
review early outputs.

**Important budget constraint:** video generation is likely to be the
dominant variable cost. Do not assume the target volume fits the budget
until a representative test clip has been generated and measured. Use
short clips, limited scenes, low-cost models where quality is
acceptable, and a hard monthly spend guard.

## 4. Recommended technology stack

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Language                Python 3.12+            Application and
                                                  workflow logic

  API                     FastAPI                 HTTP API and health
                                                  endpoint

  Validation/config       Pydantic,               Request, response, and
                          pydantic-settings       environment validation

  Database                PostgreSQL              Persistent source of
                                                  truth

  ORM/migrations          SQLAlchemy 2.x, Alembic Data access and schema
                                                  evolution

  Background jobs         Celery                  Long-running generation
                                                  and publishing tasks

  Queue/backend           Redis                   Celery broker and
                                                  result backend

  Script planning         Anthropic Claude API    Topic, script, and
                                                  scene-plan generation

  Video generation        Higgsfield API (initial Text-to-video scene
                          provider)               generation

  Voice                   ElevenLabs API (initial Indonesian narration
                          provider)               

  Rendering               FFmpeg                  Audio/video composition
                                                  and encoding

  Publishing              YouTube Data API v3     Upload and metadata

  Tests                   pytest, pytest-asyncio  Unit and integration
                                                  tests

  Local infrastructure    Docker Compose          PostgreSQL and Redis
  -----------------------------------------------------------------------

Provider selection is an initial implementation choice, not a permanent
dependency. Keep provider-specific code behind interfaces so pricing,
availability, or quality changes do not require rewriting the workflow.

## 5. System architecture

Use a modular monolith with clear internal boundaries:

-   **API layer:** accepts requests and exposes episode/job status.
-   **Application/core layer:** coordinates the production workflow and
    state transitions.
-   **Domain/data layer:** episode, scene, character, and job records.
-   **Provider layer:** Claude, video, voice, and YouTube adapters.
-   **Worker layer:** executes long-running tasks asynchronously.
-   **Media layer:** stores generated assets and rendered files.
-   **Cost/safety layer:** enforces budget and validation rules.

PostgreSQL is the source of truth. Redis/Celery is a task-delivery
mechanism, not the authoritative record of episode status.

### High-level production flow

``` text
Create episode
    |
    v
Generate topic/script
    |
    v
Validate script and scene plan
    |
    v
Generate scene assets
    |
    v
Generate narration
    |
    v
Render vertical video
    |
    v
Run technical and content checks
    |
    v
Queue for publishing
    |
    v
Upload to YouTube
    |
    v
Record video ID, URL, and final status
```

A failed stage should be retryable without repeating already completed,
reusable stages.

## 6. Project structure

``` text
little-learning-studio/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   └── v1/
│   │       ├── episodes.py
│   │       ├── characters.py
│   │       └── jobs.py
│   ├── core/
│   │   ├── orchestration.py
│   │   ├── state_machine.py
│   │   └── cost_manager.py
│   ├── models/
│   │   ├── episode.py
│   │   ├── scene.py
│   │   ├── character.py
│   │   └── generation_job.py
│   ├── schemas/
│   │   ├── episode.py
│   │   └── script.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── claude.py
│   │   ├── higgsfield.py
│   │   ├── elevenlabs.py
│   │   └── youtube.py
│   ├── services/
│   │   ├── script_service.py
│   │   ├── video_service.py
│   │   ├── voice_service.py
│   │   └── rendering_service.py
│   └── workers/
│       ├── celery_app.py
│       └── tasks.py
├── prompts/
│   ├── topic_generator.md
│   ├── script_writer.md
│   ├── visual_director.md
│   └── content_validator.md
├── storage/
│   ├── generated/
│   ├── audio/
│   ├── renders/
│   └── thumbnails/
├── tests/
│   ├── unit/
│   └── integration/
├── alembic/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

Keep generated media out of Git. For production, move media to durable
object storage (for example, S3-compatible storage) rather than relying
on a local container filesystem.

## 7. Core data model

### Episode

Suggested fields:

-   `id` --- UUID primary key
-   `title` --- working title
-   `topic` --- educational topic
-   `target_age_band` --- intended age range
-   `language` --- `id` (Bahasa Indonesia); other codes reserved for
    future use
-   `status` --- episode state
-   `script_json` --- validated script/scene plan
-   `render_path` --- final render location
-   `youtube_video_id` --- populated after successful upload
-   `estimated_cost` and `actual_cost`
-   `created_at`, `updated_at`, `published_at`

### Scene

Suggested fields:

-   `id` --- UUID primary key
-   `episode_id` --- foreign key
-   `sequence_number`
-   `narration_text`
-   `visual_prompt`
-   `duration_seconds`
-   `asset_path`
-   `generation_status`
-   `provider_request_id`
-   `estimated_cost`, `actual_cost`

### GenerationJob

Suggested fields:

-   `id` --- UUID primary key
-   `episode_id` --- foreign key
-   `stage`
-   `status`
-   `attempt_count`
-   `provider_request_id`
-   `error_code`, `error_message`
-   `started_at`, `finished_at`
-   `estimated_cost`, `actual_cost`

### Character

Use a reusable character record to keep recurring original characters
visually consistent. Store a character description, visual reference
asset, and version. Do not use copyrighted characters or imitate a
specific protected franchise.

## 8. Episode lifecycle and state machine

Recommended episode states:

``` text
DRAFT
  -> SCRIPT_READY
  -> ASSETS_GENERATED
  -> RENDERED
  -> VALIDATED
  -> PUBLISH_QUEUED
  -> PUBLISHED
```

A stage may transition to `FAILED`. A retry should resume from the
failed stage when its inputs and previous outputs are still valid.

Rules:

1.  Validate every state transition in application code.
2.  Persist state changes in PostgreSQL.
3.  Make worker tasks idempotent.
4.  Save provider request IDs and output paths.
5.  Use bounded retries with backoff.
6.  Do not regenerate completed assets unless explicitly requested or an
    asset is invalid.
7.  Do not mark an episode `PUBLISHED` until YouTube confirms the upload
    and the returned video ID is saved.

Keep job state separate from episode state. An episode can have multiple
jobs over its lifetime.

## 9. API outline

Prefix application endpoints with `/api/v1`.

  -----------------------------------------------------------------------------------
  Method                  Endpoint                            Purpose
  ----------------------- ----------------------------------- -----------------------
  `POST`                  `/episodes`                         Create a draft episode

  `GET`                   `/episodes`                         List episodes

  `GET`                   `/episodes/{episode_id}`            Retrieve episode
                                                              details

  `POST`                  `/episodes/{episode_id}/generate`   Start or resume
                                                              production

  `GET`                   `/episodes/{episode_id}/status`     Read production status

  `POST`                  `/episodes/{episode_id}/retry`      Retry an eligible
                                                              failed stage

  `GET`                   `/jobs/{job_id}`                    Retrieve a job's status
  -----------------------------------------------------------------------------------

Creating an episode should only validate and save the draft. It should
not immediately call paid AI providers. Generation starts through the
explicit generate endpoint.

## 10. Production workflow details

### Stage A --- Topic and script

Claude should return structured JSON, not free-form prose only. The
schema should include:

-   Episode title and learning objective.
-   Target age band.
-   A short opening hook.
-   Scene sequence and duration.
-   Narration per scene.
-   Visual prompt per scene.
-   On-screen text, if any.
-   Closing recap or call to action.

Validate the response with Pydantic. Reject missing fields, excessive
runtime, unsuitable language, or prompts that violate content rules.

Language handling: `narration_text`, the opening hook, `on_screen_text`,
and the closing recap are written in Bahasa Indonesia. `visual_prompt`
is written in English. Indonesian speech pacing differs from English,
so measure real narration length and tune the words-per-second guidance
and `narration_text` limit accordingly.

### Stage B --- Visual direction and generation

For each scene:

1.  Build a prompt using the scene, style guide, and character
    references.
2.  Estimate cost before submitting the request.
3.  Submit to the video provider.
4.  Poll or receive completion status.
5.  Download the result to managed storage.
6.  Record provider request ID, duration, path, and actual cost.

Instruct the video model not to render any text, letters, or signs in
the frame; all on-screen words are added in the rendering stage.

Start with a small number of scenes per Short. More scenes increase cost
and failure opportunities.

### Stage C --- Narration

1.  Convert validated narration text to speech.
2.  Save the audio asset.
3.  Record voice settings and provider request metadata.
4.  Check that audio duration is compatible with the scene timeline.

Choose a voice and model verified to pronounce Bahasa Indonesia
naturally; audition samples before committing, because quality varies
by voice. TTS is billed per character, so measure the character count
of Indonesian scripts when estimating cost. Use a licensed voice and
retain the relevant commercial-use terms for
the selected plan.

### Stage D --- Rendering

FFmpeg should:

-   Fit/crop footage to 9:16.
-   Normalize resolution and frame rate.
-   Join scene clips in sequence.
-   Mix narration and permitted background audio.
-   Add Bahasa Indonesia captions or simple on-screen labels, using a
    font that renders the text correctly.
-   Encode to a YouTube-compatible MP4.
-   Save a thumbnail if required.

Keep the rendering service deterministic: the same input assets and
render configuration should produce the same intended edit.

### Stage E --- Validation

At minimum, validate:

-   File exists and is readable.
-   Video is vertical 9:16.
-   Resolution, frame rate, codec, and duration meet configured limits.
-   Audio is present and not silent.
-   Narration and visuals are aligned sufficiently.
-   Captions/on-screen text are legible.
-   No accidental blank, corrupted, or duplicate scenes.
-   Script and output are age-appropriate.
-   Rights to generated visuals, voices, music, and other assets are
    documented.

Do not publish automatically if a required check fails. During the first
production runs, manually review every finished video before enabling
unattended publishing.

### Stage F --- YouTube publishing

Implement OAuth 2.0 and YouTube Data API v3 upload. Store refresh tokens
securely; do not commit credentials to source control.

Before upload, set title, description, tags, category, privacy status,
and audience designation. If the content is directed to children,
correctly declare it as Made for Kids using the applicable YouTube
setting/API field. Confirm current YouTube API and policy requirements
before production deployment.

Write the title, description, and tags in Bahasa Indonesia, and set the
video's default language and default audio language to `id`.

Save the returned YouTube video ID and URL. Handle quota errors, upload
interruptions, and retries without accidentally creating duplicate
uploads.

## 11. Cost controls

The monthly cap is USD 25. Treat this as a hard limit, not a target to
spend.

Required controls:

1.  Maintain a monthly ledger of estimated and actual provider costs.
2.  Estimate a job's cost before making paid API calls.
3.  Refuse new generation jobs if the projected monthly total exceeds
    the configured cap.
4.  Set per-episode and per-provider limits.
5.  Limit retries and require a reason for manual reruns.
6.  Do not enable automatic provider-account top-ups.
7.  Cache and reuse valid assets where appropriate.
8.  Log cost by episode, scene, provider, and model.

Start with a conservative video-generation allocation (for example, a
configurable USD 10 monthly sub-limit) and adjust only after measuring
real costs. Verify live provider pricing before implementation; pricing
and plan limits change. A 1--3 video/month target may still exceed the
budget if each Short contains many generated seconds or repeated
attempts.

## 12. Safety, rights, and quality requirements

-   Use original characters and original scripts.
-   Do not use famous copyrighted characters, logos, or recognizable
    franchise designs without permission.
-   Use music, sound effects, fonts, and voices with appropriate
    commercial-use rights.
-   Keep language and concepts suitable for the declared age band.
-   Have a native Indonesian speaker review early scripts and narration
    for natural phrasing, correct pronunciation, and cultural
    suitability.
-   Avoid unsafe demonstrations or instructions that children might
    imitate.
-   Do not request or expose children's personal information.
-   Correctly configure YouTube's Made for Kids designation when
    applicable.
-   Apply YouTube's synthetic/altered-content disclosure when the
    content meets the platform's criteria; do not assume every stylized
    cartoon requires it.
-   Avoid repetitive, mass-produced videos with little educational
    value. Each episode should have a clear learning objective and
    meaningful variation.
-   Keep a human approval gate until output quality and policy
    compliance are consistently demonstrated.

## 13. Development milestones

### Milestone 1 --- Foundation

-   [ ] Create Python 3.12+ project and virtual environment.
-   [ ] Add FastAPI application and health endpoint.
-   [ ] Add settings management with `.env`.
-   [ ] Add Docker Compose for PostgreSQL and Redis.
-   [ ] Configure SQLAlchemy async database access.
-   [ ] Add Episode model and Alembic migration.
-   [ ] Implement Episode create/list/get endpoints.
-   [ ] Add basic unit and integration tests.

**Acceptance criteria:** the app starts locally, connects to PostgreSQL,
applies migrations, and episode CRUD works.

### Milestone 2 --- Script generation

-   [ ] Define Pydantic schemas for script and scene plan.
-   [ ] Add Claude provider adapter.
-   [ ] Create topic and script prompts (Indonesian narration, English
    visual prompts).
-   [ ] Add `language` column to Episode (`id`).
-   [ ] Persist validated script JSON.
-   [ ] Add script validation tests and failure handling.

**Acceptance criteria:** a draft episode can produce a schema-valid
script without generating video.

### Milestone 3 --- Workflow engine

-   [ ] Implement episode state machine.
-   [ ] Add Celery and Redis worker.
-   [ ] Implement job records and status tracking.
-   [ ] Add idempotency and bounded retry behavior.
-   [ ] Add cost estimation and monthly cap checks.

**Acceptance criteria:** a generation request creates trackable jobs and
safely resumes after a simulated failure.

### Milestone 4 --- Video and voice assets

-   [ ] Implement Higgsfield adapter.
-   [ ] Audition and select an Indonesian voice/model before building
    the ElevenLabs adapter.
-   [ ] Implement ElevenLabs adapter.
-   [ ] Save assets to managed storage.
-   [ ] Persist provider request IDs and actual costs.
-   [ ] Add timeout, retry, and provider-error tests.

**Acceptance criteria:** one test episode can generate and retrieve all
required scene clips and narration within the configured budget.

### Milestone 5 --- Rendering and validation

-   [ ] Implement FFmpeg rendering service.
-   [ ] Add 9:16 output profile.
-   [ ] Add audio/video validation.
-   [ ] Generate captions or simple labels.
-   [ ] Add preview/review workflow.

**Acceptance criteria:** a complete MP4 passes automated technical
checks and can be reviewed before upload.

### Milestone 6 --- YouTube publishing

-   [ ] Configure Google Cloud project and YouTube Data API.
-   [ ] Implement OAuth flow and secure token storage.
-   [ ] Implement upload and metadata handling.
-   [ ] Set audience designation correctly.
-   [ ] Persist YouTube video ID and URL.
-   [ ] Test quota and retry behavior.

**Acceptance criteria:** an approved test video uploads successfully to
the intended channel and the application records the result.

### Milestone 7 --- Controlled automation

-   [ ] Add scheduled topic planning.
-   [ ] Add production queue limits.
-   [ ] Add monthly cost reporting.
-   [ ] Add alerts for failed jobs and budget thresholds.
-   [ ] Enable unattended publishing only after a sustained
    manual-review period.

**Acceptance criteria:** the system can run a limited monthly schedule,
stays within its budget guard, and stops safely on validation or
provider failures.

## 14. Testing strategy

-   **Unit tests:** state transitions, cost calculations, schemas,
    prompt formatting.
-   **Provider contract tests:** mock HTTP responses, timeouts, rate
    limits, and malformed payloads.
-   **Integration tests:** PostgreSQL persistence, Celery task flow, and
    storage.
-   **Rendering tests:** short fixture clips through FFmpeg; inspect
    metadata and audio presence.
-   **End-to-end tests:** one low-cost episode from draft to validated
    render.
-   **Publishing tests:** use private/unlisted test uploads where
    appropriate and verify channel settings.

Do not spend money on external generation APIs in ordinary unit tests.
Use mocks and recorded fixtures.

## 15. Configuration and secrets

Example `.env.example` keys:

``` dotenv
APP_ENV=development
APP_NAME=Little Learning Studio
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/little_learning
REDIS_URL=redis://localhost:6379/0

ANTHROPIC_API_KEY=
HIGGSFIELD_API_KEY=
ELEVENLABS_API_KEY=

YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REDIRECT_URI=

MONTHLY_BUDGET_USD=25
VIDEO_PROVIDER_BUDGET_USD=10
MAX_RETRIES_PER_STAGE=2
DEFAULT_LANGUAGE=id
```

Use a secret manager or protected environment variables in production.
`.env` must be ignored by Git. Never log API keys, OAuth secrets, or
refresh tokens.

## 16. Initial local setup

Create the project:

``` bash
mkdir little-learning-studio
cd little-learning-studio
python -m venv .venv
```

Activate the environment:

``` bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the initial dependencies:

``` bash
pip install \
  fastapi \
  "uvicorn[standard]" \
  pydantic \
  pydantic-settings \
  sqlalchemy \
  asyncpg \
  alembic \
  celery \
  redis \
  anthropic \
  httpx \
  python-multipart \
  pytest \
  pytest-asyncio
```

Create `app/main.py`:

``` python
from fastapi import FastAPI

app = FastAPI(
    title="Little Learning Studio",
    description="AI-powered educational Shorts production platform",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "little-learning-studio",
    }
```

Run the API:

``` bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API documentation
and `http://localhost:8000/health` for the health check.

## 17. Immediate next actions

The first implementation sprint should be deliberately small:

1.  Create the project skeleton and install dependencies.
2.  Add configuration and `.env.example`.
3.  Start PostgreSQL and Redis with Docker Compose.
4.  Connect SQLAlchemy to PostgreSQL.
5.  Create the Episode model and first Alembic migration.
6.  Implement and test episode create/list/get endpoints.

Do not integrate video generation in the first sprint. Establish a
reliable database-backed episode workflow first, then add Claude script
generation, background jobs, and paid media providers one stage at a
time.

## 18. Open decisions to resolve before production

-   Exact target age band (for example, 3--5 or 5--7).
-   Final target runtime and number of scenes per Short.
-   Whether a human must approve every upload or only the first
    production batch.
-   Exact video-generation model after a measured quality/cost test.
-   Indonesian voice and model choice, and narration register (simple
    standard vs. casual), reviewed by a native speaker.
-   Storage provider for production media.
-   YouTube channel branding, metadata template, and upload privacy
    defaults.
-   Current provider pricing, rate limits, commercial-use terms, and
    retention policies.

------------------------------------------------------------------------

**Planning principle:** build a small, observable, cost-limited pipeline
that reliably produces one reviewed Short before attempting higher
volume or fully unattended publishing.
