/*
  UTILS.JS
  Shared security utilities for Tax God frontend.
*/

/**
 * Escape HTML to prevent XSS when inserting dynamic content via innerHTML.
 */
export function escapeHtml(str) {
    if (str == null) return "";
    const s = String(str);
    return s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

/**
 * Simple markdown-ish to safe HTML: escape first, then convert newlines to <br>.
 */
export function safeMarkdown(str) {
    return escapeHtml(str).replace(/\n/g, "<br>");
}
