"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL, runDiagnostics, type SystemDiagnostics, type DiagnosticResult } from "../lib/api";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";

export default function Diagnostics() {
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [running, setRunning] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const runTests = async () => {
    setRunning(true);
    setError(null);
    try {
      const results = await runDiagnostics();
      setDiagnostics(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    runTests();
  }, []);

  const getStatusColor = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800 border-green-300';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'error': return 'bg-red-100 text-red-800 border-red-300';
    }
  };

  const getStatusIcon = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success': return '✓';
      case 'warning': return '⚠';
      case 'error': return '✗';
    }
  };

  const getOverallBadge = (overall: SystemDiagnostics['overall']) => {
    switch (overall) {
      case 'healthy':
        return <Badge className="bg-green-500">Healthy</Badge>;
      case 'degraded':
        return <Badge className="bg-yellow-500">Degraded</Badge>;
      case 'down':
        return <Badge className="bg-red-500">Down</Badge>;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>System Diagnostics</CardTitle>
            <CardDescription>
              API Base URL: <code className="text-xs bg-gray-100 px-2 py-1 rounded">{API_BASE_URL}</code>
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {diagnostics && getOverallBadge(diagnostics.overall)}
            <Button
              onClick={runTests}
              disabled={running}
              size="sm"
              variant="outline"
            >
              {running ? "Running..." : "Retest"}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            Error: {error}
          </div>
        )}

        {running && !diagnostics && (
          <div className="text-center py-8 text-gray-500">
            <div className="animate-pulse">Running diagnostics...</div>
          </div>
        )}

        {diagnostics && (
          <div className="space-y-3">
            {diagnostics.checks.map((check, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-md border ${getStatusColor(check.status)}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">
                      {getStatusIcon(check.status)}
                    </span>
                    <span className="font-medium">{check.name}</span>
                  </div>
                  <span className="text-xs uppercase font-semibold">
                    {check.status}
                  </span>
                </div>
                <div className="text-sm mb-2">
                  {check.message}
                </div>
                {check.details && Object.keys(check.details).length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs font-medium cursor-pointer hover:underline">
                      View Details
                    </summary>
                    <pre className="mt-2 text-xs bg-white/50 p-2 rounded overflow-auto max-h-40">
                      {JSON.stringify(check.details, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}

            <div className="mt-4 pt-3 border-t text-xs text-gray-500">
              Last checked: {new Date(diagnostics.timestamp).toLocaleString()}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
