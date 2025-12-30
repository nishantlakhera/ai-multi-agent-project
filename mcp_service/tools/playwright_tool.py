from typing import Dict, Any, List, Optional
from pathlib import Path
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect
from utils.logger import logger

def _dismiss_cookie_banner(page) -> None:
    for label in ("Accept all", "Reject all"):
        try:
            button = page.get_by_role("button", name=label)
            if button.is_visible(timeout=500):
                button.click()
                logger.info(f"[playwright_tool] Dismissed cookie banner with '{label}'")
                return
        except Exception:
            continue

def _resolve_locator(page, target: str):
    if target.startswith("role="):
        parts = target.split(" ", 1)
        role = parts[0].split("=", 1)[1]
        name = None
        if len(parts) > 1 and parts[1].startswith("name="):
            name = parts[1].split("=", 1)[1].strip('"')
        allowed_roles = {"textbox", "button", "link", "checkbox", "radio", "combobox", "option"}
        if role not in allowed_roles:
            logger.warning(f"[playwright_tool] Invalid role '{role}', falling back to label/text")
            if name:
                logger.info(f"[playwright_tool] Locator fallback=label name={name!r}")
                return page.get_by_label(name)
            logger.info(f"[playwright_tool] Locator fallback=text value={role!r}")
            return page.get_by_text(role)
        logger.info(f"[playwright_tool] Locator role={role!r} name={name!r}")
        return page.get_by_role(role, name=name) if name else page.get_by_role(role)
    if target.startswith("label="):
        label = target.split("=", 1)[1].strip('"')
        logger.info(f"[playwright_tool] Locator label={label!r}")
        return page.get_by_label(label)
    if target.startswith("text="):
        text = target.split("=", 1)[1].strip('"')
        logger.info(f"[playwright_tool] Locator text={text!r}")
        return page.get_by_text(text)
    if target.startswith("placeholder="):
        text = target.split("=", 1)[1].strip('"')
        logger.info(f"[playwright_tool] Locator placeholder={text!r}")
        return page.get_by_placeholder(text)
    if target.startswith("css="):
        selector = target.split("=", 1)[1]
        logger.info(f"[playwright_tool] Locator css={selector!r}")
        return page.locator(selector)
    logger.info(f"[playwright_tool] Locator raw={target!r}")
    return page.locator(target)

def _parse_role_target(target: str):
    if not target.startswith("role="):
        return None, None
    parts = target.split(" ", 1)
    role = parts[0].split("=", 1)[1]
    name = None
    if len(parts) > 1 and parts[1].startswith("name="):
        name = parts[1].split("=", 1)[1].strip('"')
    return role, name

def _click_fallbacks(page, name: str) -> bool:
    escaped = name.replace('"', '\\"')
    pattern = re.sub(r"\s+", r"\\s*", re.escape(name))
    candidates = [
        ("role=button partial", lambda: page.get_by_role("button", name=name, exact=False).click(timeout=3000)),
        ("role=link", lambda: page.get_by_role("link", name=name).click(timeout=3000)),
        ("text", lambda: page.get_by_text(name, exact=False).click(timeout=3000)),
        ("text regex", lambda: page.locator(f"text=/{pattern}/i").first.click(timeout=3000)),
        ("css text", lambda: page.locator(f'a:has-text("{escaped}"), button:has-text("{escaped}")').first.click(timeout=3000)),
    ]
    for label, action in candidates:
        try:
            logger.info(f"[playwright_tool] Click fallback via {label} for '{name}'")
            action()
            return True
        except Exception:
            continue
    return False

def _make_url(target: str, base_url: Optional[str]) -> str:
    if target.startswith("http://") or target.startswith("https://"):
        return target
    if base_url:
        return base_url.rstrip("/") + "/" + target.lstrip("/")
    return target

def run_dsl_plan(plan: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    steps = plan.get("steps", [])
    output_dir = Path(os.getenv("TEST_RUN_OUTPUT_DIR", "logs/test_runs")) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    timeout_ms = int(os.getenv("TEST_RUN_STEP_TIMEOUT_MS", "15000"))
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    slow_mo_ms = int(os.getenv("PLAYWRIGHT_SLOW_MO_MS", "0"))
    pause_on_start = os.getenv("PLAYWRIGHT_PAUSE_ON_START", "").lower() == "true" or bool(os.getenv("PWDEBUG"))

    step_logs: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(timeout_ms)
        if pause_on_start and not headless:
            page.pause()

        for idx, step in enumerate(steps, 1):
            action = step.get("action")
            target = step.get("target", "")
            value = step.get("value")

            step_logs.append({
                "step": idx,
                "action": action,
                "target": target,
                "status": "running",
            })

            try:
                if action in {"click", "fill", "select", "assert_visible", "assert_text"}:
                    _dismiss_cookie_banner(page)

                if action == "goto":
                    page.goto(_make_url(target or value or "", plan.get("base_url")))
                elif action == "click":
                    try:
                        _resolve_locator(page, target).click()
                    except PlaywrightTimeoutError as e:
                        role, name = _parse_role_target(target)
                        if role == "button" and name:
                            clicked = _click_fallbacks(page, name)
                            if not clicked:
                                raise PlaywrightTimeoutError(
                                    f"Unable to click '{name}'. Provide an explicit selector."
                                )
                        else:
                            raise e
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
                    artifacts.append({"type": "screenshot", "path": str(path), "step": idx})
                else:
                    raise ValueError(f"Unknown action: {action}")

                step_logs.append({
                    "step": idx,
                    "action": action,
                    "target": target,
                    "status": "passed",
                })

            except PlaywrightTimeoutError as e:
                logger.error(f"[playwright_tool] Timeout on step {idx}: {e}")
                path = output_dir / f"step-{idx}-timeout.png"
                page.screenshot(path=str(path), full_page=True)
                artifacts.append({"type": "screenshot", "path": str(path), "step": idx})
                return {"status": "failed", "failed_step": idx, "error": str(e), "steps": step_logs, "artifacts": artifacts}
            except Exception as e:
                logger.error(f"[playwright_tool] Error on step {idx}: {e}")
                path = output_dir / f"step-{idx}-error.png"
                page.screenshot(path=str(path), full_page=True)
                artifacts.append({"type": "screenshot", "path": str(path), "step": idx})
                return {"status": "failed", "failed_step": idx, "error": str(e), "steps": step_logs, "artifacts": artifacts}

        context.close()
        browser.close()

    return {"status": "passed", "failed_step": None, "error": None, "steps": step_logs, "artifacts": artifacts}
