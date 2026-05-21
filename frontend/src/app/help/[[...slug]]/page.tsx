import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { MDXRemote } from "next-mdx-remote/rsc";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";

import { HelpShell } from "@/components/help/HelpShell";
import { PageHeader } from "@/components/help/PageHeader";
import { helpMDXComponents } from "@/components/help/mdxComponents";
import { HelpLandingBody } from "@/components/help/HelpLandingBody";
import {
  getAllHelpPages,
  getHelpPageBySlug,
  getHelpSlugs,
} from "@/lib/help/content";

interface PageProps {
  params: Promise<{ slug?: string[] }>;
}

export async function generateStaticParams() {
  const slugs = getHelpSlugs();
  return [{ slug: undefined }, ...slugs.map((s) => ({ slug: s }))];
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = getHelpPageBySlug(slug);
  if (!page) return { title: "Help center" };
  return {
    title: page.frontmatter.title,
    description: page.frontmatter.summary,
  };
}

export default async function HelpPage({ params }: PageProps) {
  const { slug } = await params;
  const page = getHelpPageBySlug(slug);
  if (!page) notFound();

  const isLanding = page.slug === "";

  return (
    <HelpShell>
      <PageHeader fm={page.frontmatter} />
      {isLanding && <HelpLandingBody pages={getAllHelpPages()} />}
      {page.body.trim().length > 0 && (
        <article className="prose-help">
          <MDXRemote
            source={page.body}
            components={helpMDXComponents}
            options={{
              parseFrontmatter: false,
              mdxOptions: {
                remarkPlugins: [remarkGfm],
                rehypePlugins: [
                  rehypeSlug,
                  [
                    rehypeAutolinkHeadings,
                    {
                      behavior: "wrap",
                      properties: { className: ["heading-anchor"] },
                    },
                  ],
                ],
              },
            }}
          />
        </article>
      )}
    </HelpShell>
  );
}
