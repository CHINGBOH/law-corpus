<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { Network, type Data, type Edge, type Node as VisNode, type Options } from "vis-network";
import { DataSet } from "vis-data";
import type { GraphNode, GraphNodeRef, GraphNeighbor, GraphRelationGroup } from "@/types/api";

const props = defineProps<{
  node: GraphNode;
  structuralNeighbors: GraphNodeRef[];
  groupedRelations: Record<string, GraphRelationGroup>;
  neighbors: GraphNeighbor[];
}>();

const emit = defineEmits<{ navigate: [nodeKey: string] }>();

const container = ref<HTMLElement | null>(null);
let network: Network | null = null;

const GROUP_COLORS: Record<string, string> = {
  center: "#1f6feb",
  structural: "#94a3b8",
  policy_background: "#f0b429",
  upstream_supporting: "#2f9e44",
  institutional_linkage: "#a855f7",
  other: "#64748b",
};

function buildNetworkOptions(): Options {
  // Node labels render as canvas text below the dot, on the page background —
  // not inside the colored circle — so font color must stay dark regardless of
  // group color, or it disappears against the light page background.
  const groups: Record<string, { color: { background: string; border: string } }> = {};
  for (const [key, color] of Object.entries(GROUP_COLORS)) {
    groups[key] = { color: { background: color, border: color } };
  }
  return {
    autoResize: true,
    height: "560px",
    groups,
    nodes: { shape: "dot", size: 16, font: { color: "#1d2430", size: 13 } },
    edges: { arrows: "to", font: { size: 11, align: "middle" }, smooth: { enabled: true, type: "continuous", roundness: 0.4 } },
    physics: { solver: "barnesHut", barnesHut: { gravitationalConstant: -4000, springLength: 140 }, stabilization: { iterations: 150 } },
    interaction: { hover: true, tooltipDelay: 150 },
  };
}

// Node-group lookup derived from groupedRelations — the backend already buckets
// every neighbor into exactly one of these groups, so reuse that instead of
// re-deriving relation-type membership rules on the frontend.
function groupKeyFor(nodeKey: string): string {
  for (const [groupKey, group] of Object.entries(props.groupedRelations)) {
    if (group.items.some((item) => item.target.node_key === nodeKey)) {
      return groupKey;
    }
  }
  return "other";
}

function buildData(): Data {
  const nodes = new DataSet<VisNode>([]);
  const edges = new DataSet<Edge>([]);
  const seen = new Set<string>();

  nodes.add({ id: props.node.node_key, label: props.node.title, group: "center", size: 22 });
  seen.add(props.node.node_key);

  // Structural ("contains") edges don't carry a direction field in the API
  // response (graph_view() trims them to node_key/title/subtitle/href only),
  // so render them as plain undirected dashed lines rather than guess an arrow
  // direction — this matches how the old card view treated them too (a compact
  // reference list, not a primary directional relation).
  for (const item of props.structuralNeighbors) {
    if (!seen.has(item.node_key)) {
      nodes.add({ id: item.node_key, label: item.title, group: "structural" });
      seen.add(item.node_key);
    }
    edges.add({ from: props.node.node_key, to: item.node_key, dashes: true, arrows: "", color: { color: GROUP_COLORS.structural } });
  }

  for (const item of props.neighbors) {
    const target = item.target;
    if (!seen.has(target.node_key)) {
      nodes.add({ id: target.node_key, label: target.title, group: groupKeyFor(target.node_key) });
      seen.add(target.node_key);
    }
    const from = item.direction === "outbound" ? props.node.node_key : target.node_key;
    const to = item.direction === "outbound" ? target.node_key : props.node.node_key;
    edges.add({ from, to, label: item.relation_type_label });
  }

  return { nodes, edges };
}

function render() {
  if (!container.value) return;
  const data = buildData();
  if (network) {
    network.setData(data);
    return;
  }
  network = new Network(container.value, data, buildNetworkOptions());
  network.on("click", (params: { nodes: string[] }) => {
    const clicked = params.nodes[0];
    if (clicked && clicked !== props.node.node_key) {
      emit("navigate", clicked);
    }
  });
}

onMounted(render);
onUnmounted(() => {
  network?.destroy();
  network = null;
});

watch(() => [props.node.node_key, props.neighbors, props.structuralNeighbors], render);
</script>

<template>
  <div ref="container" class="graph-canvas"></div>
</template>

<style scoped>
.graph-canvas {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}
</style>
