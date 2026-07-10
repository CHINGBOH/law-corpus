<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import TopicMap from "@/components/TopicMap.vue";
import AskPanel from "@/components/AskPanel.vue";
import EvidencePanel from "@/components/EvidencePanel.vue";
import { getJson } from "@/api/client";
import type { HomeViewResponse } from "@/types/api";

const router = useRouter();
const data = ref<HomeViewResponse | null>(null);
const loading = ref(true);
const searchQuery = ref("");

onMounted(async () => {
  data.value = await getJson<HomeViewResponse>("/api/workspace/home");
  loading.value = false;
});

function submitSearch() {
  router.push({ path: "/search", query: { q: searchQuery.value } });
}

const statBoxes = computed(() => {
  const s = data.value?.stats;
  if (!s) return [];
  return [
    { label: "规范", value: s.instruments },
    { label: "法域", value: s.domains },
    { label: "专题", value: s.topics },
    { label: "版本", value: s.versions },
    { label: "法律关系", value: s.legal_relations },
    { label: "候选关系", value: s.relation_candidates },
    { label: "解释", value: s.plain_explanations },
  ];
});

const domainCards = computed(
  () =>
    data.value?.domains.map((d) => ({
      title: d.name,
      badge: d.instrument_count,
      description: d.description,
      footerLabel: "查看法域",
      footerHref: `/domain?slug=${d.slug}`,
    })) ?? [],
);

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

const pillarCards = computed(
  () =>
    data.value?.pillars.map((p) => ({
      title: p.title,
      strong: p.question,
      description: `${p.scope} ${p.signal}`,
    })) ?? [],
);
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div>
        <h1>法律规范体系仓库</h1>
        <p>先看法体系，再钻公司法版本、条文和制度演化</p>
      </div>
      <form class="search" @submit.prevent="submitSearch">
        <input v-model="searchQuery" name="q" placeholder="搜索法律、条文、制度、政策背景" />
        <button type="submit">查询</button>
      </form>
    </header>

    <p v-if="loading" class="status">加载中...</p>
    <main v-else-if="data">
      <section class="quick-actions">
        <router-link to="/graph?node_key=legal_instrument:cn_company_law"><strong>关系穿透台</strong><span>从公司法节点展开图谱</span></router-link>
        <router-link to="/review"><strong>候选审核台</strong><span>模型提议关系，人来转正</span></router-link>
        <router-link to="/instrument?slug=cn_company_law"><strong>公司法</strong><span>版本、关键条文、对外关系</span></router-link>
        <router-link to="/domain?slug=commercial-organization"><strong>商事组织法</strong><span>公司、合伙、个人独资</span></router-link>
        <router-link to="/law?version=cn_company_law_2023&article=47"><strong>读原文</strong><span>2023 第47条</span></router-link>
        <a href="#ask"><strong>AI解释</strong><span>基于法体系、条文和政策上下文</span></a>
      </section>

      <section class="stats">
        <article v-for="s in statBoxes" :key="s.label"><strong>{{ s.value }}</strong><span>{{ s.label }}</span></article>
      </section>

      <section>
        <div class="section-head"><h2>法域底座</h2></div>
        <TopicMap :cards="domainCards" />
      </section>

      <section>
        <div class="section-head"><h2>专题脉络</h2></div>
        <TopicMap :cards="topicCards" />
      </section>

      <section>
        <div class="section-head"><h2>规范目录</h2></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>规范</th><th>类型</th><th>法域</th><th>当前版本</th><th>施行</th></tr></thead>
            <tbody>
              <tr v-for="i in data.instruments" :key="i.slug">
                <td><router-link :to="`/instrument?slug=${i.slug}`"><strong>{{ i.short_title }}</strong></router-link><span>{{ i.canonical_title }}</span></td>
                <td>{{ i.instrument_type }}</td>
                <td>{{ i.domains }}</td>
                <td>{{ i.current_version_label }}</td>
                <td>{{ i.effective_date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div class="section-head"><h2>公司法对外关系</h2></div>
        <div class="context-grid">
          <article v-for="(r, idx) in data.company_relations" :key="idx" class="context-card">
            <div class="context-head"><span>{{ r.relation_type_label }}</span></div>
            <h3><router-link :to="r.href">{{ r.object_title }}</router-link></h3>
            <p>{{ r.claim_text }}</p>
            <EvidencePanel :evidence="r" compact />
          </article>
        </div>
      </section>

      <section id="ask">
        <div class="section-head"><h2>问公司法</h2></div>
        <AskPanel />
      </section>

      <section>
        <div class="section-head"><h2>公司法承力柱</h2></div>
        <TopicMap :cards="pillarCards" />
      </section>

      <section>
        <div class="section-head"><h2>公司法版本时间线</h2></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>#</th><th>版本</th><th>动作</th><th>通过</th><th>施行</th><th>状态</th><th>条数</th></tr></thead>
            <tbody>
              <tr v-for="v in data.versions" :key="v.slug">
                <td>{{ v.version_sequence }}</td>
                <td><strong>{{ v.version_label }}</strong><span>{{ v.slug }}</span></td>
                <td>{{ v.action_type }}</td>
                <td>{{ v.adopted_date }}</td>
                <td>{{ v.effective_date }}</td>
                <td><span class="badge">{{ v.status }}</span></td>
                <td>{{ v.article_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div class="section-head"><h2>政策环境与比较法证据</h2></div>
        <div class="context-grid">
          <article v-for="(c, idx) in data.contexts" :key="idx" class="context-card">
            <div class="context-head"><span>{{ c.version_label }}</span><span class="badge">{{ c.evidence_level }}</span></div>
            <h3>{{ c.title }}</h3>
            <p>{{ c.claim_text }}</p>
            <footer><span>{{ c.relation_type }}</span><span>confidence {{ c.confidence }}</span></footer>
          </article>
        </div>
      </section>

      <section>
        <div class="section-head"><h2>来源</h2></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>等级</th><th>类型</th><th>标题</th><th>发布方</th></tr></thead>
            <tbody>
              <tr v-for="s in data.sources" :key="s.slug">
                <td>{{ s.reliability_tier }}</td>
                <td>{{ s.source_type }}</td>
                <td><a :href="s.url ?? undefined" target="_blank" rel="noreferrer">{{ s.title }}</a></td>
                <td>{{ s.publisher }}</td>
              </tr>
            </tbody>
          </table>
        </div>
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
  min-width: 280px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.search button {
  border: none;
  background: var(--accent);
  color: white;
  padding: 8px 14px;
  border-radius: 6px;
}

.status {
  color: var(--text-muted);
}

main section {
  margin-bottom: 28px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.quick-actions a {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quick-actions span {
  font-size: 13px;
  color: var(--text-muted);
}

.stats {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
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
  font-size: 18px;
}

.stats span {
  font-size: 12px;
  color: var(--text-muted);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.section-head h2 {
  font-size: 18px;
  margin: 0;
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

td span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
}

.badge {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.context-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

.context-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-muted);
}

.context-card h3 {
  font-size: 15px;
  margin: 0 0 4px;
}

.context-card p {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 8px;
}

.context-card footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 820px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
