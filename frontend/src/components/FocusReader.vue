<script setup lang="ts">
import { computed } from "vue";
import type { ArticleUnit, NavGroup, NavLink } from "@/types/api";

const props = defineProps<{
  article: ArticleUnit;
  navGroups: NavGroup[];
  prev?: NavLink;
  next?: NavLink;
  compareHref?: string | null;
  compact?: boolean;
}>();

const paragraphs = computed(() =>
  (props.article.text || "").split("\n").filter((line) => line.trim().length > 0),
);
</script>

<template>
  <div class="focus-reader" :class="{ compact }">
    <aside v-if="!compact" class="article-nav">
      <div class="nav-title">条文导航</div>
      <details v-for="group in navGroups" :key="group.start" :open="group.open">
        <summary>第{{ group.start }}-{{ group.end }}条</summary>
        <div class="links">
          <router-link
            v-for="item in group.items"
            :key="item.unit_number_int"
            :to="item.href"
            class="article-link"
            :class="{ active: item.active }"
          >
            {{ item.unit_number }}
          </router-link>
        </div>
      </details>
    </aside>

    <section class="article-pane">
      <div v-if="!compact && (prev || next || compareHref)" class="reader-strip">
        <router-link v-if="prev?.enabled" :to="prev.href">{{ prev.label }}</router-link>
        <span v-else-if="prev" class="disabled-link">{{ prev.label }}</span>
        <router-link v-if="compareHref" :to="compareHref">与2023对比</router-link>
        <router-link v-if="next?.enabled" :to="next.href">{{ next.label }}</router-link>
        <span v-else-if="next" class="disabled-link">{{ next.label }}</span>
      </div>
      <div class="article-meta">
        {{ article.version_label }} · <code>{{ article.canonical_ref }}</code>
      </div>
      <h2>{{ article.unit_number }}</h2>
      <div class="article-text">
        <p v-for="(line, idx) in paragraphs" :key="idx">{{ line }}</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.focus-reader {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 20px;
  align-items: start;
}

.focus-reader.compact {
  grid-template-columns: 1fr;
}

.article-nav {
  position: sticky;
  top: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.links {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px 0;
}

.article-link {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
}

.article-link.active {
  background: var(--accent);
  color: white;
}

.article-pane {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
}

.reader-strip {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 12px;
}

.disabled-link {
  color: var(--text-muted);
}

.article-meta {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.article-pane h2 {
  margin: 0 0 12px;
}

.article-text p {
  font-size: 17px;
  line-height: 1.85;
  margin: 0 0 12px;
}

@media (max-width: 820px) {
  .focus-reader {
    grid-template-columns: 1fr;
  }
}
</style>
