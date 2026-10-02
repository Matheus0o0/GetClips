import { useState } from "react";
import { RefreshCcw, Loader2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { useRerunJob } from "@/features/jobs/api/hooks";

const MODELS = [
  { value: "distil-large-v3", label: "Distil Large v3 (recomendado)" },
  { value: "large-v3", label: "Large v3 (máxima qualidade)" },
  { value: "medium", label: "Medium" },
  { value: "small", label: "Small" },
  { value: "base", label: "Base" },
  { value: "tiny", label: "Tiny (rápido)" },
];

const LANGS = [
  { value: "pt", label: "Português (forçar)" },
  { value: "en", label: "Inglês (forçar)" },
  { value: "es", label: "Espanhol (forçar)" },
  { value: "fr", label: "Francês (forçar)" },
  { value: "de", label: "Alemão (forçar)" },
  { value: "it", label: "Italiano (forçar)" },
  { value: "ja", label: "Japonês (forçar)" },
  { value: "zh", label: "Chinês (forçar)" },
  { value: "auto", label: "Auto-detectar" },
];

export function RerunPanel({
  jobId,
  currentModel,
  currentLanguage,
}: {
  jobId: string;
  currentModel: string;
  currentLanguage: string;
}) {
  const [open, setOpen] = useState(false);
  const [model, setModel] = useState(currentModel);
  const [language, setLanguage] = useState(
    currentLanguage === "auto" ? "pt" : currentLanguage,
  );
  const rerun = useRerunJob();

  async function submit() {
    await rerun.mutateAsync({
      jobId,
      payload: { model, language },
    });
  }

  if (!open) {
    return (
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
      >
        <RefreshCcw className="h-4 w-4" />
        Gerar novamente
      </Button>
    );
  }

  return (
    <div className="border rounded-lg p-4 space-y-4 bg-background">
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium">Reprocessar transcrição</div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setOpen(false)}
        >
          Cancelar
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Modelo</Label>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MODELS.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Idioma</Label>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LANGS.map((l) => (
                <SelectItem key={l.value} value={l.value}>
                  {l.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Um novo job será criado com esses parâmetros. Se o arquivo original
        ainda estiver em disco, o download é ignorado.
      </p>

      <Button
        type="button"
        onClick={submit}
        disabled={rerun.isPending}
        className="w-full"
      >
        {rerun.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <RefreshCcw className="h-4 w-4" />
        )}
        {rerun.isPending ? "Enviando..." : "Confirmar e regenerar"}
      </Button>
    </div>
  );
}
