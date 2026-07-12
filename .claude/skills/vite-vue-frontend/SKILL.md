---
name: vite-vue-frontend
description: Explains the Vite + Vue 3 conventions established in legal-corpus's frontend/ workstation — when to use a composable vs a direct getJson() call, how the shared components are abstracted (by data shape, not by page), the Vite proxy/build setup that ties into the stdlib Python backend, and the end-to-end checklist for adding a new view. This skill should be used whenever adding, modifying, or reviewing anything under frontend/ — a new view, a new shared component, a new composable, or a change to vite.config.ts/router/api client — so the change matches the existing architecture instead of introducing a parallel pattern (e.g. reaching for Pinia, Options API, or a bespoke fetch wrapper).
---

# Vite + Vue Frontend Conventions

## Overview

`frontend/` is a Vue 3 + Vite + TypeScript SPA — the only UI layer for legal-corpus (no
server-rendered HTML). It talks to a stdlib Python backend (`app/server.py`) that has no
framework of its own, just `/api/*` JSON endpoints. Every convention below exists because
of that pairing: a minimal backend with no ORM/serializer layer, and a minimal frontend
with no state-management library. Read `CLAUDE.md`'s "frontend/" section first for the
directory map; this skill covers the *why* and the *how to extend it*.

## Vite config essentials (`frontend/vite.config.ts`)

```ts
server: { proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } } },
build: { outDir: "../app/static", emptyOutDir: true },
resolve: { alias: { "@": "./src" } },
```

- **Dev proxy**: `/api/*` forwards to the Python backend on `:8000`. Frontend code always
  calls relative paths (`/api/workspace/graph`), never a hardcoded host — this makes dev
  (`:5173` + proxy) and prod (`:8000` alone) identical from the app code's point of view.
- **`build.outDir` points at `../app/static`**: `npm run build` emits straight into the
  directory `server.py` serves as static files with SPA-fallback-to-`index.html`. There is
  no separate deploy step — building *is* deploying, for this single-process app.
- **`@` alias** resolves to `src/`. Use it in every import (`@/api/client`, `@/types/api`),
  never relative `../../` chains.

`npm run build` runs `vue-tsc --noEmit && vite build` — the type-check is a build gate, not
optional. A view that compiles but fails `vue-tsc` fails the build.

## Vue conventions

- **`<script setup>` only.** No Options API anywhere in this codebase. If writing a
  component and reaching for `export default { data() {...} }`, stop — rewrite as
  `<script setup lang="ts">` with `ref`/`computed`/imported composables.
- **No Pinia, no Vuex.** This is a deliberate choice, not an oversight — see the state
  management rule below for why the composable layer is sufficient here.
- **Router**: `createWebHistory()` (`src/router/index.ts`), paths intentionally mirror the
  `/api/workspace/*` paths documented in `README.md`. A new view's route path should read
  as the human-facing name of its backend aggregation function, not an arbitrary URL.

## State management: composable vs. direct fetch

Two patterns coexist on purpose — picking the wrong one for a given view is the most
common mistake to avoid:

**Direct `getJson()` in the view** (`HomeView`, `InstrumentView`, `DomainView`,
`TopicView`, `SearchView`): the view's state is "whatever came back from one fetch on
mount/query-change." No other action in the page mutates it. Adding a composable here
would be an indirection layer with nothing to abstract.

**A composable in `src/composables/`** (`useGraphView`, `useReaderView`,
`useReviewQueue`): the state is written from *multiple* places in the same page — preset
clicks, path queries, candidate extraction, accept/reject actions all touch the same
`data` ref. The composable collects every writer of that state into one function so the
template only ever reads, never races itself. Shape to copy (from `useGraphView.ts`):

```ts
export function useGraphView() {
  const data: Ref<GraphViewResponse | null> = ref(null);
  const loading = ref(false);
  const error: Ref<string | null> = ref(null);
  async function load(nodeKey: string, toNodeKey = ""): Promise<void> { /* fetch, set data/loading/error */ }
  return { data, loading, error, load };
}
```

Decision rule: **if a page has more than one user action capable of changing the same
piece of server-derived state, it needs a composable; if it's read-once-per-navigation, it
doesn't.**

## Component abstraction: by data shape, not by page

The six shared components in `src/components/` (`RelationBoard`, `FocusReader`,
`TopicMap`, `EvidencePanel`, `ReviewDrawer`, `ContextSidebar`) are each keyed to a *data
shape*, not a business page:

- `FocusReader` = "article nav + body" shape → reused by the law reader, the generic
  instrument reader, and the compare view (in compact mode).
- `TopicMap` = "card grid" shape → reused by domain/topic/pillar pages and topic link
  groups.
- `EvidencePanel` = the *only* rendering path for `source`/`evidence_level`/`confidence` —
  structurally enforces the evidence rule (see `CLAUDE.md`) by being the single place that
  knows how to render a claim.

When a new view needs to show something, first check whether its data has the same shape
as an existing component's props before writing new markup. A node-link diagram
(`RelationGraphCanvas.vue`) was *not* folded into `RelationBoard` despite showing the same
underlying data, because the shape it consumes (a `{nodes, edges}` graph) is genuinely
different from a grouped list — that's the right call to make a sibling component instead
of overloading one with a rendering-mode flag.

## API contract: `src/types/api.ts`

Every `/api/workspace/*` response shape gets a matching TypeScript interface in
`src/types/api.ts`. This file is the formal contract with `app/workspace_service.py` — the
backend has no schema/serializer layer (`db_access.py` shells out to `psql` and returns
raw JSON), so this file is the *only* place the shape is declared at all. When a backend
aggregation function's returned dict changes, update the matching interface in the same
change — there is no other check that will catch a drift (Python raises nothing; the
frontend just gets `undefined` at runtime).

## Checklist: adding a new view end-to-end

1. **Backend**: add a function to `app/workspace_service.py` composing existing
   `graph_service`/`review_service`/`QUERIES[...]` calls into one dict; add a branch in
   `server.py`'s `workspace_response`.
2. **Contract**: add the matching interface to `frontend/src/types/api.ts`.
3. **State**: decide composable vs. direct fetch per the rule above.
4. **View**: new file in `frontend/src/views/`, reusing existing shared components before
   writing new markup (check the data-shape list above).
5. **Route**: add to `frontend/src/router/index.ts`, path mirroring the API path.
6. **Type-check**: `cd frontend && npm run build` (runs `vue-tsc --noEmit` first) — must be
   clean before considering the view done.
7. **Browser-verify**: start both dev servers (`python3 app/server.py` in one terminal,
   `cd frontend && npm run dev` in another) and actually load the route — a passing
   type-check does not mean the data renders correctly. Use `chrome-devtools-mcp` for
   screenshots/snapshots in this environment; `mcp__playwright__*`'s screenshot tool has
   been observed to hang indefinitely waiting on a font-load promise here — fall back to
   chrome-devtools-mcp rather than retrying playwright screenshots.
8. **Production smoke test** (only for changes likely to affect the build, e.g. a new
   heavy dependency like `vis-network`): `npm run build` then serve from `app/server.py`
   alone on `:8000` and confirm the route works with no dev-proxy involved.
