export type DiataxisKind = "tutorial" | "how-to" | "reference" | "explanation";

export type HelpArea =
  | "getting-started"
  | "concepts"
  | "guides"
  | "reference"
  | "glossary"
  | "faq"
  | "troubleshooting"
  | "changelog"
  | "disclaimers"
  | "root";

export interface HelpFrontmatter {
  title: string;
  summary?: string;
  diataxis?: DiataxisKind;
  area?: HelpArea;
  updated?: string;
  order?: number;
  tags?: string[];
}

export interface HelpPage {
  slug: string;
  href: string;
  area: HelpArea;
  frontmatter: HelpFrontmatter;
  body: string;
}

export interface HelpAreaGroup {
  area: HelpArea;
  title: string;
  description: string;
  pages: HelpPage[];
}
