<script setup lang="ts">
import { watch, ref } from "vue";
import { useRoute } from "vue-router";
import TopicMap from "@/components/TopicMap.vue";
import { getJson } from "@/api/client";
import type { TopicLinkCard, TopicViewResponse } from "@/types/api";

const route = useRoute();
const data = ref<TopicViewResponse | null>(null);
const loading = ref(true);

function currentSlug(): string {
  const value = route.query.slug;
  return typeof value === "string" && value ? value : "capital-credit";
}

async function refresh() {
  loading.value = true;
  data.value = await getJson<TopicViewResponse>(`/api/workspace/topic?slug=${currentSlug()}`);
  loading.value = false;
}

watch(() => route.query.slug, refresh, { immediate: true });

function toCards(links: TopicLinkCard[]) {
  return links.map((link) => ({
    title: link.meta,
    strong: link.title,
    description: link.description,
    footerLabel: "打开",
    footerHref: link.href,
  }));
}
</script>

<template>
  <div class="page">
    <p v-if="loading" class="status">加载中...</p>
    <template v-else-if="data">
      <header class="topbar">
        <div>
          <h1>{{ data.topic.title }}</h1>
          <p>{{ data.topic.pillar_title }} · {{ data.topic.question }}</p>
        </div>
        <div class="inline-actions">
          <router-link to="/">返回首页</router-link>
          <router-link to="/instrument?slug=cn_company_law">返回公司法</router-link>
        </div>
      </header>

      <section class="stats">
        <article><strong>{{ data.topic.title }}</strong><span>专题</span></article>
        <article><strong>{{ data.topic.pillar_title }}</strong><span>承力柱</span></article>
        <article><strong>{{ data.topic.link_count }}</strong><span>关联节点</span></article>
        <article><strong>{{ data.topic.explanation_count }}</strong><span>解释数</span></article>
        <article><strong>{{ data.topic.status }}</strong><span>状态</span></article>
      </section>

      <section>
        <div class="section-head"><h2>专题摘要</h2></div>
        <article class="context-card"><p>{{ data.topic.summary }}</p></article>
      </section>

      <section>
        <div class="section-head"><h2>核心法条与规范</h2></div>
        <TopicMap :cards="toCards(data.core)" empty-text="当前没有核心节点。" />
      </section>

      <section>
        <div class="section-head"><h2>补充节点</h2></div>
        <TopicMap :cards="toCards(data.support)" empty-text="当前没有补充节点。" />
      </section>

      <section>
        <div class="section-head"><h2>政策与历史背景</h2></div>
        <TopicMap :cards="toCards(data.background)" empty-text="当前没有背景事件。" />
      </section>

      <section>
        <div class="section-head"><h2>大白话与提纲</h2></div>
        <div class="context-grid">
          <p v-if="!data.explanations.length" class="empty">当前还没有解释说明。</p>
          <article v-for="(item, idx) in data.explanations" :key="idx" class="context-card">
            <div class="context-head"><span>{{ item.title }}</span><span class="badge">{{ item.explanation_type }}</span></div>
            <p>{{ item.body }}</p>
            <footer><span>confidence {{ item.confidence }}</span><span>{{ item.source_title }}</span></footer>
          </article>
        </div>
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

.context-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.context-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.badge {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.context-card footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

@media (max-width: 820px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
