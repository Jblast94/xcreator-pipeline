"""
Content Pipeline Web Dashboard — FastAPI + Jinja2 + HTMX.

Central control panel for:
  - Model discovery (HF latest models)
  - LoRA directory (CivitAI curated)
  - ComfyUI workflow management
  - daggr bridge execution
  - GPU provisioning (RunPod/Vast.ai)
  - Output gallery

Run:  uv run python app.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ── Config ────────────────────────────────────────────────────────────────────

DASHBOARD_HOST = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "7861"))
BRIDGE_URL = os.environ.get("DAGGR_BRIDGE_URL", "http://127.0.0.1:3721")
OUTPUT_DIR = Path(
    os.environ.get(
        "DAGGR_OUTPUT_DIR",
        "/mnt/storage/projects/content-automation-platform/workflow/generated_content",
    )
)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Content Pipeline Dashboard", version="0.1.0")

# Add error handler to see full tracebacks
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarRequest

@app.exception_handler(Exception)
async def debug_exception_handler(request: StarRequest, exc: Exception):
    import traceback
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": tb},
    )

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Try to mount static dir
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Data: Known Spaces ─────────────────────────────────────────────────────────

SPACES: dict[str, dict[str, Any]] = {
    "Z-Image-Turbo": {
        "id": "jblast94/Z-Image-Turbo",
        "purpose": "Primary image gen",
    },
    "flux-klein-9b-kv": {
        "id": "jblast94/flux-klein-9b-kv",
        "purpose": "Backup image gen (Flux)",
    },
    "LTX-2-3": {
        "id": "jblast94/LTX-2-3",
        "purpose": "Video generation",
    },
    "linkaroo-caption": {
        "id": "jblast94/linkaroo-caption",
        "purpose": "Image captioning",
    },
}

# ── Data: Curated LoRAs (from CivitAI research) ────────────────────────────────

CURATED_LORAS = [
    {
        "name": "aidmaNSFWunlock",
        "creator": "aidma",
        "base_model": "FLUX.1/2",
        "category": "NSFW Unlock",
        "url": "https://civitai.com/models/674027",
        "rating": "4.9",
        "likes": "12K",
        "downloads": "280K",
        "trigger_words": "nsfw, nude",
        "stack_order": "Base @ 0.5-0.8",
    },
    {
        "name": "Nude Style for FLUX V2",
        "creator": "community",
        "base_model": "FLUX.1/2",
        "category": "Style",
        "url": "https://civitai.com/models/847101",
        "rating": "4.8",
        "likes": "8K",
        "downloads": "150K",
        "trigger_words": "nsfw, nude (helps; not required)",
        "stack_order": "Style @ 1.0 (no trigger needed)",
    },
    {
        "name": "Detail Enhancer FLUX V1",
        "creator": "community",
        "base_model": "FLUX.1/2",
        "category": "Detail Enhancer",
        "url": "https://civitai.com/models/detail-enhancer-flux",
        "rating": "4.7",
        "likes": "6K",
        "downloads": "120K",
        "trigger_words": "detailed, sharp focus",
        "stack_order": "Detail @ 0.5-1.0",
    },
    {
        "name": "Perfect Hands FLUX",
        "creator": "community",
        "base_model": "FLUX.1/2",
        "category": "Anatomy",
        "url": "https://civitai.com/models/perfect-hands-flux",
        "rating": "4.6",
        "likes": "5K",
        "downloads": "95K",
        "trigger_words": "perfect hands, detailed hands",
        "stack_order": "Anatomy @ 0.5-0.7",
    },
    {
        "name": "aidmaBreasts FLUX",
        "creator": "aidma",
        "base_model": "FLUX.1/2",
        "category": "Anatomy",
        "url": "https://civitai.com/models/aidma-breasts-flux",
        "rating": "4.8",
        "likes": "9K",
        "downloads": "200K",
        "trigger_words": "breasts, large breasts",
        "stack_order": "Anatomy @ 0.7-0.9",
    },
    {
        "name": "aidmaPussy FLUX",
        "creator": "aidma",
        "base_model": "FLUX.1/2",
        "category": "Anatomy",
        "url": "https://civitai.com/models/aidma-pussy-flux",
        "rating": "4.7",
        "likes": "11K",
        "downloads": "250K",
        "trigger_words": "pussy, vagina, spread",
        "stack_order": "Anatomy @ 0.7-0.9",
    },
    {
        "name": "aidmaassFLUX",
        "creator": "aidma",
        "base_model": "FLUX.1/2",
        "category": "Anatomy",
        "url": "https://civitai.com/models/aidma-ass-flux",
        "rating": "4.8",
        "likes": "10K",
        "downloads": "220K",
        "trigger_words": "ass, big ass, anal",
        "stack_order": "Anatomy @ 0.6-0.9",
    },
    {
        "name": "NSFW Master FLUX (Z-Image Turbo)",
        "creator": "community",
        "base_model": "Z-Image",
        "category": "NSFW Unlock",
        "url": "https://civitai.com/models/667086/nsfw-master-flux",
        "rating": "4.5",
        "likes": "4K",
        "downloads": "80K",
        "trigger_words": "nsfw, nude, master",
        "stack_order": "Base unlock @ 0.6-0.9",
    },
]

CURATED_CHECKPOINTS = [
    {
        "name": "Fluxed Up 7.1",
        "creator": "community",
        "base_model": "FLUX.1",
        "url": "https://civitai.com/models/847101/fluxed-up-flux-nsfw-checkpoint",
        "rating": "4.9",
        "favorites": "95.9K",
        "images": 8300,
        "generations": 8300000,
        "best_for": "General NSFW, any scene",
    },
    {
        "name": "Flux Klein (high-res)",
        "creator": "community",
        "base_model": "FLUX.2 Klein",
        "url": "https://civitai.com/models/2311518/flux-klein-high-res-workflow",
        "rating": "4.8",
        "favorites": "45K",
        "images": 3200,
        "generations": 2100000,
        "best_for": "High-res (4K/8K), photorealism",
    },
    {
        "name": "Z-Image Turbo V2",
        "creator": "Tongyi-MAI",
        "base_model": "Z-Image",
        "url": "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo",
        "rating": "4.6",
        "favorites": "28K",
        "images": 1500,
        "generations": 950000,
        "best_for": "Fast inference (4-9 steps), low VRAM",
    },
]

# ── Data: ComfyUI Workflow Templates ─────────────────────────────────────────

COMFYUI_WORKFLOWS = [
    {
        "id": "flux-t2i",
        "name": "FLUX.1 Text-to-Image",
        "type": "Image",
        "model": "FLUX.1-dev",
        "description": "Standard FLUX.1 text-to-image generation with optional LoRA stacking. Outputs 1024×1024 images.",
        "resolution": "1024×1024",
        "steps": "28-35",
        "vram": "16-24 GB",
    },
    {
        "id": "flux-klein-hires",
        "name": "FLUX Klein High-Res",
        "type": "Image",
        "model": "FLUX.2 Klein",
        "description": "FLUX Klein pipeline with upscaling to 4K/8K. Uses Klein's efficient architecture for high resolution.",
        "resolution": "4K-8K",
        "steps": "28-35 + upscale",
        "vram": "24 GB",
    },
    {
        "id": "sdxl-t2i",
        "name": "SDXL Text-to-Image",
        "type": "Image",
        "model": "SDXL",
        "description": "Standard SDXL pipeline. Maximum LoRA compatibility — thousands of community LoRAs available.",
        "resolution": "1024×1024",
        "steps": "25-30",
        "vram": "8-16 GB",
    },
    {
        "id": "wan21-i2v",
        "name": "Wan2.1 Image-to-Video",
        "type": "Video",
        "model": "Wan2.1 14B",
        "description": "Image-to-video generation using Wan2.1. Takes an input image and generates a video continuation.",
        "resolution": "1280×720",
        "steps": "50",
        "vram": "24-48 GB",
    },
    {
        "id": "wan21-t2v",
        "name": "Wan2.1 Text-to-Video",
        "type": "Video",
        "model": "Wan2.1 14B",
        "description": "Text-to-video generation using Wan2.1. Generates video from prompt description alone.",
        "resolution": "1280×720",
        "steps": "50",
        "vram": "24-48 GB",
    },
    {
        "id": "wan22-long-video",
        "name": "Wan2.2 Long Video (GGUF)",
        "type": "Video",
        "model": "Wan2.2 5B",
        "description": "Long-form video generation with Wan2.2 GGUF. Supports frame interpolation for extended sequences.",
        "resolution": "1280×720",
        "steps": "50+",
        "vram": "16-24 GB (GGUF)",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────


async def check_hf_space(space_id: str) -> dict[str, Any]:
    """Check a HF Space's health via API."""
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://huggingface.co/api/spaces/{space_id}"
            )
            if resp.status_code != 200:
                return {"status": "error", "latency": time.time() - t0}
            data = resp.json()
            stage = data.get("runtime", {}).get("stage", "UNKNOWN")
            return {
                "status": stage,
                "latency": time.time() - t0,
            }
    except Exception as e:
        return {"status": f"error: {e}", "latency": time.time() - t0}


async def check_bridge() -> dict[str, Any]:
    """Check the daggr bridge health."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{BRIDGE_URL}/health")
            if resp.status_code == 200:
                return resp.json()
            return {"status": f"http_{resp.status_code}"}
    except Exception as e:
        return {"status": f"unreachable: {e}"}


async def search_hf_models(
    pipeline_tag: str = "",
    query: str = "",
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Search HuggingFace for models by pipeline tag."""
    params = {"limit": limit, "sort": "downloads"}
    if pipeline_tag and pipeline_tag != "all":
        params["pipeline_tag"] = pipeline_tag
    if query:
        params["search"] = query

    url = "https://huggingface.co/api/models"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            models = resp.json()
            results = []
            for m in models:
                mapping = m.get("inference_provider_mapping", {}) or {}
                results.append(
                    {
                        "id": m["id"],
                        "pipeline_tag": m.get("pipeline_tag", "unknown"),
                        "downloads": m.get("downloads", 0),
                        "likes": m.get("likes", 0),
                        "inference_providers": bool(mapping),
                        "library_name": m.get("library_name", ""),
                    }
                )
            return results
    except Exception:
        return []


# ── Routes ─────────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Health info
    bridge_info = await check_bridge()
    bridge_status = bridge_info.get("status", "unreachable")

    space_details = {}
    spaces_healthy = 0
    for name, info in SPACES.items():
        hc = await check_hf_space(info["id"])
        space_details[name] = hc
        if hc.get("status") == "RUNNING":
            spaces_healthy += 1

    # Model stats
    models = await search_hf_models("text-to-image", limit=5)
    latest_name = models[0]["id"].split("/")[-1] if models else "none"

    # Output stats
    output_count = 0
    output_size = "0"
    output_last = "N/A"
    if OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob("*.json"))
        output_count = len(files)
        total_size = sum(f.stat().st_size for f in files)
        output_size = (
            f"{total_size / 1024 / 1024:.1f} MB"
            if total_size > 1024 * 1024
            else f"{total_size / 1024:.1f} KB"
        )
        if files:
            output_last = datetime.fromtimestamp(
                max(f.stat().st_mtime for f in files)
            ).strftime("%Y-%m-%d %H:%M")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "health": {
                "bridge": bridge_status,
                "spaces_healthy": spaces_healthy,
                "spaces_total": len(SPACES),
                "serverless": True,
                "space_details": space_details,
            },
            "spaces": SPACES,
            "model_stats": {
                "image": len(await search_hf_models("text-to-image", limit=3)),
                "video": len(await search_hf_models("text-to-video", limit=3)),
                "lora": len(CURATED_LORAS),
                "latest_name": latest_name,
            },
            "workflow_stats": {
                "total": 1,
                "nodes": bridge_info.get("workflow_nodes", 0) if bridge_status == "ok" else 0,
                "healthy": bridge_status == "ok",
            },
            "gpu_stats": {"available": 0, "active": 0},
            "output_stats": {
                "count": output_count,
                "size": output_size,
                "last": output_last,
            },
        },
    )


@app.get("/models", response_class=HTMLResponse)
async def models_page(
    request: Request,
    query: str = Query(""),
    pipeline: str = Query("all"),
):
    image_models = await search_hf_models("text-to-image", query, limit=24)
    video_models = await search_hf_models("text-to-video", query, limit=16)
    i2v_models = await search_hf_models("image-to-video", query, limit=12)
    other_models = await search_hf_models(
        "image-to-image" if not query else "", query, limit=8
    )

    return templates.TemplateResponse(
        request,
        "models.html",
        {
            "request": request,
            "query": query,
            "pipeline": pipeline,
            "models": {
                "image": image_models,
                "video": video_models,
                "i2v": i2v_models,
                "other": other_models,
            },
        },
    )


@app.get("/models/search", response_class=HTMLResponse)
async def models_search(
    request: Request,
    q: str = Query(""),
    pipeline: str = Query("all"),
):
    # Redirect to main models page with query
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=f"/models?query={q}&pipeline={pipeline}")


@app.get("/lora", response_class=HTMLResponse)
async def lora_page(request: Request):
    return templates.TemplateResponse(
        request,
        "lora.html",
        {
            "request": request,
            "loras": CURATED_LORAS,
            "checkpoints": CURATED_CHECKPOINTS,
        },
    )


@app.get("/comfyui", response_class=HTMLResponse)
async def comfyui_page(request: Request):
    return templates.TemplateResponse(
        request,
        "comfyui.html",
        {
            "request": request,
            "workflows": COMFYUI_WORKFLOWS,
        },
    )


@app.post("/comfyui/deploy")
async def comfyui_deploy(template: str = Form(...)):
    return HTMLResponse(
        f"""<div class="card" style="margin-top:16px;">
        <h3>🚀 Deploying: {template}</h3>
        <p class="text-muted">Deployment command generated. Use RunPod or Vast.ai to deploy (see GPU tab).</p>
        <pre>
# Deploy this workflow via RunPod:
# 1. Go to GPU tab
# 2. Enter RunPod API key
# 3. Select template and GPU
# 4. Click Deploy

# Or for local ComfyUI:
# 1. Install ComfyUI
# 2. Download workflow JSON
# 3. Load in ComfyUI
        </pre>
        </div>"""
    )


@app.get("/comfyui/workflow/{wf_id}")
async def comfyui_workflow_detail(wf_id: str):
    wf = next((w for w in COMFYUI_WORKFLOWS if w["id"] == wf_id), None)
    if not wf:
        return HTMLResponse("<div class='card'>Workflow not found</div>")

    return HTMLResponse(
        f"""<div class="card" style="margin-top:16px;">
        <h3>{wf['name']}</h3>
        <p>{wf['description']}</p>
        <pre style="font-size:12px;">
Resolution: {wf['resolution']}
Steps: {wf['steps']}
VRAM: {wf['vram']}
Model: {wf['model']}

Workflow JSON can be exported from ComfyUI once deployed.
        </pre>
        </div>"""
    )


@app.post("/comfyui/deploy/runpod")
async def comfyui_deploy_runpod(
    runpod_key: str = Form(...),
    runpod_template: str = Form(...),
    runpod_gpu: str = Form(...),
):
    # Generate deployment command
    return HTMLResponse(
        f"""<div class="card" style="margin-top:16px;border-color:var(--green);">
        <h3 class="text-green">✅ Deployment Script Generated</h3>
        <pre style="font-size:12px;">
# RunPod ComfyUI Deployment
# Template: {runpod_template}
# GPU: {runpod_gpu}

# 1. Install RunPod SDK:
pip install runpod

# 2. Deploy:
python3 << 'EOF'
import runpod
runpod.api_key = "{runpod_key[:6]}..."
endpoint = runpod.Endpoint.create(
    name="content-pipeline-comfyui",
    template_id="{runpod_template}",
    gpu_type_ids=["{runpod_gpu}"],
    max_workers=1,
    idle_timeout=30,
)
print(f"Ready! Endpoint: {{endpoint.id}}")
EOF

# 3. Test your endpoint:
curl -X POST https://api.runpod.io/v2/endpoints/YOUR_ENDPOINT_ID/runsync \\
  -H "Authorization: Bearer {runpod_key[:6]}..." \\
  -H "Content-Type: application/json" \\
  -d '{{"input": {{"workflow": "YOUR_WORKFLOW_JSON"}}}}'
        </pre>
        </div>"""
    )


@app.get("/workflows", response_class=HTMLResponse)
async def workflows_page(request: Request):
    bridge_info = await check_bridge()
    bridge_healthy = bridge_info.get("status") == "ok"
    wf_name = bridge_info.get("workflow_name", "N/A")
    wf_nodes = bridge_info.get("workflow_nodes", 0)

    # Get sessions
    sessions = {}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{BRIDGE_URL}/sessions")
            if resp.status_code == 200:
                sessions = resp.json()
    except Exception:
        pass

    # Get node info
    nodes = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{BRIDGE_URL}/workflow")
            if resp.status_code == 200:
                wf_data = resp.json()
                nodes = wf_data.get("nodes", [])
    except Exception:
        pass

    return templates.TemplateResponse(
        request,
        "workflows.html",
        {
            "request": request,
            "bridge_healthy": bridge_healthy,
            "workflow_name": wf_name,
            "workflow_nodes": wf_nodes,
            "nodes": nodes,
            "sessions": sessions,
        },
    )


@app.post("/workflows/run")
async def workflows_run(
    wf_topic: str = Form("test prompt"),
    wf_platform: str = Form("Twitter/X (NSFW)"),
    wf_nsfw: str = Form("true"),
    wf_intensity: str = Form("Explicit"),
):
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            payload = {
                "node_name": None,
                "inputs": {
                    "topic": wf_topic,
                    "platform": wf_platform,
                    "nsfw_mode": wf_nsfw == "true",
                    "intensity": wf_intensity,
                },
            }
            resp = await client.post(f"{BRIDGE_URL}/execute", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return HTMLResponse(
                    f"""<div class="card" style="margin-top:16px;border-color:var(--green);">
                    <h3>✅ Execution Complete</h3>
                    <pre style="font-size:12px;">{json.dumps(data, indent=2)}</pre>
                    </div>"""
                )
            else:
                return HTMLResponse(
                    f"""<div class="card" style="margin-top:16px;border-color:var(--red);">
                    <h3 class="text-red">❌ Bridge Error: {resp.status_code}</h3>
                    <pre>{resp.text[:500]}</pre>
                    </div>"""
                )
    except Exception as e:
        return HTMLResponse(
            f"""<div class="card" style="margin-top:16px;border-color:var(--red);">
            <h3 class="text-red">❌ Error</h3>
            <pre>{e}</pre>
            </div>"""
        )


@app.post("/workflows/validate")
async def workflows_validate(
    wf_topic: str = Form("test prompt"),
    wf_platform: str = Form("Twitter/X (NSFW)"),
    wf_nsfw: str = Form("true"),
    wf_intensity: str = Form("Explicit"),
):
    bridge_info = await check_bridge()
    space_checks = {}
    for name, info in SPACES.items():
        space_checks[name] = await check_hf_space(info["id"])

    html = f"""<div class="card" style="margin-top:16px;">
    <h3>🔍 Pre-Flight Validation</h3>
    <table>
        <thead>
            <tr><th>Check</th><th>Status</th><th>Detail</th></tr>
        </thead>
        <tbody>
            <tr>
                <td>Bridge</td>
                <td><span class="badge badge-{'healthy' if bridge_info.get('status')=='ok' else 'down'}">{'✅' if bridge_info.get('status')=='ok' else '❌'}</span></td>
                <td>{bridge_info.get('status','unreachable')}</td>
            </tr>"""
    for name, hc in space_checks.items():
        s = hc.get("status", "unknown")
        badge = (
            "healthy"
            if s == "RUNNING"
            else "down"
            if s in ("RUNTIME_ERROR", "BUILD_ERROR", "error")
            else "degraded"
        )
        html += f"""
            <tr>
                <td>{name}</td>
                <td><span class="badge badge-{badge}">{'✅' if s=='RUNNING' else '⚠' if s=='SLEEPING' else '❌'} {s}</span></td>
                <td class="text-muted">{hc.get('latency',0):.2f}s</td>
            </tr>"""
    healthy_count = sum(
        1 for hc in space_checks.values() if hc.get("status") == "RUNNING"
    )
    html += f"""
        </tbody>
    </table>
    <div class="flex mt-2">
        <span>{healthy_count}/{len(SPACES)} spaces healthy</span>
        <span style="margin-left:auto;font-size:13px;" class="text-muted">
        Topic: "{wf_topic}" · {wf_platform} · {wf_intensity}
        </span>
    </div>
    </div>"""
    return HTMLResponse(html)


@app.get("/workflows/session/{session_id}")
async def workflow_session(session_id: str):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{BRIDGE_URL}/session/{session_id}")
            if resp.status_code == 200:
                data = resp.json()
                return HTMLResponse(
                    f"""<div class="card" style="margin-top:16px;">
                    <h3>Session: {session_id[:16]}...</h3>
                    <pre>{json.dumps(data, indent=2)}</pre>
                    </div>"""
                )
    except Exception:
        pass
    return HTMLResponse("<div class='card'>Session not found</div>")


@app.get("/gpu", response_class=HTMLResponse)
async def gpu_page(request: Request):
    return templates.TemplateResponse(request, "gpu.html", {"request": request})


# ── Grok Routes ──────────────────────────────────────────────────────────────


# ── Create Page ───────────────────────────────────────────────────────────────

@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    from content_gen import list_recent_outputs
    recent = list_recent_outputs(12)
    return templates.TemplateResponse(
        request, "create.html",
        {"request": request, "recent_outputs": recent},
    )


@app.post("/create/generate")
async def create_generate(
    topic: str = Form(...),
    image_prompt: str = Form(""),
    platform: str = Form("twitter"),
    tone: str = Form("engaging"),
    want_thread: str = Form("off"),
    full_size: str = Form("1024x1024"),
):
    from content_gen import create_content_piece

    try:
        w, h = full_size.split("x")
        width, height = int(w), int(h)
    except (ValueError, AttributeError):
        width, height = 1024, 1024

    piece = create_content_piece(
        topic=topic,
        image_prompt=image_prompt,
        platform=platform,
        tone=tone,
        generate_thread=(want_thread == "on"),
        width=width,
        height=height,
    )

    html = f'<div class="card" style="margin-top:16px;border-color:var(--green);">'
    html += f'<h3 class="text-green">✅ Content Generated</h3>'
    html += f'<div class="text-muted" style="font-size:12px;">ID: {piece.id} · Backend: {piece.backend}</div>'

    # Image
    if piece.image_url:
        html += f'<div style="margin:12px 0;"><img src="{piece.image_url}" style="max-width:400px;border-radius:8px;border:1px solid var(--border);" alt="Generated"></div>'
        if piece.image_path:
            html += f'<div class="text-muted" style="font-size:12px;">📁 {piece.image_path}</div>'

    # Hook
    html += f'<div style="margin:12px 0;padding:12px;background:var(--bg);border-radius:8px;border:1px solid var(--border);">'
    html += f'<div style="font-size:12px;color:var(--text2);margin-bottom:4px;">🐦 Hook ({len(piece.hook)} chars)</div>'
    html += f'<div>{piece.hook}</div></div>'

    # Caption
    html += f'<div style="margin:12px 0;padding:12px;background:var(--bg);border-radius:8px;border:1px solid var(--border);">'
    html += f'<div style="font-size:12px;color:var(--text2);margin-bottom:4px;">📝 Caption ({platform})</div>'
    html += f'<div>{piece.caption}</div></div>'

    # Hashtags
    if piece.hashtags:
        html += f'<div style="margin:8px 0;"><span class="text-accent" style="font-size:13px;">{piece.hashtags}</span></div>'

    # Thread
    if piece.thread:
        html += f'<div style="margin:12px 0;padding:12px;background:var(--bg);border-radius:8px;border:1px solid var(--border);">'
        html += f'<div style="font-size:12px;color:var(--text2);margin-bottom:8px;">🧵 Thread ({len(piece.thread)} tweets)</div>'
        for i, tweet in enumerate(piece.thread):
            html += f'<div style="padding:8px;border-bottom:1px solid var(--border);font-size:13px;">{i+1}. {tweet}</div>'
        html += '</div>'

    # Multi-platform
    html += '<div style="margin:12px 0;" data-tabs>'
    html += '<div class="tabs">'
    for p in ["twitter", "instagram", "tiktok", "telegram"]:
        html += f'<div class="tab" data-tab="tab-{p}">{p}</div>'
    html += '</div>'
    for p in ["twitter", "instagram", "tiktok", "telegram"]:
        adapted = piece.platform_ready.get(p, "")
        html += f'<div class="tab-content" id="tab-{p}"><div style="padding:12px;background:var(--bg);border-radius:8px;font-size:13px;">{adapted}</div></div>'
    html += '</div>'

    html += '</div>'
    return HTMLResponse(html)


@app.post("/create/image-only")
async def create_image_only(
    prompt: str = Form(...),
    img_size: str = Form("1024x1024"),
):
    """Generate just an image — fastest path."""
    from content_gen import generate_image_turbo
    try:
        w, h = img_size.split("x")
        width, height = int(w), int(h)
    except (ValueError, AttributeError):
        width, height = 1024, 1024
    result = generate_image_turbo(prompt, width=width, height=height)

    if result.success and result.images:
        html = f'<div class="card" style="margin-top:16px;border-color:var(--green);"><h3 class="text-green">🖼 Image Ready</h3>'
        for url in result.images:
            html += f'<img src="{url}" style="max-width:400px;border-radius:8px;margin:8px 0;" alt="Generated">'
        if result.content and result.content.image_path:
            html += f'<div class="text-muted" style="font-size:12px;">📁 {result.content.image_path}</div>'
        html += '</div>'
        return HTMLResponse(html)

    return HTMLResponse(f'<div class="card" style="border-color:var(--red);"><h3 class="text-red">❌ Image Failed</h3><p>{result.error}</p></div>')


@app.post("/create/caption-only")
async def create_caption_only(
    topic: str = Form(...),
    platform: str = Form("twitter"),
    tone: str = Form("engaging"),
):
    """Generate just a caption — text only, instant."""
    from content_gen import generate_caption, generate_hashtags
    caption = generate_caption(topic, platform=platform, tone=tone)
    hashtags = generate_hashtags(topic)

    html = f'<div class="card" style="margin-top:16px;border-color:var(--green);"><h3 class="text-green">📝 Caption Ready</h3>'
    html += f'<div style="padding:12px;background:var(--bg);border-radius:8px;margin:8px 0;">{caption}</div>'
    html += f'<div class="text-accent" style="font-size:13px;">{hashtags}</div>'
    html += '</div>'
    return HTMLResponse(html)


# ── Distribute Page ──────────────────────────────────────────────────────────

@app.get("/distribute", response_class=HTMLResponse)
async def distribute_page(request: Request):
    return templates.TemplateResponse(request, "distribute.html", {"request": request})


@app.get("/grok", response_class=HTMLResponse)
async def grok_page(request: Request):
    from xai_grok import XAI_API_KEY

    return templates.TemplateResponse(
        request,
        "grok.html",
        {
            "request": request,
            "api_configured": bool(XAI_API_KEY),
        },
    )


@app.post("/grok/generate/image")
async def grok_generate_image(
    img_prompt: str = Form(...),
    img_n: str = Form("1"),
    img_ar: str = Form("1:1"),
):
    from xai_grok import generate_image

    try:
        n = int(img_n)
    except ValueError:
        n = 1

    results = generate_image(img_prompt, n=n, aspect_ratio=img_ar)

    html = '<div class="card" style="margin-top:16px;"><h3>🖼 Image Results</h3>'
    html += '<div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(250px,1fr));">'

    for i, img in enumerate(results):
        if img.success and img.url:
            # We'll show a direct link since we can't embed images easily
            html += f"""
            <div style="background:var(--bg);padding:12px;border-radius:8px;border:1px solid var(--border);">
                <div style="font-size:13px;font-weight:600;margin-bottom:6px;">Image {i+1}</div>
                <a href="{img.url}" target="_blank" class="btn btn-sm" style="margin-bottom:4px;">🔗 Open Image</a>
                <div class="text-muted" style="font-size:11px;word-break:break-all;">{img.url[:80]}...</div>
            </div>"""
        else:
            html += f'<div style="color:var(--red);padding:12px;">❌ {img.error}</div>'

    html += "</div></div>"
    return HTMLResponse(html)


@app.post("/grok/generate/video")
async def grok_generate_video(
    vid_prompt: str = Form(...),
    vid_duration: str = Form("10"),
    vid_ar: str = Form("16:9"),
    vid_res: str = Form("720p"),
):
    from xai_grok import generate_video, download_to_file

    try:
        duration = int(vid_duration)
    except ValueError:
        duration = 10

    result = generate_video(
        vid_prompt,
        duration=duration,
        aspect_ratio=vid_ar,
        resolution=vid_res,
        poll_timeout=600,
    )

    if result.success and result.url:
        # Try to download locally
        local = download_to_file(result.url)
        local_str = f"📁 {local}" if local else ""

        html = f"""<div class="card" style="margin-top:16px;border-color:var(--green);">
        <h3 class="text-green">🎬 Video Generated</h3>
        <p style="margin:8px 0;">Duration: {duration}s · {vid_ar} · {vid_res}</p>
        <div class="flex gap-2">
            <a href="{result.url}" target="_blank" class="btn btn-primary">▶ Watch Video</a>
        </div>
        <div class="mt-2 text-muted" style="font-size:12px;word-break:break-all;">
            URL: {result.url}<br>
            {local_str}
        </div>
        </div>"""
        return HTMLResponse(html)

    return HTMLResponse(
        f"""<div class="card" style="margin-top:16px;border-color:var(--red);">
        <h3 class="text-red">❌ Video Generation Failed</h3>
        <p>{result.error}</p>
        </div>"""
    )


@app.post("/gpu/runpod/deploy")
async def gpu_runpod_deploy(
    rp_key: str = Form(...),
    rp_template: str = Form(...),
    rp_gpu: str = Form(...),
    rp_workers: str = Form("1"),
    rp_idle: str = Form("30"),
):
    return HTMLResponse(
        f"""<div class="card" style="margin-top:16px;border-color:var(--green);">
        <h3 class="text-green">🚀 RunPod Deployment Command</h3>
        <pre style="font-size:12px;">
export RUNPOD_API_KEY="{rp_key[:8]}..."

python3 << 'PYEOF'
import runpod
runpod.api_key = "{rp_key[:8]}..."
endpoint = runpod.Endpoint.create(
    name="content-pipeline-comfyui",
    template_id="{rp_template}",
    gpu_type_ids=["{rp_gpu}"],
    max_workers={rp_workers},
    idle_timeout={rp_idle},
)
print(f"Endpoint: {{endpoint.id}}")
print(f"Status: {{endpoint.status}}")
PYEOF

# Test after deployment:
# curl https://api.runpod.io/v2/endpoints/YOUR_ENDPOINT/health \\
#   -H "Authorization: Bearer $RUNPOD_API_KEY"
        </pre>
        </div>"""
    )


@app.post("/gpu/vast/search")
async def gpu_vast_search(
    vast_key: str = Form(...),
    vast_vram: str = Form("24"),
    vast_price: str = Form("0.50"),
):
    return HTMLResponse(
        f"""<div class="card" style="margin-top:16px;">
        <h3>🔍 Vast.ai Instance Search</h3>
        <p class="text-muted">Search for instances with &ge;{vast_vram} GB VRAM at &le;${vast_price}/hr</p>
        <pre style="font-size:12px;">
# Search Vast.ai for ComfyUI instances:
curl -s -H "Authorization: Bearer {vast_key[:8]}..." \\
  "https://console.vast.ai/api/v0/bundles?search=comfyui&gpu_ram>={vast_vram}&min_bid<={vast_price}" \\
  | python3 -c "
import sys,json
data=json.load(sys.stdin)
for offer in data.get('offers',[])[:10]:
    gpu=offer.get('gpu_name','?')
    price=offer.get('min_bid',0)
    ram=offer.get('gpu_ram',0)
    uid=offer.get('id','?')
    print(f'  {gpu:20s} \${price:>5.2f}/hr  {ram:>4} GB  ID:{uid}')
"
        </pre>
        <div class="mt-2 text-muted">
        Tip: Look for instances with "comfyui" in the image name for pre-installed setups.
        </div>
        </div>"""
    )


@app.get("/outputs", response_class=HTMLResponse)
async def outputs_page(request: Request):
    outputs = []
    if OUTPUT_DIR.exists():
        files = sorted(
            OUTPUT_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True
        )[:24]
        for f in files:
            try:
                data = json.loads(f.read_text())
                outputs.append(
                    {
                        "filename": f.name,
                        "platform": data.get("platform", "?"),
                        "caption": data.get("caption", "") or "",
                        "time": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "size": (
                            f"{f.stat().st_size / 1024:.1f} KB"
                            if f.stat().st_size > 1024
                            else f"{f.stat().st_size} B"
                        ),
                    }
                )
            except Exception:
                pass

    return templates.TemplateResponse(
        request,
        "outputs.html", {"request": request, "outputs": outputs}
    )


@app.get("/outputs/{filename}")
async def output_file(filename: str):
    from fastapi.responses import FileResponse

    filepath = OUTPUT_DIR / filename
    if filepath.exists():
        return FileResponse(str(filepath))
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/_refresh_health")
async def refresh_health():
    bridge_info = await check_bridge()
    bridge_healthy = bridge_info.get("status") == "ok"

    spaces = {}
    for name, info in SPACES.items():
        spaces[name] = await check_hf_space(info["id"])
    spaces_healthy = sum(
        1 for hc in spaces.values() if hc.get("status") == "RUNNING"
    )

    html = f"""<div class="status-bar" id="status-bar">
    <div class="status-item">
        <span class="status-dot {'green' if bridge_healthy else 'red'}"></span>
        Bridge: {'healthy' if bridge_healthy else bridge_info.get('status','error')}
    </div>
    <div class="status-item">
        <span class="status-dot {'green' if spaces_healthy > 0 else 'red'}"></span>
        Spaces: {spaces_healthy}/{len(SPACES)} healthy
    </div>
    <div class="status-item">
        <span class="status-dot green"></span>
        API: Available
    </div>
    <div class="status-item text-muted" style="margin-left:auto;">
        <span class="spinner" style="display:none;" id="refresh-spinner"></span>
    </div>
</div>"""
    return HTMLResponse(html)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[dashboard] Starting Content Pipeline Web Dashboard")
    print(f"[dashboard] URL: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"[dashboard] Bridge: {BRIDGE_URL}")
    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT, log_level="info")
