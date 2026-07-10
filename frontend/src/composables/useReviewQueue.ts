import { ref, type Ref } from "vue";
import { getJson, postJson } from "@/api/client";
import type { ReviewBundle } from "@/types/api";

export function useReviewQueue() {
  const bundle: Ref<ReviewBundle | null> = ref(null);
  const loading = ref(false);
  const actionStatus = ref("");

  async function load(status: string, candidateId = ""): Promise<void> {
    loading.value = true;
    try {
      const params = new URLSearchParams({ status });
      if (candidateId) params.set("candidate_id", candidateId);
      bundle.value = await getJson<ReviewBundle>(`/api/workspace/review?${params.toString()}`);
    } finally {
      loading.value = false;
    }
  }

  // Every mutation returns the full refreshed bundle (list + detail), so we
  // just replace local state wholesale instead of re-fetching separately —
  // this is what fixes the legacy page's stale-list-after-action bug.
  async function accept(candidateId: string): Promise<void> {
    actionStatus.value = "处理中...";
    bundle.value = await postJson<ReviewBundle>("/api/workspace/review/candidate/accept", {
      candidate_id: candidateId,
      status: bundle.value?.status ?? "pending",
    });
    actionStatus.value = "已接受";
  }

  async function reject(candidateId: string, reviewNote: string): Promise<void> {
    actionStatus.value = "处理中...";
    bundle.value = await postJson<ReviewBundle>("/api/workspace/review/candidate/reject", {
      candidate_id: candidateId,
      review_note: reviewNote,
      status: bundle.value?.status ?? "pending",
    });
    actionStatus.value = "已驳回";
  }

  async function edit(
    candidateId: string,
    relationType: string,
    claimText: string,
    confidence: string,
    reviewNote: string,
  ): Promise<void> {
    actionStatus.value = "处理中...";
    bundle.value = await postJson<ReviewBundle>("/api/workspace/review/candidate/edit", {
      candidate_id: candidateId,
      relation_type: relationType,
      claim_text: claimText,
      confidence,
      review_note: reviewNote,
      status: bundle.value?.status ?? "pending",
    });
    actionStatus.value = "已保存";
  }

  return { bundle, loading, actionStatus, load, accept, reject, edit };
}
