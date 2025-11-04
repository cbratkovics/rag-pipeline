"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "../lib/api";

type Check = { label: string; ok: boolean; detail?: string };

export default function Diagnostics() {
  const [checks, setChecks] = useState<Check[]>([]);
  const [running, setRunning] = useState(true);

  useEffect(() => {
    (async () => {
      const results: Check[] = [];
      try {
        await fetch(`${API_BASE_URL}/api/health`, {
          method: "OPTIONS",
          mode: "cors",
        });
        results.push({ label: "CORS preflight", ok: true });
      } catch (e: any) {
        results.push({ label: "CORS preflight", ok: false, detail: String(e) });
      }
      try {
        // Try the actual health endpoint
        const r = await fetch(`${API_BASE_URL}/healthz`, {
          mode: "cors",
          headers: {
            'Accept': 'application/json',
          }
        });
        results.push({
          label: "API health",
          ok: r.ok,
          detail: r.ok ? "Connected" : `HTTP ${r.status}`,
        });
      } catch (e: any) {
        results.push({ label: "API health", ok: false, detail: String(e) });
      }
      setChecks(results);
      setRunning(false);
    })();
  }, []);

  return (
    <div className="rounded-md border p-4 bg-white/60">
      <div className="mb-2 font-medium">Connectivity Diagnostics</div>
      <div className="text-xs text-gray-500 mb-3">
        BASE_URL: <code>{API_BASE_URL}</code>
      </div>
      <ul className="space-y-1">
        {checks.map((c) => (
          <li key={c.label} className="flex items-center justify-between">
            <span>{c.label}</span>
            <span className={c.ok ? "text-green-600" : "text-red-600"}>
              {c.ok ? "OK" : "FAIL"}
              {!c.ok && c.detail ? ` — ${c.detail}` : ""}
            </span>
          </li>
        ))}
      </ul>
      {running && <div className="mt-2 text-xs text-gray-500">Running…</div>}
    </div>
  );
}
