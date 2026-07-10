<script setup lang="ts">
import { reactive, watch } from "vue";
import EvidencePanel from "@/components/EvidencePanel.vue";
import type { ReviewBundle } from "@/types/api";

const props = defineProps<{ bundle: ReviewBundle; actionStatus: string }>();
const emit = defineEmits<{
  select: [candidateId: string];
  accept: [candidateId: string];
  reject: [candidateId: string, reviewNote: string];
  edit: [candidateId: string, relationType: string, claimText: string, confidence: string, reviewNote: string];
}>();

const form = reactive({
  relationType: "",
  claimText: "",
  confidence: "",
  reviewNote: "",
});

function syncForm() {
  const detail = props.bundle.detail;
  form.relationType = detail?.relation_type ?? "";
  form.claimText = detail?.claim_text ?? "";
  form.confidence = detail != null && detail.confidence != null ? String(detail.confidence) : "";
  form.reviewNote = detail?.review_note ?? "";
}

watch(() => props.bundle.detail?.id, syncForm, { immediate: true });
</script>

<template>
  <section class="review-layout">
    <aside class="candidate-list">
      <div class="nav-title">候选队列</div>
      <p v-if="!bundle.candidates.length" class="empty">当前状态下没有候选关系。</p>
      <a
        v-for="item in bundle.candidates"
        :key="item.id"
        class="candidate-item"
        :class="{ active: item.id === bundle.selected_id }"
        href="#"
        @click.prevent="emit('select', item.id)"
      >
        <strong>{{ item.relation_type_label }}</strong>
        <span>{{ item.subject_title }} -&gt; {{ item.object_title }}</span>
        <span>{{ item.status_label }} · {{ item.source_title }}</span>
      </a>
    </aside>

    <section class="detail-pane" v-if="bundle.detail">
      <article class="result">
        <div>{{ bundle.detail.status_label }} · {{ bundle.detail.proposer }}</div>
        <h2>{{ bundle.detail.subject_title }} -&gt; {{ bundle.detail.object_title }}</h2>
        <p>{{ bundle.detail.claim_text }}</p>
        <p><strong>关系语义：</strong>{{ bundle.detail.relation_type_label }}</p>
        <footer class="result-actions">
          <a :href="bundle.detail.graph_hrefs.subject">主体图谱</a>
          <a :href="bundle.detail.graph_hrefs.path">穿透路径</a>
        </footer>
      </article>

      <article class="edit-panel">
        <div class="section-head"><h2>编辑与审核</h2></div>
        <label>关系类型</label>
        <input v-model="form.relationType" />
        <label>主张</label>
        <textarea v-model="form.claimText" rows="3"></textarea>
        <label>置信度</label>
        <input v-model="form.confidence" />
        <label>审核备注</label>
        <textarea v-model="form.reviewNote" rows="2"></textarea>
        <div class="actions">
          <button type="button" @click="emit('accept', bundle.detail.id)">接受</button>
          <button
            type="button"
            @click="emit('edit', bundle.detail.id, form.relationType, form.claimText, form.confidence, form.reviewNote)"
          >
            改写
          </button>
          <button type="button" @click="emit('reject', bundle.detail.id, form.reviewNote)">驳回</button>
          <span>{{ actionStatus }}</span>
        </div>
      </article>
    </section>
    <p v-else class="empty">当前没有可审核候选。</p>

    <aside class="context-pane" v-if="bundle.detail">
      <section>
        <h3>证据来源</h3>
        <EvidencePanel :evidence="bundle.detail.evidence" />
      </section>
      <section>
        <h3>图谱跳转</h3>
        <a :href="bundle.detail.graph_hrefs.subject">打开主体节点</a>
        <a :href="bundle.detail.graph_hrefs.object">打开客体节点</a>
      </section>
    </aside>
  </section>
</template>

<style scoped>
.review-layout {
  display: grid;
  grid-template-columns: 280px 1fr 260px;
  gap: 20px;
  align-items: start;
}

.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.candidate-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  font-size: 13px;
  color: var(--text);
}

.candidate-item.active {
  border-color: var(--accent);
  background: var(--badge-bg);
}

.candidate-item span {
  color: var(--text-muted);
  font-size: 12px;
}

.detail-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result,
.edit-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.edit-panel label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

.edit-panel input,
.edit-panel textarea {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font: inherit;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.actions button {
  border: none;
  background: var(--accent);
  color: white;
  padding: 8px 14px;
  border-radius: 6px;
}

.context-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-size: 13px;
}

.context-pane section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
}

.context-pane h3 {
  font-size: 14px;
  margin: 0 0 8px;
}

.context-pane a {
  display: block;
  margin-bottom: 4px;
}

.empty {
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .review-layout {
    grid-template-columns: 1fr;
  }
}
</style>
