import { Star, Trash2, Pencil } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { cn } from "@/shared/lib/utils";
import type { EditingTemplate } from "./types";

interface Props {
  template: EditingTemplate;
  onEdit: (t: EditingTemplate) => void;
  onDelete: (id: string) => void;
  onSetDefault: (id: string) => void;
  isDeleting?: boolean;
  isSettingDefault?: boolean;
}

export function TemplateCard({
  template,
  onEdit,
  onDelete,
  onSetDefault,
  isDeleting,
  isSettingDefault,
}: Props) {
  const cfg = template.config;

  return (
    <div
      className={cn(
        "relative flex flex-col gap-3 rounded-lg border bg-card p-4 transition-shadow hover:shadow-md",
        template.is_default && "border-primary ring-1 ring-primary",
      )}
    >
      {template.is_default && (
        <Badge className="absolute right-3 top-3 gap-1 text-xs">
          <Star className="h-3 w-3 fill-current" />
          Padrão
        </Badge>
      )}

      <div className="pr-16">
        <h3 className="font-semibold leading-tight">{template.name}</h3>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <dt>Formato</dt>
        <dd className="text-foreground">{cfg.video.aspect_ratio} · {cfg.video.resolution}</dd>
        <dt>Legendas</dt>
        <dd className="text-foreground">{cfg.captions.words_per_block} palavras · {cfg.captions.style}</dd>
        <dt>Tracking</dt>
        <dd className="text-foreground">{cfg.tracking.enabled ? "Ativo" : "Desativado"}</dd>
        <dt>Zoom dinâmico</dt>
        <dd className="text-foreground">{cfg.camera.dynamic_zoom ? `até ${cfg.camera.max_zoom}×` : "Desativado"}</dd>
        <dt>Jump cuts</dt>
        <dd className="text-foreground">{cfg.cuts.jump_cuts ? "Sim" : "Não"}</dd>
        <dt>Silêncio</dt>
        <dd className="text-foreground">{cfg.cuts.remove_silence ? "Removido" : "Mantido"}</dd>
      </dl>

      <div className="flex items-center gap-2 pt-1">
        {!template.is_default && (
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5 text-xs"
            disabled={isSettingDefault}
            onClick={() => onSetDefault(template.id)}
          >
            <Star className="h-3.5 w-3.5" />
            Definir padrão
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          className="gap-1.5 text-xs"
          onClick={() => onEdit(template)}
        >
          <Pencil className="h-3.5 w-3.5" />
          Editar
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="ml-auto gap-1.5 text-xs text-destructive hover:text-destructive"
          disabled={isDeleting}
          onClick={() => onDelete(template.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
          Excluir
        </Button>
      </div>
    </div>
  );
}
