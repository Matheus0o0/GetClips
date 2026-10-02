import { useQuery } from "@tanstack/react-query";
import { Download, Sparkles, Scissors, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Progress } from "@/shared/ui/progress";
import { Badge } from "@/shared/ui/badge";
import { api } from "@/shared/lib/api";
import { formatDuration } from "@/shared/lib/format";
import {
  useClips,
  useCreateHighlights,
  useRenderClip,
} from "@/features/clips/api/hooks";
import type { ClipDTO } from "@/shared/types/clip";

interface Props {
  jobId: string;
  transcriptionAvailable: boolean;
}

export function ClipsPanel({ jobId, transcriptionAvailable }: Props) {
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.settings(),
  });
  const clipsQ = useClips(jobId);
  const createHl = useCreateHighlights(jobId);
  const renderClip = useRenderClip(jobId);

  const canRequest = transcriptionAvailable && settings?.highlight_configured;
  const clips = clipsQ.data ?? [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle className="flex items-center gap-2">
            <Scissors className="h-5 w-5" /> Cortes verticais
          </CardTitle>
          {canRequest && (
            <Button
              size="sm"
              onClick={() => createHl.mutate({})}
              disabled={createHl.isPending}
            >
              <Sparkles className="h-4 w-4" />
              {clips.length ? "Gerar mais candidatos" : "Sugerir cortes"}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {!transcriptionAvailable && (
          <p className="text-sm text-muted-foreground">
            Aguarde a transcrição terminar antes de pedir cortes.
          </p>
        )}
        {transcriptionAvailable && !settings?.highlight_configured && (
          <div className="rounded-md border border-amber-500/40 bg-amber-500/5 p-3 text-sm">
            <div className="flex items-center gap-2 font-medium">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              {settings?.highlight_provider === "ollama" ? "Ollama não disponível" : "LLM não configurada"}
            </div>
            <p className="mt-1 text-muted-foreground">
              {settings?.highlight_provider === "ollama"
                ? <>Inicie o Ollama localmente (<code>ollama serve</code>) e certifique-se que o modelo está baixado.</>
                : <>Defina <code>{settings?.highlight_provider === "anthropic" ? "ANTHROPIC_API_KEY" : "OPENAI_API_KEY"}</code> em <code>backend/.env</code>.</>
              }
            </p>
          </div>
        )}

        {createHl.isError && (
          <p className="text-sm text-destructive">
            {(createHl.error as Error).message}
          </p>
        )}

        {clips.length === 0 && canRequest && !createHl.isPending && (
          <p className="text-sm text-muted-foreground">
            Nenhum candidato ainda. Clique em <b>Sugerir cortes</b>.
          </p>
        )}

        {createHl.isPending && (
          <div className="flex items-center gap-3 rounded-md border border-border bg-muted/40 p-3">
            <Loader2 className="h-4 w-4 animate-spin shrink-0 text-muted-foreground" />
            <div className="text-sm">
              <p className="font-medium">Analisando transcrição com IA local…</p>
              <p className="text-muted-foreground text-xs mt-0.5">Isso pode levar 1–2 minutos dependendo do tamanho do vídeo.</p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {clips.map((c) => (
            <ClipRow
              key={c.id}
              clip={c}
              onRender={() => renderClip.mutate(c.id)}
              renderPending={renderClip.isPending && renderClip.variables === c.id}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ClipRow({
  clip,
  onRender,
  renderPending,
}: {
  clip: ClipDTO;
  onRender: () => void;
  renderPending: boolean;
}) {
  const scorePct = Math.round(clip.score * 100);
  return (
    <div className="rounded-md border p-3 bg-background space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>
              {formatDuration(clip.inicio)} → {formatDuration(clip.fim)}
            </span>
            <span>·</span>
            <span>{formatDuration(clip.duration)}</span>
            <span>·</span>
            <span>score {scorePct}</span>
            <ClipStatusBadge status={clip.status} />
          </div>
          <div className="text-sm font-medium">
            {clip.hook_text || "(sem hook)"}
          </div>
          {clip.motivo && (
            <div className="text-xs text-muted-foreground">{clip.motivo}</div>
          )}
        </div>
        <div className="shrink-0">
          {clip.status === "pending" && (
            <Button size="sm" onClick={onRender} disabled={renderPending}>
              Renderizar
            </Button>
          )}
          {clip.status === "ready" && (
            <Button size="sm" variant="outline" asChild>
              <a href={api.clipDownloadUrl(clip.id)} download>
                <Download className="h-4 w-4" /> Baixar
              </a>
            </Button>
          )}
        </div>
      </div>
      {clip.status === "rendering" && (
        <Progress value={clip.progress * 100} />
      )}
      {clip.status === "error" && clip.error_message && (
        <div className="text-xs text-destructive">{clip.error_message}</div>
      )}
    </div>
  );
}

type BadgeVariant = "outline" | "success" | "default" | "destructive";

function ClipStatusBadge({ status }: { status: ClipDTO["status"] }) {
  const map: Record<ClipDTO["status"], { label: string; variant: BadgeVariant }> = {
    pending: { label: "candidato", variant: "outline" },
    rendering: { label: "renderizando", variant: "default" },
    ready: { label: "pronto", variant: "success" },
    error: { label: "erro", variant: "destructive" },
  };
  const cfg = map[status];
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}
