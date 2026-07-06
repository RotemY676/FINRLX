"use client";

import SimpleModePage from "./simple/page";

/**
 * LEAP S7a — the front door is Simple Mode (SIMPLE_MODE_SPEC J0, D29).
 * The Decision Command Center that lived here moved feature-intact to /pro.
 * /simple stays mounted as an alias so links from the vertical-slice period
 * keep working (thin re-export per D9's move policy).
 */
export default function HomePage() {
  return <SimpleModePage />;
}
