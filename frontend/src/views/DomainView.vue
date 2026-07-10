<script setup lang="ts">
import { watch, ref } from "vue";
import { useRoute } from "vue-router";
import { getJson } from "@/api/client";
import type { DomainViewResponse } from "@/types/api";

const route = useRoute();
const data = ref<DomainViewResponse | null>(null);
const loading = ref(true);

function currentSlug(): string {
  const value = route.query.slug;
  return typeof value === "string" && value ? value : "commercial-organization";
}

async function refresh() {
  loading.value = true;
  data.value = await getJson<DomainViewResponse>(`/api/workspace/domain?slug=${currentSlug()}`);
  loading.value = false;
}

watch(() => route.query.slug, refresh, { immediate: true });
</script>

<template>
  <div class="page">
    <p v-if="loading" class="status">加载中...</p>
    <template v-else-if="data">
      <header class="topbar">
        <div>
          <h1>{{ data.domain.name }}</h1>
          <p>{{ data.domain.description }}</p>
        </div>
        <router-link to="/">返回首页</router-link>
      </header>

      <section class="stats">
        <article><strong>{{ data.domain.instrument_count }}</strong><span>规范数</span></article>
        <article><strong>{{ data.domain.name }}</strong><span>法域</span></article>
        <article><strong>{{ data.domain.sort_order }}</strong><span>排序</span></article>
        <article><strong>先看体系，再钻条文</strong><span>主线</span></article>
        <article><strong>{{ data.domain.slug }}</strong><span>入口</span></article>
      </section>

      <section>
        <div class="section-head"><h2>规范</h2></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>规范</th><th>定位</th><th>类型</th><th>当前版本</th></tr></thead>
            <tbody>
              <tr v-for="i in data.instruments" :key="i.slug">
                <td><router-link :to="`/instrument?slug=${i.slug}`"><strong>{{ i.short_title }}</strong></router-link><span>{{ i.canonical_title }}</span></td>
                <td><span class="badge">{{ i.is_primary ? "主节点" : "关联节点" }}</span></td>
                <td>{{ i.instrument_type }}</td>
                <td>{{ i.current_version_label }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.page {
  max-width: 1000px;
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

.status {
  color: var(--text-muted);
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

.section-head h2 {
  font-size: 18px;
  margin: 0 0 8px;
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

@media (max-width: 820px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
