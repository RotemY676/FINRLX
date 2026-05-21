import "server-only";
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import type { HelpArea, HelpFrontmatter, HelpPage } from "./types";

const HELP_ROOT = path.join(process.cwd(), "src", "content", "help");

function walk(dir: string, acc: string[] = []): string[] {
  if (!fs.existsSync(dir)) return acc;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, acc);
    else if (entry.isFile() && /\.(md|mdx)$/i.test(entry.name)) acc.push(full);
  }
  return acc;
}

function fileToPage(file: string): HelpPage {
  const raw = fs.readFileSync(file, "utf8");
  const { data, content } = matter(raw);
  const rel = path.relative(HELP_ROOT, file).replace(/\\/g, "/").replace(/\.(md|mdx)$/i, "");
  const slug = rel === "index" ? "" : rel.replace(/\/index$/i, "");
  const href = slug === "" ? "/help" : `/help/${slug}`;
  const area: HelpArea = inferArea(slug, data?.area);
  const fm: HelpFrontmatter = {
    title: typeof data?.title === "string" ? data.title : prettifySlug(slug || "Help center"),
    summary: typeof data?.summary === "string" ? data.summary : undefined,
    diataxis: data?.diataxis,
    area,
    updated: typeof data?.updated === "string" ? data.updated : undefined,
    order: typeof data?.order === "number" ? data.order : undefined,
    tags: Array.isArray(data?.tags) ? data.tags.filter((t: unknown) => typeof t === "string") : undefined,
  };
  return { slug, href, area, frontmatter: fm, body: content };
}

function inferArea(slug: string, declared?: unknown): HelpArea {
  if (typeof declared === "string") return declared as HelpArea;
  if (!slug) return "root";
  const first = slug.split("/")[0];
  switch (first) {
    case "getting-started":
    case "concepts":
    case "guides":
    case "reference":
    case "glossary":
    case "faq":
    case "troubleshooting":
    case "changelog":
    case "disclaimers":
      return first as HelpArea;
    default:
      return "root";
  }
}

function prettifySlug(slug: string): string {
  return slug
    .split("/")
    .pop()!
    .split("-")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(" ");
}

let cache: HelpPage[] | null = null;

export function getAllHelpPages(): HelpPage[] {
  if (cache) return cache;
  const files = walk(HELP_ROOT);
  cache = files
    .map(fileToPage)
    .sort((a, b) => {
      const ao = a.frontmatter.order ?? 1000;
      const bo = b.frontmatter.order ?? 1000;
      if (ao !== bo) return ao - bo;
      return a.frontmatter.title.localeCompare(b.frontmatter.title);
    });
  return cache;
}

export function getHelpPageBySlug(slugParts: string[] | undefined): HelpPage | null {
  const slug = (slugParts ?? []).join("/");
  const pages = getAllHelpPages();
  return pages.find((p) => p.slug === slug) ?? null;
}

export function getPagesByArea(area: HelpArea): HelpPage[] {
  return getAllHelpPages().filter((p) => p.area === area);
}

export function getHelpSlugs(): string[][] {
  return getAllHelpPages()
    .filter((p) => p.slug !== "")
    .map((p) => p.slug.split("/"));
}
