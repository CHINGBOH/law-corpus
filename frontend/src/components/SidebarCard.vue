<script setup lang="ts">
defineProps<{ title: string; meta?: string }>();
</script>

<template>
  <article class="sidebar-card">
    <div class="head">
      <h2>{{ title }}</h2>
      <span v-if="meta">{{ meta }}</span>
    </div>
    <div class="body">
      <slot />
    </div>
  </article>
</template>

<style scoped>
.sidebar-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.head h2 {
  font-size: 16px;
  margin: 0;
}

.head span {
  font-size: 12px;
  color: var(--text-muted);
}

.body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
}
</style>
