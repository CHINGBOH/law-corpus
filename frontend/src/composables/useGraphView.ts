import { ref, type Ref } from "vue";
import { getJson, postJson } from "@/api/client";
import type { ExtractCandidatesResponse, GraphViewResponse } from "@/types/api";

export function useGraphView() {
  const data: Ref<GraphViewResponse | null> = ref(null);
  const loading = ref(false);
  const error: Ref<string | null> = ref(null);
  const extractStatus = ref("");

  async function load(nodeKey: string, toNodeKey = ""): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const params = new URLSearchParams({ node_key: nodeKey });
      if (toNodeKey) params.set("to_node_key", toNodeKey);
      const response = await getJson<GraphViewResponse>(`/api/workspace/graph?${params.toString()}`);
      if (!response.ok) {
        error.value = response.error || "未找到该图谱节点";
        data.value = null;
        return;
      }
      data.value = response;
    } catch (err) {
      error.value = String(err);
      data.value = null;
    } finally {
      loading.value = false;
    }
  }

  async function extractCandidates(ref_: string): Promise<void> {
    extractStatus.value = "正在抽取...";
    try {
      const response = await postJson<ExtractCandidatesResponse>("/api/agent/extract-relations", {
        canonical_ref: ref_,
      });
      extractStatus.value = response.ok ? `已写入候选 ${response.created.length} 条` : response.error || "抽取失败";
    } catch (err) {
      extractStatus.value = String(err);
    }
  }

  return { data, loading, error, extractStatus, load, extractCandidates };
}
