import "server-only";
import { getAllHelpPages } from "./content";
import type { HelpAreaGroup } from "./types";
import { AREA_META } from "./toc";

export interface HelpSearchEntry {
  slug: string;
  href: string;
  title: string;
  summary: string;
  area: string;
  areaTitle: string;
  diataxis?: string;
  body: string;
}

const STRIP_RE = /<[^>]+>|`{1,3}[^`]*`{1,3}|\[([^\]]+)\]\([^)]+\)|[*_~]/g;

function plainText(md: string): string {
  return md
    .replace(/^---[\s\S]*?---/m, "")
    .replace(STRIP_RE, (_m, linkText) => (linkText ? linkText : ""))
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 2400);
}

/**
 * Build a flat, search-ready index of every help page. Computed at build time
 * (Server Components), then serialized into the page as a `<script>` tag so
 * the client can search without an additional fetch.
 */
export function getHelpSearchIndex(): HelpSearchEntry[] {
  return getAllHelpPages().map((p) => ({
    slug: p.slug,
    href: p.href,
    title: p.frontmatter.title,
    summary: p.frontmatter.summary ?? "",
    area: p.area,
    areaTitle: AREA_META[p.area]?.title ?? "Help center",
    diataxis: p.frontmatter.diataxis,
    body: plainText(p.body),
  }));
}

export type { HelpAreaGroup };
