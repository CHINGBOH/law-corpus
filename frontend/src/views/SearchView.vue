<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { getJson } from "@/api/client";
import type { SearchViewResponse } from "@/types/api";

const route = useRoute();
const data = ref<SearchViewResponse | null>(null);
const loading = ref(false);

function currentQuery(): string {
  const value = route.query.q;
  return typeof value === "string" ? value : "";
}

async function refresh() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ q: currentQuery() });
    data.value = await getJson<SearchViewResponse>(`/api/workspace/search?${params.toString()}`);
  } finally {
    loading.value = false;
  }
}

watch(() => route.query.q, refresh, { immediate: true });
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div>
        <h1>查询</h1>
        <p><router-link to="/">返回首页</router-link></p>
      </div>
    </header>

    <p v-if="loading" class="status">加载中...</p>
    <section v-else>
      <p v-if="!data?.results.length" class="empty">当前还没有匹配结果。</p>
      <article v-for="(r, idx) in data?.results ?? []" :key="idx" class="result">
        <div>{{ r.instrument_title }} · {{ r.version_label }} · {{ r.canonical_ref }}</div>
        <h2>{{ r.unit_number }} {{ r.title }}</h2>
        <p>{{ r.text }}</p>
        <footer>
          <router-link v-for="action in r.actions" :key="action.href" :to="action.href">{{ action.label }}</router-link>
        </footer>
      </article>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.topbar h1 {
  font-size: 26px;
  margin: 0 0 4px;
}

.topbar p {
  margin: 0;
  color: var(--text-muted);
}

.status,
.empty {
  color: var(--text-muted);
}

.result {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
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
  margin-top: 8px;
  font-size: 13px;
}
</style>
