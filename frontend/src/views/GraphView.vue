<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ContextSidebar from "@/components/ContextSidebar.vue";
import SidebarCard from "@/components/SidebarCard.vue";
import RelationBoard from "@/components/RelationBoard.vue";
import { useGraphView } from "@/composables/useGraphView";

const route = useRoute();
const router = useRouter();
const { data, loading, error, extractStatus, load, extractCandidates } = useGraphView();

const nodeKeyInput = ref("");
const toNodeKeyInput = ref("");

function currentNodeKey(): string {
  const value = route.query.node_key;
  return typeof value === "string" && value ? value : "legal_instrument:cn_company_law";
}

function currentToNodeKey(): string {
  const value = route.query.to_node_key;
  return typeof value === "string" ? value : "";
}

async function refresh() {
  nodeKeyInput.value = currentNodeKey();
  toNodeKeyInput.value = currentToNodeKey();
  await load(nodeKeyInput.value, toNodeKeyInput.value);
}

watch(() => [route.query.node_key, route.query.to_node_key], refresh, { immediate: true });

function submitNodeSearch() {
  router.push({ path: "/graph", query: { node_key: nodeKeyInput.value } });
}

function submitPathSearch() {
  router.push({ path: "/graph", query: { node_key: nodeKeyInput.value, to_node_key: toNodeKeyInput.value } });
}

function openNode(nodeKey: string) {
  router.push({ path: "/graph", query: { node_key: nodeKey } });
}

const pathChain = computed(() => {
  const path = data.value?.path;
  if (!path || !path.nodes.length) return [];
  const chain: { type: "node" | "edge"; label: string }[] = [];
  path.nodes.forEach((node, idx) => {
    chain.push({ type: "node", label: node.title });
    const edge = path.edges[idx];
    if (edge) chain.push({ type: "edge", label: edge.relation_type });
  });
  return chain;
});
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div>
        <h1>关系穿透台</h1>
        <p v-if="data">{{ data.node.title }} · {{ data.node.subtitle }}</p>
      </div>
      <form class="search" @submit.prevent="submitNodeSearch">
        <input v-model="nodeKeyInput" placeholder="legal_unit:company_law:2023:article_47" />
        <button type="submit">打开节点</button>
      </form>
    </header>

    <p v-if="loading" class="status">加载中...</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <main v-else-if="data">
      <section class="stats">
        <article><strong>{{ data.node.node_type_label }}</strong><span>节点类型</span></article>
        <article><strong>{{ data.node.ref }}</strong><span>引用</span></article>
        <article><strong>{{ data.counts.meaningful_neighbors }}</strong><span>制度关系</span></article>
        <article><strong>{{ data.counts.structural_neighbors }}</strong><span>结构关系</span></article>
        <article><strong>{{ toNodeKeyInput || "-" }}</strong><span>路径目标</span></article>
      </section>

      <section class="graph-layout">
        <ContextSidebar>
          <SidebarCard title="当前节点" meta="当前节点">
            <p class="hint-box">{{ data.node.hint }}</p>
            <footer class="result-actions">
              <a :href="data.node.href">打开原文</a>
              <router-link to="/review">去审核台</router-link>
            </footer>
          </SidebarCard>

          <SidebarCard title="常用入口" meta="研究预设">
            <div class="mini-links">
              <a v-for="preset in data.presets" :key="preset.node_key" href="#" @click.prevent="openNode(preset.node_key)">
                {{ preset.label }}
              </a>
            </div>
          </SidebarCard>

          <SidebarCard title="结构定位" meta="不计入制度关系">
            <div class="mini-links" v-if="data.structural_neighbors.length">
              <a
                v-for="item in data.structural_neighbors"
                :key="item.node_key"
                href="#"
                @click.prevent="openNode(item.node_key)"
              >
                {{ item.title }} · {{ item.subtitle }}
              </a>
            </div>
            <p v-else class="empty">当前没有结构隶属信息。</p>
          </SidebarCard>

          <SidebarCard title="候选提议" meta="/api/review/candidates">
            <p>先在条文节点触发候选关系抽取，再到审核台转正。</p>
            <div v-if="data.node.can_extract_candidates" class="ask-actions">
              <button type="button" @click="extractCandidates(data.node.ref ?? '')">抽取候选关系</button>
              <span>{{ extractStatus }}</span>
            </div>
          </SidebarCard>

          <SidebarCard title="路径查询" meta="/api/graph/path">
            <form class="reader-controls" @submit.prevent="submitPathSearch">
              <input v-model="toNodeKeyInput" placeholder="context_event:cn_registration_capital_reform_2013" />
              <button type="submit">查路径</button>
            </form>
            <div class="path-box">
              <template v-if="pathChain.length">
                <span
                  v-for="(item, idx) in pathChain"
                  :key="idx"
                  :class="item.type === 'node' ? 'path-node' : 'path-edge'"
                >
                  {{ item.label }}
                </span>
              </template>
              <p v-else-if="toNodeKeyInput" class="empty">没有找到 4 跳以内路径。</p>
              <p v-else class="empty">输入目标节点，查看穿透路径。</p>
            </div>
          </SidebarCard>
        </ContextSidebar>

        <RelationBoard :grouped-relations="data.grouped_relations" :neighbors="data.neighbors" />
      </section>
    </main>
  </div>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.topbar h1 {
  font-size: 26px;
  margin: 0 0 4px;
}

.topbar p {
  margin: 0;
  color: var(--text-muted);
}

.search {
  display: flex;
  gap: 8px;
}

.search input {
  min-width: 320px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.search button,
.ask-actions button,
.reader-controls button {
  border: none;
  background: var(--accent);
  color: white;
  padding: 8px 14px;
  border-radius: 6px;
}

.status {
  color: var(--text-muted);
}

.status.error {
  color: #b3261e;
}

.stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stats article {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats strong {
  font-size: 16px;
  overflow-wrap: anywhere;
}

.stats span {
  font-size: 12px;
  color: var(--text-muted);
}

.graph-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
  align-items: start;
}

.hint-box {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
}

.result-actions {
  display: flex;
  gap: 12px;
}

.mini-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ask-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reader-controls {
  display: flex;
  gap: 8px;
}

.reader-controls input {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.path-box {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.path-node {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 13px;
}

.path-edge {
  color: var(--text-muted);
  font-size: 12px;
}

.empty {
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 820px) {
  .graph-layout {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
