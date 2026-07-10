<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ContextSidebar from "@/components/ContextSidebar.vue";
import SidebarCard from "@/components/SidebarCard.vue";
import FocusReader from "@/components/FocusReader.vue";
import { useReaderView } from "@/composables/useReaderView";

const route = useRoute();
const router = useRouter();
const { data, loading, error, loadLaw, loadInstrument } = useReaderView();

const isLawMode = computed(() => route.path === "/law");

function query(name: string, fallback: string): string {
  const value = route.query[name];
  return typeof value === "string" && value ? value : fallback;
}

async function refresh() {
  if (isLawMode.value) {
    await loadLaw(query("version", "cn_company_law_2023"), Number(query("article", "1")) || 1);
  } else {
    await loadInstrument(query("slug", "cn_civil_code"), Number(query("unit", "1")) || 1);
  }
}

watch(() => [route.path, route.query.version, route.query.article, route.query.slug, route.query.unit], refresh, {
  immediate: true,
});

function changeVersion(event: Event) {
  router.push({ path: "/law", query: { version: (event.target as HTMLSelectElement).value, article: 1 } });
}
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div>
        <h1>{{ data?.title ?? (isLawMode ? "原文阅读" : "条文阅读") }}</h1>
        <p v-if="isLawMode">
          <router-link to="/graph">返回首页</router-link> ·
          <router-link :to="data?.compare_href ?? '/compare'">版本对比</router-link>
        </p>
        <p v-else>
          <router-link to="/graph">返回首页</router-link> ·
          <router-link :to="`/instrument?slug=${data?.instrument_slug ?? ''}`">返回规范页</router-link>
        </p>
      </div>
      <select v-if="isLawMode && data?.versions" :value="data.selected_version" @change="changeVersion">
        <option v-for="v in data.versions" :key="v.slug" :value="v.slug">{{ v.version_label }}</option>
      </select>
    </header>

    <p v-if="loading && !data" class="status">加载中...</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <main v-else-if="data">
      <div class="layout">
        <FocusReader
          :article="data.article"
          :nav-groups="data.nav_groups"
          :prev="data.prev"
          :next="data.next"
          :compare-href="data.compare_href"
        />
        <ContextSidebar
          :sections="[
            { title: '常用动作', links: data.sidebar.actions },
            { title: '关联法条', links: data.sidebar.relations, emptyText: '当前条文尚未补录跨法关系。' },
            { title: '相关专题', links: data.sidebar.topics, emptyText: '当前条文尚未挂接专题。' },
          ]"
        >
          <SidebarCard title="当前条文">
            <p><strong>{{ data.sidebar.meta.label }}</strong></p>
            <p><code>{{ data.sidebar.meta.ref }}</code></p>
          </SidebarCard>
          <SidebarCard v-if="data.sidebar.tip" title="阅读提示">
            <p>{{ data.sidebar.tip }}</p>
          </SidebarCard>
        </ContextSidebar>
      </div>
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

.topbar select {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.status {
  color: var(--text-muted);
}

.status.error {
  color: #b3261e;
}

.layout {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 20px;
  align-items: start;
}

@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
