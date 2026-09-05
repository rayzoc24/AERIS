/**
 * Safe rendering of any untrusted HTML returned by the backend.
 * Components MUST call sanitize() before setting innerHTML. Prefer
 * textContent over innerHTML wherever possible. (security check #8)
 */
import DOMPurify from "dompurify";

const ALLOWED_TAGS = ["p", "br", "strong", "em", "ul", "ol", "li"];

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS,
    ALLOWED_ATTR: [],
    ALLOW_DATA_ATTR: false,
  });
}

export function sanitizeText(dirty: string): string {
  // Strip control characters and zero-width chars.
  return dirty.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").replace(/[\u200B-\u200D\uFEFF]/g, "");
}
