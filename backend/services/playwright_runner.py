from typing import Dict, Any, Optional
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect
from config.settings import settings
from utils.logger import logger

def _resolve_locator(page, target: str):
    if target.startswith("role="):
        parts = target.split(" ", 1)
        role = parts[0].split("=", 1)[1]
        name = None
        if len(parts) > 1 and parts[1].startswith("name="):
            name = parts[1].split("=", 1)[1].strip('"')
        return page.get_by_role(role, name=name) if name else page.get_by_role(role)
    if target.startswith("label="):
        label = target.split("=", 1)[1].strip('"')
        return page.get_by_label(label)
    if target.startswith("text="):
        text = target.split("=", 1)[1].strip('"')
        return page.get_by_text(text)
    if target.startswith("placeholder="):
        text = target.split("=", 1)[1].strip('"')
        return page.get_by_placeholder(text)
    if target.startswith("css="):
        return page.locator(target.split("=", 1)[1])
    return page.locator(target)

def _make_url(target: str, base_url: Optional[str]) -> str:
    if target.startswith("http://") or target.startswith("https://"):
        return target
    if base_url:
        return base_url.rstrip("/") + "/" + target.lstrip("/")
    return target

def run_dsl_plan(plan: Dict[str, Any], run_id: str, store) -> Dict[str, Any]:
    steps = plan.get("steps", [])
    output_dir = Path(settings.TEST_RUN_OUTPUT_DIR) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(settings.TEST_RUN_STEP_TIMEOUT_MS)

        for idx, step in enumerate(steps, 1):
            action = step.get("action")
            target = step.get("target", "")
            value = step.get("value")

            store.add_step(run_id, {
                "step": idx,
                "action": action,
                "target": target,
                "status": "running",
            })

            try:
                if action == "goto":
                    page.goto(_make_url(target or value or "", plan.get("base_url")))
                elif action == "click":
                    _resolve_locator(page, target).click()
                elif action == "fill":
                    _resolve_locator(page, target).fill(value or "")
                elif action == "select":
                    _resolve_locator(page, target).select_option(value or "")
                elif action == "assert_visible":
                    expect(_resolve_locator(page, target)).to_be_visible()
                elif action == "assert_text":
                    expect(_resolve_locator(page, target)).to_contain_text(value or "")
                elif action == "screenshot":
                    name = value or f"step-{idx}"
                    path = output_dir / f"{name}.png"
                    page.screenshot(path=str(path), full_page=True)
                    store.add_artifact(run_id, {"type": "screenshot", "path": str(path), "step": idx})
                else:
                    raise ValueError(f"Unknown action: {action}")

                store.add_step(run_id, {
                    "step": idx,
                    "action": action,
                    "target": target,
                    "status": "passed",
                })

            except PlaywrightTimeoutError as e:
                logger.error(f"[playwright_runner] Timeout on step {idx}: {e}")
                path = output_dir / f"step-{idx}-timeout.png"
                page.screenshot(path=str(path), full_page=True)
                store.add_artifact(run_id, {"type": "screenshot", "path": str(path), "step": idx})
                return {"status": "failed", "failed_step": idx, "error": str(e)}
            except Exception as e:
                logger.error(f"[playwright_runner] Error on step {idx}: {e}")
                path = output_dir / f"step-{idx}-error.png"
                page.screenshot(path=str(path), full_page=True)
                store.add_artifact(run_id, {"type": "screenshot", "path": str(path), "step": idx})
                return {"status": "failed", "failed_step": idx, "error": str(e)}

        context.close()
        browser.close()

    return {"status": "passed", "failed_step": None, "error": None}
