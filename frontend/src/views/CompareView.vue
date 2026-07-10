<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import FocusReader from "@/components/FocusReader.vue";
import { getJson } from "@/api/client";
import type { CompareViewResponse } from "@/types/api";

const route = useRoute();
const router = useRouter();
const data = ref<CompareViewResponse | null>(null);
const loading = ref(false);

function query(name: string, fallback: string): string {
  const value = route.query[name];
  return typeof value === "string" && value ? value : fallback;
}

async function refresh() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      left: query("left", "cn_company_law_2018"),
      right: query("right", "cn_company_law_2023"),
      article: query("article", "47"),
    });
    data.value = await getJson<CompareViewResponse>(`/api/workspace/compare?${params.toString()}`);
  } finally {
    loading.value = false;
  }
}

watch(() => [route.query.left, route.query.right, route.query.article], refresh, { immediate: true });

function submit(event: Event) {
  const form = event.target as HTMLFormElement;
  const formData = new FormData(form);
  router.push({
    path: "/compare",
    query: {
      left: String(formData.get("left")),
      right: String(formData.get("right")),
      article: String(formData.get("article")),
    },
  });
}
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div>
        <h1>版本对比</h1>
        <p><router-link to="/graph">返回首页</router-link> · <router-link to="/law">原文阅读</router-link></p>
      </div>
      <form class="reader-controls" @submit.prevent="submit">
        <select name="left" :value="data?.left.slug">
          <option v-for="v in data?.versions ?? []" :key="v.slug" :value="v.slug">{{ v.version_label }}</option>
        </select>
        <select name="right" :value="data?.right.slug">
          <option v-for="v in data?.versions ?? []" :key="v.slug" :value="v.slug">{{ v.version_label }}</option>
        </select>
        <input name="article" :value="data?.article_no ?? 47" inputmode="numeric" aria-label="条号" />
        <button type="submit">对比</button>
      </form>
    </header>

    <p v-if="loading && !data" class="status">加载中...</p>
    <section v-else-if="data" class="compare-grid">
      <article class="compare-pane">
        <FocusReader v-if="data.left.article" :article="data.left.article" :nav-groups="[]" compact />
        <p v-else class="empty">没有找到该版本的对应条文。</p>
      </article>
      <article class="compare-pane">
        <FocusReader v-if="data.right.article" :article="data.right.article" :nav-groups="[]" compact />
        <p v-else class="empty">没有找到该版本的对应条文。</p>
      </article>
    </section>
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

.reader-controls {
  display: flex;
  gap: 8px;
}

.reader-controls select,
.reader-controls input {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.reader-controls input {
  width: 80px;
}

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

.compare-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.empty {
  color: var(--text-muted);
}

@media (max-width: 820px) {
  .compare-grid {
    grid-template-columns: 1fr;
  }
}
</style>
