import { useMemo, useState } from "react";
import { Check, Copy, Loader2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { useTranscription } from "@/features/jobs/api/hooks";

const LANG_LABEL: Record<string, string> = {
  pt: "Português",
  en: "Inglês",
  es: "Espanhol",
  fr: "Francês",
  de: "Alemão",
  it: "Italiano",
  ja: "Japonês",
  zh: "Chinês",
  ru: "Russo",
};

export function TranscriptionViewer({
  jobId,
  enabled,
}: {
  jobId: string;
  enabled: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const { data, isLoading, error } = useTranscription(jobId, enabled);

  const text = data?.full_text ?? "";
  const wordCount = useMemo(() => (text ? text.split(/\s+/).length : 0), [text]);

  async function copy() {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // fallback: seleciona
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  if (!enabled) return null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div className="space-y-1">
          <CardTitle>Transcrição</CardTitle>
          {data && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">
                {LANG_LABEL[data.language_detected] ?? data.language_detected}
                {" · "}
                {Math.round(data.language_probability * 100)}%
              </Badge>
              <span>{data.segments.length} segmentos</span>
              <span>· {wordCount} palavras</span>
            </div>
          )}
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={copy}
          disabled={!text}
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          {copied ? "Copiado" : "Copiar texto"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Carregando…
          </div>
        )}
        {error && (
          <div className="text-sm text-destructive">
            {(error as Error).message}
          </div>
        )}
        {data && (
          <div className="rounded-md border bg-background p-4 max-h-[480px] overflow-auto">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{text}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
