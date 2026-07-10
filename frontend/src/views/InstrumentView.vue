<script setup lang="ts">
import { computed, watch, ref } from "vue";
import { useRoute } from "vue-router";
import TopicMap from "@/components/TopicMap.vue";
import EvidencePanel from "@/components/EvidencePanel.vue";
import { getJson } from "@/api/client";
import type { InstrumentViewResponse } from "@/types/api";

const route = useRoute();
const data = ref<InstrumentViewResponse | null>(null);
const loading = ref(true);

function currentSlug(): string {
  const value = route.query.slug;
  return typeof value === "string" && value ? value : "cn_company_law";
}

async function refresh() {
  loading.value = true;
  data.value = await getJson<InstrumentViewResponse>(`/api/workspace/instrument?slug=${currentSlug()}`);
  loading.value = false;
}

watch(() => route.query.slug, refresh, { immediate: true });

const topicCards = computed(
  () =>
    data.value?.topics.map((t) => ({
      title: t.title,
      badge: t.pillar_title,
      strong: t.question,
      description: t.summary,
      footerLabel: "查看专题",
      footerHref: `/topic?slug=${t.slug}`,
    })) ?? [],
);
</script>

<template>
  <div class="page">
    <p v-if="loading" class="status">加载中...</p>
    <template v-else-if="data">
      <header class="topbar">
        <div>
          <h1>{{ data.instrument.short_title }}</h1>
          <p>{{ data.instrument.canonical_title }} · {{ data.instrument.domains }}</p>
        </div>
        <div class="inline-actions">
          <router-link to="/">返回首页</router-link>
          <router-link :to="`/graph?node_key=legal_instrument:${data.instrument.slug}`">图谱打开</router-link>
          <a v-if="data.instrument.source_url" :href="data.instrument.source_url" target="_blank" rel="noreferrer">官方来源</a>
        </div>
      </header>

      <section class="stats">
        <article><strong>{{ data.instrument.current_version_label }}</strong><span>当前版本</span></article>
        <article><strong>{{ data.instrument.instrument_type }}</strong><span>类型</span></article>
        <article><strong>{{ data.instrument.effective_date }}</strong><span>施行</span></article>
        <article><strong>{{ data.instrument.first_enacted_date }}</strong><span>初次制定</span></article>
        <article><strong>{{ data.instrument.domains }}</strong><span>法域</span></article>
      </section>

      <section>
        <div class="section-head"><h2>体系关系</h2></div>
        <div class="context-grid">
          <p v-if="!data.relations.length" class="empty">当前还没有关系数据。</p>
          <article v-for="(r, idx) in data.relations" :key="idx" class="context-card">
            <div class="context-head"><span>{{ r.relation_type_label }}</span></div>
            <h3><router-link :to="r.href">{{ r.object_title }}</router-link></h3>
            <p>{{ r.claim_text }}</p>
            <EvidencePanel :evidence="r" compact />
          </article>
        </div>
      </section>

      <section>
        <div class="section-head"><h2>相关专题</h2></div>
        <TopicMap :cards="topicCards" empty-text="当前规范还没有挂接专题。" />
      </section>

      <section>
        <div class="section-head"><h2>版本</h2></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>#</th><th>版本</th><th>动作</th><th>通过</th><th>施行</th></tr></thead>
            <tbody>
              <tr v-for="v in data.versions" :key="v.slug">
                <td>{{ v.version_sequence }}</td>
                <td>{{ v.version_label }}</td>
                <td>{{ v.action_type }}</td>
                <td>{{ v.adopted_date }}</td>
                <td>{{ v.effective_date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div class="section-head"><h2>关键条文</h2></div>
        <p v-if="!data.units.length" class="empty">当前只录入了元数据，尚未补关键条文。</p>
        <article v-for="u in data.units" :key="u.canonical_ref" class="result">
          <div>{{ u.version_label }} · {{ u.canonical_ref }}</div>
          <h2>{{ u.unit_number }}</h2>
          <p>{{ u.text }}</p>
          <footer>
            <router-link v-for="action in u.actions" :key="action.href" :to="action.href">{{ action.label }}</router-link>
          </footer>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.page {
  max-width: 1100px;
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

.inline-actions {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.status,
.empty {
  color: var(--text-muted);
}

section {
  margin-bottom: 24px;
}

.section-head h2 {
  font-size: 18px;
  margin: 0 0 8px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 24px;
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

.stats span {
  font-size: 12px;
  color: var(--text-muted);
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th,
td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-soft);
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.context-card,
.result {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.context-head {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.result > div {
  font-size: 12px;
  color: var(--text-muted);
}

.result h2 {
  font-size: 17px;
  margin: 4px 0 8px;
}

.result footer {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

@media (max-width: 820px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
