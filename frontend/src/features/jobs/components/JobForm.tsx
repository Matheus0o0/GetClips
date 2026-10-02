import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Link as LinkIcon, Loader2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { useCreateJob, useUploadFile } from "@/features/jobs/api/hooks";

const MODELS = [
  { value: "distil-large-v3", label: "Distil Large v3 (recomendado)" },
  { value: "large-v3", label: "Large v3 (máxima qualidade)" },
  { value: "medium", label: "Medium" },
  { value: "small", label: "Small" },
  { value: "base", label: "Base" },
  { value: "tiny", label: "Tiny (rápido)" },
];

const LANGS = [
  { value: "auto", label: "Auto-detectar" },
  { value: "pt", label: "Português" },
  { value: "en", label: "Inglês" },
  { value: "es", label: "Espanhol" },
  { value: "fr", label: "Francês" },
  { value: "de", label: "Alemão" },
  { value: "it", label: "Italiano" },
  { value: "ja", label: "Japonês" },
  { value: "zh", label: "Chinês" },
];

export function JobForm() {
  const nav = useNavigate();
  const create = useCreateJob();
  const upload = useUploadFile();

  const [mode, setMode] = useState<"url" | "file">("url");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState("distil-large-v3");
  const [language, setLanguage] = useState("pt");

  const isBusy = create.isPending || upload.isPending;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      let jobId: string;
      if (mode === "url") {
        if (!url.trim()) return;
        const job = await create.mutateAsync({
          url: url.trim(),
          params: { model, language, beam_size: 5 },
        });
        jobId = job.id;
      } else {
        if (!file) return;
        const job = await upload.mutateAsync({ file, model, language, beamSize: 5 });
        jobId = job.id;
      }
      nav(`/jobs/${jobId}`);
    } catch (err) {
      alert(`Erro: ${(err as Error).message}`);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-6">
      <div className="flex gap-2">
        <Button
          type="button"
          variant={mode === "url" ? "default" : "outline"}
          onClick={() => setMode("url")}
        >
          <LinkIcon className="h-4 w-4" />
          URL
        </Button>
        <Button
          type="button"
          variant={mode === "file" ? "default" : "outline"}
          onClick={() => setMode("file")}
        >
          <Upload className="h-4 w-4" />
          Arquivo local
        </Button>
      </div>

      {mode === "url" ? (
        <div className="space-y-2">
          <Label htmlFor="url">URL do vídeo</Label>
          <Input
            id="url"
            type="url"
            required
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            YouTube, TikTok, Instagram, Facebook, Twitter/X, Vimeo, URL direta.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <Label htmlFor="file">Arquivo (vídeo ou áudio)</Label>
          <Input
            id="file"
            type="file"
            accept="video/*,audio/*"
            required
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <p className="text-xs text-muted-foreground">Até 4 GB.</p>
        </div>
      )}

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

      <Button type="submit" size="lg" disabled={isBusy} className="w-full">
        {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        {isBusy ? "Enviando..." : "Iniciar transcrição"}
      </Button>
    </form>
  );
}
