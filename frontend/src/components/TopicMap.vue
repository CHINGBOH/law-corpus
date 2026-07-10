<script setup lang="ts">
export interface TopicMapCard {
  title: string;
  badge?: string | number | null;
  strong?: string | null;
  description?: string | null;
  footerLabel?: string;
  footerHref?: string;
}

defineProps<{ cards: TopicMapCard[]; emptyText?: string }>();
</script>

<template>
  <div class="topic-map">
    <p v-if="!cards.length" class="empty">{{ emptyText ?? "当前没有内容。" }}</p>
    <article v-for="(card, idx) in cards" :key="idx" class="card">
      <div class="head">
        <span>{{ card.title }}</span>
        <span v-if="card.badge != null" class="badge">{{ card.badge }}</span>
      </div>
      <strong v-if="card.strong">{{ card.strong }}</strong>
      <p v-if="card.description">{{ card.description }}</p>
      <footer v-if="card.footerHref">
        <router-link :to="card.footerHref">{{ card.footerLabel ?? "查看" }}</router-link>
      </footer>
    </article>
  </div>
</template>

<style scoped>
.topic-map {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.head > span:first-child {
  font-weight: 600;
}

.badge {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  white-space: nowrap;
}

.card p {
  margin: 0;
  font-size: 14px;
  color: var(--text-muted);
}

.card footer {
  margin-top: auto;
  padding-top: 4px;
  font-size: 13px;
}

.empty {
  color: var(--text-muted);
  font-size: 14px;
}
</style>
