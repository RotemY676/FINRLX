---
title: Universe and features
summary: What goes into a model — assets, indicators, and the discipline of point-in-time data.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 2
---

Every decision starts with a universe (which assets are eligible) and a feature set (what the model sees about each asset at each time step). The choices you make here constrain everything downstream. A universe that silently drops delisted names inflates returns; a feature set built from forward-looking aggregates leaks future information into training.

This page lays out the rules FINRLX enforces, the choices you control, and the failure modes the team most often sees.
