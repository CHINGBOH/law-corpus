<script setup lang="ts">
import { ref } from "vue";
import { postJson } from "@/api/client";

interface AskResponse {
  ok: boolean;
  error?: string;
  model?: string;
  answer?: string;
  answer_html?: string;
  context_units?: number;
}

const question = ref("");
const status = ref("");
const answerHtml = ref("");

async function ask() {
  const trimmed = question.value.trim();
  if (!trimmed) {
    status.value = "请输入问题";
    return;
  }
  status.value = "查询资料并调用 DeepSeek...";
  answerHtml.value = "";
  try {
    const data = await postJson<AskResponse>("/api/ask", { question: trimmed });
    status.value = data.ok ? `模型：${data.model}，上下文条文：${data.context_units}` : data.error || "查询失败";
    answerHtml.value = data.answer_html || data.answer || "";
  } catch (err) {
    status.value = String(err);
  }
}
</script>

<template>
  <article class="ask-panel">
    <textarea
      v-model="question"
      placeholder="例如：为什么 2023 公司法要把认缴出资改成五年缴足？这和 2013 改革有什么张力？"
    ></textarea>
    <div class="actions">
      <button type="button" @click="ask">问 DeepSeek</button>
      <span>{{ status }}</span>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div class="answer" v-html="answerHtml"></div>
  </article>
</template>

<style scoped>
.ask-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

textarea {
  width: 100%;
  min-height: 72px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font: inherit;
  resize: vertical;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.actions button {
  border: none;
  background: var(--accent);
  color: white;
  padding: 8px 14px;
  border-radius: 6px;
}

.actions span {
  color: var(--text-muted);
  font-size: 13px;
}

.answer {
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.7;
}

.answer :deep(h2),
.answer :deep(h3),
.answer :deep(h4) {
  margin: 12px 0 6px;
}

.answer :deep(code) {
  background: var(--badge-bg);
  border-radius: 4px;
  padding: 1px 4px;
}
</style>
