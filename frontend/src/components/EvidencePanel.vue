<script setup lang="ts">
import type { EvidenceInfo } from "@/types/api";

defineProps<{ evidence: EvidenceInfo; compact?: boolean }>();
</script>

<template>
  <footer class="evidence" :class="{ compact }">
    <span v-if="evidence.evidence_level" class="badge">{{ evidence.evidence_level }}</span>
    <span v-if="evidence.confidence != null" class="confidence">confidence {{ evidence.confidence }}</span>
    <a v-if="evidence.source_url" :href="evidence.source_url" target="_blank" rel="noreferrer">
      {{ evidence.source_title || "来源" }}
    </a>
    <span v-else-if="evidence.source_title">{{ evidence.source_title }}</span>
    <p v-if="!compact && evidence.excerpt_text" class="excerpt">{{ evidence.excerpt_text }}</p>
  </footer>
</template>

<style scoped>
.evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: var(--text-muted);
}

.evidence.compact {
  font-size: 12px;
}

.badge {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.excerpt {
  flex-basis: 100%;
  margin: 4px 0 0;
  font-style: italic;
}
</style>
