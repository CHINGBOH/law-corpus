<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import EvidencePanel from "@/components/EvidencePanel.vue";
import type { GraphNeighbor, GraphRelationGroup } from "@/types/api";

const props = defineProps<{
  groupedRelations: Record<string, GraphRelationGroup>;
  neighbors: GraphNeighbor[];
}>();

const router = useRouter();

const nonEmptyGroups = computed(() =>
  Object.entries(props.groupedRelations).filter(([, group]) => group.items.length > 0),
);

function openNode(nodeKey: string) {
  router.push({ path: "/graph", query: { node_key: nodeKey } });
}
</script>

<template>
  <section class="relation-board">
    <div class="group-grid" v-if="nonEmptyGroups.length">
      <article v-for="[key, group] in nonEmptyGroups" :key="key" class="group-card">
        <div class="head">
          <h2>{{ group.label }}</h2>
          <span>{{ group.items.length }} 个</span>
        </div>
        <div class="mini-links">
          <a
            v-for="item in group.items.slice(0, 8)"
            :key="item.target.node_key"
            href="#"
            @click.prevent="openNode(item.target.node_key)"
          >
            {{ item.target.title }}
          </a>
        </div>
      </article>
    </div>

    <div class="section-head">
      <h2>一跳关系</h2>
      <a :href="`/api/graph/neighbors?node_key=${encodeURIComponent(neighbors[0]?.target.node_key ?? '')}`">
        /api/graph/neighbors
      </a>
    </div>
    <div class="neighbor-grid">
      <p v-if="!neighbors.length" class="empty">当前节点还没有已整理的一跳制度关系。</p>
      <article v-for="item in neighbors" :key="`${item.direction}-${item.target.node_key}-${item.relation_type}`" class="neighbor-card">
        <div class="head">
          <span>{{ item.relation_type_label }}</span>
          <span class="badge">{{ item.direction === "outbound" ? "出去" : "进来" }}</span>
        </div>
        <h3>
          <a href="#" @click.prevent="openNode(item.target.node_key)">{{ item.target.title }}</a>
        </h3>
        <p>{{ item.target.subtitle }}</p>
        <EvidencePanel :evidence="item" compact />
      </article>
    </div>
  </section>
</template>

<style scoped>
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.group-card,
.neighbor-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.head h2 {
  font-size: 16px;
  margin: 0;
}

.head span {
  font-size: 12px;
  color: var(--text-muted);
}

.mini-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin: 8px 0;
}

.section-head h2 {
  font-size: 18px;
  margin: 0;
}

.section-head a {
  font-size: 12px;
  color: var(--text-muted);
}

.neighbor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.neighbor-card h3 {
  font-size: 15px;
  margin: 0 0 4px;
}

.neighbor-card p {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 8px;
}

.badge {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.empty {
  color: var(--text-muted);
  font-size: 14px;
}
</style>
