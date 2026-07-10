import { ref, type Ref } from "vue";
import { getJson } from "@/api/client";
import type { ReaderViewResponse } from "@/types/api";

export function useReaderView() {
  const data: Ref<ReaderViewResponse | null> = ref(null);
  const loading = ref(false);
  const error: Ref<string | null> = ref(null);

  async function loadLaw(version: string, article: number): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const params = new URLSearchParams({ version, article: String(article) });
      const response = await getJson<ReaderViewResponse>(`/api/workspace/reader?${params.toString()}`);
      if (!response.ok) {
        error.value = response.error || "未找到条文";
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

  async function loadInstrument(slug: string, unit: number): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const params = new URLSearchParams({ slug, unit: String(unit) });
      const response = await getJson<ReaderViewResponse>(`/api/workspace/instrument-reader?${params.toString()}`);
      if (!response.ok) {
        error.value = response.error || "未找到规范";
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

  return { data, loading, error, loadLaw, loadInstrument };
}
