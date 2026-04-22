/** @odoo-module **/

function markDone(actionRow, action) {
    if (!actionRow) {
        return;
    }
    const doneText = action === "confirm" ? "Confirmed" : "Cancelled";
    actionRow.innerHTML = `<span>${doneText}</span>`;
}

function detectAction(button) {
    const explicit = (button.dataset.action || "").trim().toLowerCase();
    if (explicit === "confirm" || explicit === "cancel") {
        return explicit;
    }
    const href = (button.getAttribute("href") || "").toLowerCase();
    if (href.includes("/confirm_create")) {
        return "confirm";
    }
    if (href.includes("/cancel_create")) {
        return "cancel";
    }
    return "";
}

async function handleClick(ev) {
    const button = ev.target.closest(".o_m_ai_pending_create_action");
    if (!button) {
        return;
    }
    ev.preventDefault();

    const actionRow = button.closest(".o_m_ai_pending_create_actions");
    if (button.dataset.loading === "1") {
        return;
    }
    button.dataset.loading = "1";

    try {
        const url = new URL(button.href, window.location.origin);
        url.searchParams.set("no_redirect", "1");
        const response = await fetch(url.toString(), {
            method: "GET",
            credentials: "same-origin",
        });
        if (response.ok) {
            const action = detectAction(button);
            markDone(actionRow, action);
        }
    } catch (_error) {
        window.location.href = button.href;
    } finally {
        delete button.dataset.loading;
    }
}

document.addEventListener("click", handleClick, true);
