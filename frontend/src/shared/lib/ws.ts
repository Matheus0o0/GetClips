export type JobEvent = {
  type: string;
  job_id: string;
  timestamp: string;
  stage?: string;
  progress?: number;
  message?: string;
  outputs?: Record<string, string>;
  error?: string;
};

export function openJobSocket(
  jobId: string,
  onMessage: (event: JobEvent) => void,
  onError?: (err: Event) => void,
): () => void {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${window.location.host}/ws/jobs/${jobId}`;
  const ws = new WebSocket(url);

  ws.onmessage = (ev) => {
    try {
      onMessage(JSON.parse(ev.data));
    } catch (e) {
      console.warn("Malformed WS payload", e);
    }
  };
  ws.onerror = (e) => onError?.(e);

  return () => {
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close();
    }
  };
}
