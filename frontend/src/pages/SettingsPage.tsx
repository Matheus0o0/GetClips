import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { api } from "@/shared/lib/api";
import { Badge } from "@/shared/ui/badge";

export function SettingsPage() {
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.settings(),
  });
  const { data: models } = useQuery({
    queryKey: ["models"],
    queryFn: () => api.models(),
  });

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Configurações</h1>
        <p className="text-muted-foreground mt-1">
          Somente leitura por enquanto — edite em <code>backend/.env</code>.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Ambiente</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 text-sm">
          {settings ? (
            <>
              <Info label="Modelo padrão" value={settings.default_model} />
              <Info label="Idioma padrão" value={settings.default_language} />
              <Info label="Device" value={settings.device} />
              <Info label="Jobs concorrentes" value={String(settings.max_concurrent_jobs)} />
              <Info label="Beam size" value={String(settings.beam_size)} />
              <Info label="Armazenamento" value={settings.storage_root} />
            </>
          ) : (
            <div className="text-muted-foreground col-span-2">Carregando...</div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Cortes verticais (IA {settings?.highlight_provider === "ollama" ? "local" : "externa"})</CardTitle>
            {settings && (
              settings.highlight_configured ? (
                <Badge variant="success">Ativo</Badge>
              ) : (
                <Badge variant="warning">Não configurado</Badge>
              )
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="rounded-md border border-amber-500/40 bg-amber-500/5 p-3 flex gap-2">
            <ShieldAlert className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-muted-foreground">
              {settings?.highlight_provider === "ollama"
                ? <>Seleção de cortes via <b>Ollama local</b> — nada sai da sua máquina. Vídeo, áudio, transcrição e render acontecem <b>100% offline</b>.</>
                : <>Apenas o <b>texto</b> da transcrição é enviado ao provedor externo (OpenAI/Anthropic). Vídeo, áudio e render acontecem <b>100% no seu computador</b>.</>
              }
            </p>
          </div>
          {settings && (
            <div className="grid grid-cols-2 gap-4">
              <Info label="Provedor" value={settings.highlight_provider} />
              <Info
                label="Chave de API"
                value={settings.highlight_configured ? "definida" : "ausente"}
              />
              <Info label="Máx. cortes" value={String(settings.highlight_max_clips)} />
              <Info
                label="Duração alvo"
                value={`${settings.highlight_clip_duration_min}–${settings.highlight_clip_duration_max}s`}
              />
              <Info
                label="Resolução do corte"
                value={settings.reframe_output_resolution}
              />
            </div>
          )}
          {settings && !settings.highlight_configured && (
            <div className="text-xs text-muted-foreground flex items-start gap-2">
              <AlertCircle className="h-3.5 w-3.5 mt-0.5" />
              <span>
                {settings.highlight_provider === "ollama"
                  ? <>Inicie o Ollama (<code>ollama serve</code>) e baixe o modelo (<code>ollama pull llama3.2</code>).</>
                  : <>Defina <code>{settings.highlight_provider === "anthropic" ? "ANTHROPIC_API_KEY" : "OPENAI_API_KEY"}</code> em <code>backend/.env</code> e reinicie o backend.</>
                }
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Modelos disponíveis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {models?.map((m) => (
            <div
              key={m.name}
              className="flex items-center justify-between p-3 rounded-md border"
            >
              <span className="font-mono text-sm">{m.name}</span>
              {m.downloaded ? (
                <Badge variant="success">Baixado</Badge>
              ) : (
                <Badge variant="outline">Não baixado</Badge>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-foreground mt-0.5">{value}</div>
    </div>
  );
}
