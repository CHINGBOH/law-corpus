---
name: vis-network-graph-upgrade
description: Implements the relation-graph visualization upgrade for legal-corpus's 关系穿透台 (Relation Piercing Platform) — replacing the card-list-only RelationBoard.vue with a real interactive node-link diagram using vis-network, per the recommendation in docs/graph-libraries-research.md. This skill should be used when the user asks to add a graph/network visualization to the legal-corpus frontend, to continue that work across sessions, or when running the vis-network upgrade via /loop. Self-contained and resumable: each invocation re-checks repo state and continues from the first incomplete checkpoint.
---

# vis-network Graph Upgrade

## Overview

Upgrade `legal-corpus`'s graph page from a card-list-only view to a real interactive
node-link diagram, using `vis-network` (the library recommended in
`docs/graph-libraries-research.md` after comparing it against Cytoscape.js, Sigma.js, and
D3-force for this project's scale — a few dozen edges, no need for WebGL or heavy graph
algorithms). Read that research doc's "综合结论" and "后续行动" sections before starting;
this skill executes that plan.

**Do not touch the backend.** `app/workspace_service.py`'s `graph_view()` JSON contract
(`node`, `counts`, `structural_neighbors`, `grouped_relations`, `neighbors`, `presets`,
`path`) already has everything the diagram needs, pre-resolved (labels, hrefs). This is a
frontend-only change.

## Resumable Workflow

This skill is designed to be re-entered repeatedly (e.g. via `/loop`). On every
invocation: **first re-check which checkpoints are already done by inspecting the repo**,
then do the next incomplete one. Do not redo completed work. Do not skip ahead — each
checkpoint depends on the previous one existing and working.

### Checkpoint 1 — `vis-network` installed

Check: does `frontend/package.json` list `vis-network` under `dependencies`?

If not:
```bash
cd frontend && npm install vis-network
```
Do not add `vis-data` — the core `vis-network` package exports `DataSet`/`Network`
directly and that's sufficient here.

### Checkpoint 2 — `RelationGraphCanvas.vue` exists and type-checks

Check: does `frontend/src/components/RelationGraphCanvas.vue` exist, and does
`npx vue-tsc --noEmit` (run from `frontend/`) pass?

If not, create it. Contract:
- Props: the same `groupedRelations: Record<string, GraphRelationGroup>` and
  `neighbors: GraphNeighbor[]` that `RelationBoard.vue` already takes (see
  `frontend/src/types/api.ts` for these interfaces), plus the current node
  (`GraphNode`, for the center node) and `structuralNeighbors: GraphNodeRef[]`.
- Map that data into vis-network's `{nodes: DataSet, edges: DataSet}` format:
  - One node for the current center node (id = its `node_key`), fixed/highlighted.
  - One node per unique neighbor target (dedupe `structural_neighbors` and
    `neighbors[].target` by `node_key` — a node can appear in both).
  - One edge per `neighbors[]` item: `from`/`to` set by `direction` (`outbound` →
    from=center, to=target; `inbound` → from=target, to=center), `label` =
    `relation_type_label`.
  - `structural_neighbors` edges use `relation_type: 'contains'` conceptually — give
    them a distinct edge color/dashed style and route them through vis-network's
    `hierarchicalRepulsion` physics solver (per the research doc's recommendation),
    since they are structural containment, not institutional relations.
  - Group neighbor nodes by which `grouped_relations` bucket they fall into
    (`policy_background`/`upstream_supporting`/`institutional_linkage`/`other`) and
    set vis-network's `group` field accordingly, with one color per group — this
    maps the existing card-grouping logic onto the diagram instead of reinventing
    grouping.
- On node click, `emit('navigate', nodeKey)` — the parent (`GraphView.vue`) already
  has an `openNode(nodeKey)` router-push handler from the existing `RelationBoard`
  wiring; reuse it, don't duplicate navigation logic.
- Instantiate `vis.Network` in `onMounted`, tear down in `onUnmounted` (call
  `network.destroy()` — vis-network does not clean up automatically and leaks DOM/
  canvas listeners across Vue route changes otherwise).
- Physics: `barnesHut` solver for relation edges (default), `hierarchicalRepulsion`
  scoped to structural edges as noted above — see the physics config examples
  already captured from `ctx7` research if you need exact option shapes; re-fetch
  `/visjs/vis-network` via `ctx7` if the local memory of the API has gone stale.

Verify by running `npx vue-tsc --noEmit` in `frontend/` — must pass with zero errors
before moving to the next checkpoint.

### Checkpoint 3 — tab toggle wired into `GraphView.vue`

Check: does `frontend/src/views/GraphView.vue` render both `RelationGraphCanvas` and
`RelationBoard` behind a tab/toggle control (not a full replacement — the research doc
is explicit that the card list stays as a "列表模式" for evidence-dense reading and
accessibility, it is not being deleted)?

If not, add a small local `ref<'graph' | 'list'>('graph')` toggle state, two tab
buttons above the main content area (reuse the existing page's `.topbar`/section
styling conventions — check `RelationBoard.vue` and `GraphView.vue`'s current
`<style scoped>` blocks for the established color tokens (`var(--accent)`,
`var(--border)`, etc.) rather than inventing new ones), and conditionally render
`<RelationGraphCanvas v-if="tab === 'graph'" ...>` /
`<RelationBoard v-else ...>` with the same props both already receive today.

Default tab: `'graph'` (the new diagram is the improvement being shipped; list mode
is the fallback, not the other way around).

### Checkpoint 4 — verified in a real browser

Check: has this session (or a prior one, evidenced by a note left in this file's
"Progress Log" section below) confirmed the diagram renders correctly with real data
and zero console errors?

If not:
1. Ensure both dev servers are running: `python3 app/server.py` (port 8000) and
   `cd frontend && npm run dev` (port 5173) — check `ps aux | grep -E "server.py|vite"`
   before starting new ones; do not spawn duplicates.
2. Use the `playwright` MCP tools (`browser_navigate`, `browser_console_messages`,
   `browser_take_screenshot`) — not a guess — to visit
   `http://127.0.0.1:5173/graph?node_key=legal_unit:company_law:2023:article_47` (this
   node has real relation data: `based_on`/`policy_background`/etc. edges, per prior
   verification in this project), confirm the diagram tab renders nodes/edges with
   correct labels, click a node and confirm navigation works, switch to list mode and
   confirm `RelationBoard` still works unchanged, and check
   `browser_console_messages` for zero errors (pre-existing warnings about routes not
   yet built, e.g. `/review` or `/api/contexts`, are expected and not regressions —
   compare against what this project's `README.md`/prior session history already
   documents as known warnings, don't treat them as new bugs).
3. Record the outcome in the Progress Log below (append, do not overwrite prior
   entries) so a future/looped invocation of this skill knows checkpoint 4 is done
   and can stop.

### When all four checkpoints are done

Stop. Do not keep looping. If this skill is being driven by `/loop`, report completion
back to the user (summarize what changed, list files touched) instead of continuing —
a `/loop` session should end itself once the task converges, not run indefinitely on a
finished task.

## Progress Log

<!-- Append one line per session with date + which checkpoint(s) completed, so a
     resumed /loop invocation can tell what's already done without re-deriving it
     from git diff alone. Do not delete prior entries. -->
