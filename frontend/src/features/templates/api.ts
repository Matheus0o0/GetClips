import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { EditingTemplate, EditingTemplateConfig } from "./types";

const BASE = "/api/v1/templates";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export const templateKeys = {
  all: ["templates"] as const,
  detail: (id: string) => ["templates", id] as const,
};

export function useTemplates() {
  return useQuery({
    queryKey: templateKeys.all,
    queryFn: () => fetchJSON<EditingTemplate[]>(BASE),
  });
}

export function useTemplate(id: string) {
  return useQuery({
    queryKey: templateKeys.detail(id),
    queryFn: () => fetchJSON<EditingTemplate>(`${BASE}/${id}`),
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; config?: EditingTemplateConfig }) =>
      fetchJSON<EditingTemplate>(BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: templateKeys.all }),
  });
}

export function useUpdateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      name,
      config,
    }: { id: string; name?: string; config?: EditingTemplateConfig }) =>
      fetchJSON<EditingTemplate>(`${BASE}/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, config }),
      }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: templateKeys.all });
      qc.invalidateQueries({ queryKey: templateKeys.detail(vars.id) });
    },
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      fetchJSON<{ message: string }>(`${BASE}/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: templateKeys.all }),
  });
}

export function useSetDefaultTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      fetchJSON<EditingTemplate>(`${BASE}/${id}/set-default`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: templateKeys.all }),
  });
}
