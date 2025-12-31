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
            name = parts[1].split("=", 1)[1].strip('"').strip("'")
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
        label = target.split("=", 1)[1].strip('"').strip("'")
        logger.info(f"[playwright_tool] Locator label={label!r}")
        return page.get_by_label(label)
    if target.startswith("text="):
        text = target.split("=", 1)[1].strip('"').strip("'")
        logger.info(f"[playwright_tool] Locator text={text!r}")
        return page.get_by_text(text)
    if target.startswith("placeholder="):
        text = target.split("=", 1)[1].strip('"').strip("'")
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
        name = parts[1].split("=", 1)[1].strip('"').strip("'")
    return role, name

def _parse_text_target(target: str) -> Optional[str]:
    if target.startswith("text="):
        return target.split("=", 1)[1].strip('"').strip("'")
    return None

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

def _click_first_visible(locator) -> bool:
    try:
        handles = locator.element_handles()
    except Exception:
        return False
    for handle in handles:
        try:
            if not handle.is_visible():
                continue
            handle.scroll_into_view_if_needed(timeout=2000)
            handle.click(timeout=3000)
            return True
        except Exception:
            continue
    return False

def _click_text_fallbacks(page, text: str) -> bool:
    escaped = text.replace('"', '\\"')
    candidates = [
        page.get_by_role("link", name=text, exact=False),
        page.get_by_role("button", name=text, exact=False),
        page.locator(f'a:has-text("{escaped}")'),
        page.locator(f'button:has-text("{escaped}")'),
        page.locator(f'text="{escaped}"'),
    ]
    for locator in candidates:
        if _click_first_visible(locator):
            return True
    return False

def _wait_for_settle(page) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        return
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        return

def _click_option_by_text(page, value: str) -> bool:
    value = value.strip()
    if not value:
        return False

    locator_candidates = [
        page.get_by_role("option", name=value, exact=False).first,
        page.get_by_text(value, exact=False).first,
        page.locator(f'[role="option"]:has-text("{value}")').first,
        page.locator(f'li:has-text("{value}")').first,
    ]

    for locator in locator_candidates:
        try:
            locator.scroll_into_view_if_needed(timeout=2000)
            locator.click(timeout=3000)
            return True
        except Exception:
            continue

    return False

def _click_option_by_text_in(container, value: str) -> bool:
    value = value.strip()
    if not value:
        return False

    locator_candidates = [
        container.locator(f'[class*="option"]:has-text("{value}")').first,
        container.locator(f'[role="option"]:has-text("{value}")').first,
        container.locator(f'div:has-text("{value}")').first,
        container.locator(f'li:has-text("{value}")').first,
        container.get_by_role("option", name=value, exact=False).first,
        container.get_by_text(value, exact=False).first,
    ]

    for locator in locator_candidates:
        try:
            if not locator.is_visible():
                continue
            locator.scroll_into_view_if_needed(timeout=2000)
            locator.click(timeout=3000)
            return True
        except Exception:
            continue

    return False

def _scroll_dropdown_for_option(page, value: str, trigger=None) -> bool:
    candidates = []
    if trigger is not None:
        try:
            control_id = trigger.get_attribute("aria-controls") or trigger.get_attribute("aria-owns")
            if control_id:
                candidates.append(page.locator(f"#{control_id}"))
        except Exception:
            pass
        try:
            candidates.append(
                trigger.locator(
                    "xpath=ancestor-or-self::*[contains(@class,'dropdown') or contains(@class,'select')][1]"
                )
            )
        except Exception:
            pass

    candidates.extend([
        page.locator('[role="listbox"]'),
        page.locator('ul[role="listbox"]'),
        page.locator('[class*="dropdown"][class*="menu"]'),
        page.locator('[class*="dropdown"][class*="list"]'),
        page.locator('[class*="dropdown"][class*="options"]'),
        page.locator('[class*="options-container"]'),
        page.locator('[class*="options"]'),
        page.locator('[class*="select"][class*="menu"]'),
    ])

    for container in candidates:
        try:
            container.first.wait_for(state="visible", timeout=500)
            box = container.first
            try:
                options_box = box.locator('[class*="options-container"]').first
                if options_box.is_visible(timeout=200):
                    box = options_box
            except Exception:
                pass
            for _ in range(16):
                option_locators = [
                    box.get_by_role("option", name=value, exact=False).first,
                    box.get_by_text(value, exact=False).first,
                    box.locator(f'[role="option"]:has-text("{value}")').first,
                    box.locator(f'li:has-text("{value}")').first,
                ]
                for option in option_locators:
                    try:
                        option.scroll_into_view_if_needed(timeout=1000)
                        option.click(timeout=2000)
                        return True
                    except Exception:
                        continue
                box.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")
            return False
        except Exception:
            continue
    return False

def _scroll_dropdown_for_option_in(container, value: str) -> bool:
    value = value.strip()
    if not value:
        return False

    try:
        container.wait_for(state="visible", timeout=500)
    except Exception:
        return False

    box = container
    try:
        options_box = box.locator('[class*="options-container"]').first
        if options_box.is_visible(timeout=200):
            box = options_box
    except Exception:
        pass

    try:
        scroll_height = box.evaluate("el => el.scrollHeight")
        client_height = box.evaluate("el => el.clientHeight")
        max_steps = max(8, int((scroll_height / max(client_height, 1)) + 2))
    except Exception:
        max_steps = 16

    for _ in range(max_steps):
        option_locators = [
            box.locator(f'[class*="option"]:has-text("{value}")').first,
            box.locator(f'[role="option"]:has-text("{value}")').first,
            box.locator(f'div:has-text("{value}")').first,
            box.locator(f'li:has-text("{value}")').first,
            box.get_by_role("option", name=value, exact=False).first,
            box.get_by_text(value, exact=False).first,
        ]
        for option in option_locators:
            try:
                if not option.is_visible():
                    continue
                option.scroll_into_view_if_needed(timeout=1000)
                option.click(timeout=2000)
                return True
            except Exception:
                continue
        try:
            box.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")
        except Exception:
            return False
    return False

def _find_native_select(page, locator, target: str):
    try:
        tag = locator.evaluate("el => el.tagName.toLowerCase()")
        if tag == "select":
            return locator
    except Exception:
        pass

    label_text = None
    if target.startswith("label="):
        label_text = target.split("=", 1)[1].strip('"').strip("'")

    select_candidates = []
    if label_text:
        label_loc = page.locator("label", has_text=label_text)
        select_candidates.append(
            label_loc.locator(
                "xpath=ancestor-or-self::*[contains(@class,'dropdown') or contains(@class,'select')][1]//select"
            )
        )
        select_candidates.append(label_loc.locator("xpath=following::select[1]"))

    try:
        labelledby = locator.get_attribute("aria-labelledby")
    except Exception:
        labelledby = None
    if labelledby:
        for label_id in labelledby.split():
            label_loc = page.locator(f"#{label_id}")
            select_candidates.append(
                label_loc.locator(
                    "xpath=ancestor-or-self::*[contains(@class,'dropdown') or contains(@class,'select')][1]//select"
                )
            )
            select_candidates.append(label_loc.locator("xpath=following::select[1]"))

    select_candidates.extend([
        locator.locator(
            "xpath=ancestor-or-self::*[contains(@class,'dropdown') or contains(@class,'select')][1]//select"
        ),
        locator.locator("xpath=ancestor-or-self::*[self::form or self::div or self::section][1]//select"),
        locator.locator("xpath=following::select[1]"),
    ])

    for candidate in select_candidates:
        try:
            if candidate.count() < 1:
                continue
            select_loc = candidate.first
            select_loc.wait_for(state="attached", timeout=500)
            return select_loc
        except Exception:
            continue
    return None

def _get_options_container(root):
    if root is None:
        return None
    candidates = [
        root.locator('[class*="options-container"]'),
        root.locator('[role="listbox"]'),
        root.locator('[class*="options"]'),
    ]
    for candidate in candidates:
        try:
            if candidate.count() < 1:
                continue
            container = candidate.first
            if container.is_visible():
                return container
        except Exception:
            continue
    return root

def _ensure_dropdown_open(trigger, options_container) -> None:
    if options_container is None:
        return
    try:
        if options_container.is_visible():
            return
    except Exception:
        pass
    try:
        trigger.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        trigger.click(timeout=3000)
    except Exception:
        try:
            trigger.press("Enter", timeout=2000)
        except Exception:
            return
    try:
        options_container.wait_for(state="visible", timeout=3000)
    except Exception:
        return

def _find_dropdown_trigger(select_locator):
    try:
        root = select_locator.locator(
            "xpath=ancestor-or-self::*[contains(@class,'dropdown') or contains(@class,'select')][1]"
        )
    except Exception:
        return None, None

    try:
        if root.count() < 1:
            return None, None
    except Exception:
        return None, None

    root = root.first
    candidates = [
        root.locator('[aria-expanded]'),
        root.locator('[role="combobox"]'),
        root.locator('[class*="dropdown__container"]'),
        root.locator("button"),
    ]
    for candidate in candidates:
        try:
            if candidate.count() > 0:
                return candidate.first, root
        except Exception:
            continue
    return None, root

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
                        _wait_for_settle(page)
                    except PlaywrightTimeoutError as e:
                        role, name = _parse_role_target(target)
                        if role == "button" and name:
                            clicked = _click_fallbacks(page, name)
                            if not clicked:
                                raise PlaywrightTimeoutError(
                                    f"Unable to click '{name}'. Provide an explicit selector."
                                )
                            _wait_for_settle(page)
                        else:
                            locator = _resolve_locator(page, target)
                            if _click_first_visible(locator):
                                _wait_for_settle(page)
                            else:
                                text_target = _parse_text_target(target)
                                if text_target and _click_text_fallbacks(page, text_target):
                                    _wait_for_settle(page)
                                else:
                                    raise e
                    except Exception as e:
                        if "strict mode violation" in str(e).lower():
                            logger.info(f"[playwright_tool] Click fallback via first visible match for '{target}'")
                            locator = _resolve_locator(page, target)
                            if _click_first_visible(locator):
                                _wait_for_settle(page)
                            else:
                                text_target = _parse_text_target(target)
                                if text_target and _click_text_fallbacks(page, text_target):
                                    _wait_for_settle(page)
                                else:
                                    raise
                        elif "not visible" in str(e).lower():
                            locator = _resolve_locator(page, target)
                            if _click_first_visible(locator):
                                _wait_for_settle(page)
                            else:
                                text_target = _parse_text_target(target)
                                if text_target and _click_text_fallbacks(page, text_target):
                                    _wait_for_settle(page)
                                else:
                                    raise
                        else:
                            raise
                elif action == "fill":
                    _resolve_locator(page, target).fill(value or "")
                elif action == "select":
                    if not value:
                        raise ValueError("Select action missing value")
                    locator = _resolve_locator(page, target)
                    select_locator = _find_native_select(page, locator, target)
                    if select_locator is not None:
                        trigger, root = _find_dropdown_trigger(select_locator)
                        options_container = _get_options_container(root)
                        try:
                            select_locator.select_option(label=value, force=True)
                        except Exception:
                            try:
                                select_locator.select_option(value=value, force=True)
                            except Exception:
                                matched = select_locator.evaluate(
                                    """
                                    (el, desired) => {
                                        const options = Array.from(el.options || []);
                                        const match = options.find(opt =>
                                            opt.label === desired ||
                                            opt.text === desired ||
                                            opt.textContent === desired ||
                                            opt.value === desired
                                        );
                                        if (!match) {
                                            return false;
                                        }
                                        el.value = match.value;
                                        el.dispatchEvent(new Event("input", { bubbles: true }));
                                        el.dispatchEvent(new Event("change", { bubbles: true }));
                                        return true;
                                    }
                                    """,
                                    value,
                                )
                                if not matched:
                                    raise PlaywrightTimeoutError(
                                        f"Option '{value}' not found for target '{target}'"
                                    )
                        if trigger is not None and root is not None:
                            try:
                                trigger_text = trigger.inner_text(timeout=500)
                            except Exception:
                                trigger_text = ""
                            if value not in trigger_text:
                                _ensure_dropdown_open(trigger, options_container)
                                if not _click_option_by_text_in(options_container, value):
                                    _scroll_dropdown_for_option_in(options_container, value)
                    else:
                        locator.click()
                        if not _click_option_by_text(page, value) and not _scroll_dropdown_for_option(page, value, locator):
                            raise PlaywrightTimeoutError(
                                f"Option '{value}' not found for target '{target}'"
                            )
                    _wait_for_settle(page)
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
