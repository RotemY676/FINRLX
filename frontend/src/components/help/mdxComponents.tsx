import Link from "next/link";
import type { MDXRemoteProps } from "next-mdx-remote/rsc";
import { Annotated } from "./Annotated";
import { Callout } from "./Callout";
import { HelpLink } from "./HelpLink";
import { Term } from "./Term";
import { DiataxisBadge } from "./DiataxisBadge";

const HEADING_BASE = "scroll-mt-24 font-display text-ink";

type AnchorProps = React.AnchorHTMLAttributes<HTMLAnchorElement>;

// WCAG 1.4.1: inline links must be distinguishable from surrounding prose by
// something other than colour alone. We underline by default with a soft
// 2px offset so the line doesn't crowd descenders, then darken on hover.
const MDX_LINK_CLASS =
  "text-primary underline underline-offset-2 decoration-1 hover:decoration-2 hover:opacity-90";

function MDXLink({ href = "", children, ...rest }: AnchorProps) {
  const isExternal = /^https?:\/\//.test(href);
  if (isExternal) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer noopener"
        className={MDX_LINK_CLASS}
        {...rest}
      >
        {children}
      </a>
    );
  }
  return (
    <Link href={href} className={MDX_LINK_CLASS}>
      {children}
    </Link>
  );
}

export const helpMDXComponents: MDXRemoteProps["components"] = {
  h1: (p) => <h1 {...p} className={`${HEADING_BASE} text-[28px] font-bold mt-0 mb-3`} />,
  h2: (p) => <h2 {...p} className={`${HEADING_BASE} text-[22px] font-semibold mt-10 mb-3 pb-2 border-b border-line`} />,
  h3: (p) => <h3 {...p} className={`${HEADING_BASE} text-[17px] font-semibold mt-8 mb-2`} />,
  h4: (p) => <h4 {...p} className={`${HEADING_BASE} text-[15px] font-semibold mt-6 mb-2`} />,
  p:  (p) => <p {...p} className="text-[14.5px] leading-7 text-ink-2 my-3" />,
  ul: (p) => <ul {...p} className="my-3 ml-5 list-disc text-[14.5px] leading-7 text-ink-2 space-y-1" />,
  ol: (p) => <ol {...p} className="my-3 ml-5 list-decimal text-[14.5px] leading-7 text-ink-2 space-y-1" />,
  li: (p) => <li {...p} className="marker:text-ink-4" />,
  a: MDXLink as React.FC<AnchorProps>,
  hr: (p) => <hr {...p} className="my-8 border-line" />,
  blockquote: (p) => (
    <blockquote {...p} className="my-4 pl-4 border-l-2 border-line text-ink-3 italic" />
  ),
  code: (p) => (
    <code
      {...p}
      className="font-mono text-[12.5px] px-1 py-0.5 rounded bg-surface-3 text-ink"
    />
  ),
  pre: (p) => (
    <pre
      {...p}
      className="my-4 p-4 rounded-md bg-surface-3 text-ink font-mono text-[12.5px] leading-6 overflow-x-auto ring-1 ring-line"
    />
  ),
  table: (p) => (
    <div className="my-4 overflow-x-auto">
      <table {...p} className="w-full text-[13.5px] border-collapse" />
    </div>
  ),
  th: (p) => (
    <th {...p} className="text-left font-semibold text-ink px-3 py-2 border-b border-line-strong bg-surface-2" />
  ),
  td: (p) => <td {...p} className="px-3 py-2 border-b border-line text-ink-2 align-top" />,
  img: ({ src = "", alt = "", ...rest }) => (
    // Plain <img> intentionally — MDX inline images use markdown ![alt](src)
    // syntax with arbitrary string sources, so next/image's static type
    // checking doesn't apply. Annotated screenshots use the <Annotated />
    // component which wraps next/image properly.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      className="my-4 rounded-md ring-1 ring-line max-w-full h-auto"
      {...rest}
    />
  ),
  // Custom components surfaced inside MDX
  Annotated,
  Callout,
  HelpLink,
  Term,
  DiataxisBadge,
};
