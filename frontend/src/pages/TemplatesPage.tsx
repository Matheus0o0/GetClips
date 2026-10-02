import { useState } from "react";
import { LayoutTemplate, Plus } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { TemplateCard } from "@/features/templates/TemplateCard";
import { TemplateFormDialog } from "@/features/templates/TemplateFormDialog";
import {
  useTemplates,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useSetDefaultTemplate,
} from "@/features/templates/api";
import type { EditingTemplate, EditingTemplateConfig } from "@/features/templates/types";

export function TemplatesPage() {
  const { data: templates = [], isLoading } = useTemplates();
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();
  const deleteMutation = useDeleteTemplate();
  const setDefaultMutation = useSetDefaultTemplate();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<EditingTemplate | null>(null);

  function openCreate() {
    setEditing(null);
    setDialogOpen(true);
  }

  function openEdit(t: EditingTemplate) {
    setEditing(t);
    setDialogOpen(true);
  }

  function handleClose() {
    setDialogOpen(false);
    setEditing(null);
  }

  function handleSubmit(name: string, config: EditingTemplateConfig) {
    if (editing) {
      updateMutation.mutate(
        { id: editing.id, name, config },
        { onSuccess: handleClose },
      );
    } else {
      createMutation.mutate(
        { name, config },
        { onSuccess: handleClose },
      );
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LayoutTemplate className="h-5 w-5 text-primary" />
          <h1 className="text-xl font-semibold">Templates de edição</h1>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          Criar template
        </Button>
      </div>

      {isLoading && (
        <div className="text-sm text-muted-foreground">Carregando…</div>
      )}

      {!isLoading && templates.length === 0 && (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <LayoutTemplate className="mx-auto mb-3 h-10 w-10 text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">
            Nenhum template criado ainda.
          </p>
          <Button variant="outline" className="mt-4 gap-2" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Criar o primeiro template
          </Button>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {templates.map((t) => (
          <TemplateCard
            key={t.id}
            template={t}
            onEdit={openEdit}
            onDelete={(id) => deleteMutation.mutate(id)}
            onSetDefault={(id) => setDefaultMutation.mutate(id)}
            isDeleting={deleteMutation.isPending && deleteMutation.variables === t.id}
            isSettingDefault={setDefaultMutation.isPending && setDefaultMutation.variables === t.id}
          />
        ))}
      </div>

      <TemplateFormDialog
        open={dialogOpen}
        initial={editing}
        onClose={handleClose}
        onSubmit={handleSubmit}
        isPending={isPending}
      />
    </div>
  );
}
