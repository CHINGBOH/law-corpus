<script setup lang="ts">
import { watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ReviewDrawer from "@/components/ReviewDrawer.vue";
import { useReviewQueue } from "@/composables/useReviewQueue";

const route = useRoute();
const router = useRouter();
const { bundle, loading, actionStatus, load, accept, reject, edit } = useReviewQueue();

function currentStatus(): string {
  const value = route.query.status;
  return typeof value === "string" ? value : "pending";
}

function currentCandidateId(): string {
  const value = route.query.candidate_id;
  return typeof value === "string" ? value : "";
}

watch(
  () => [route.query.status, route.query.candidate_id],
  () => load(currentStatus(), currentCandidateId()),
  { immediate: true },
);

function changeStatus(event: Event) {
  const status = (event.target as HTMLSelectElement).value;
  router.push({ path: "/review", query: { status } });
}

function selectCandidate(candidateId: string) {
  router.push({ path: "/review", query: { status: currentStatus(), candidate_id: candidateId } });
}
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div>
        <h1>候选审核台</h1>
        <p>模型先提议，你再接受、驳回或改写。</p>
      </div>
      <select :value="currentStatus()" @change="changeStatus">
        <option v-for="option in bundle?.status_options ?? []" :key="option" :value="option">
          {{ option || "all" }}
        </option>
      </select>
    </header>

    <p v-if="loading && !bundle" class="status">加载中...</p>
    <ReviewDrawer
      v-else-if="bundle"
      :bundle="bundle"
      :action-status="actionStatus"
      @select="selectCandidate"
      @accept="accept"
      @reject="reject"
      @edit="edit"
    />
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
</style>
