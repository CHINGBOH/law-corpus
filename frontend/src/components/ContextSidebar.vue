<script setup lang="ts">
import SidebarCard from "@/components/SidebarCard.vue";
import type { SidebarLink } from "@/types/api";

interface Section {
  title: string;
  meta?: string;
  links?: SidebarLink[];
  emptyText?: string;
}

defineProps<{ sections?: Section[] }>();
</script>

<template>
  <aside class="context-sidebar">
    <SidebarCard v-for="(section, idx) in sections ?? []" :key="idx" :title="section.title" :meta="section.meta">
      <div class="mini-links" v-if="section.links && section.links.length">
        <a v-for="link in section.links" :key="link.href + link.label" :href="link.href">{{ link.label }}</a>
      </div>
      <p v-else class="empty">{{ section.emptyText ?? "暂无内容。" }}</p>
    </SidebarCard>
    <slot />
  </aside>
</template>

<style scoped>
.context-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.mini-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty {
  color: var(--text-muted);
  font-size: 13px;
  margin: 0;
}

@media (min-width: 821px) {
  .context-sidebar {
    position: sticky;
    top: 16px;
    align-self: start;
  }
}
</style>
