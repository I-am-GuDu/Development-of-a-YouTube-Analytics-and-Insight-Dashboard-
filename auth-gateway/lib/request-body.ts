// Bound chunked bodies too; Content-Length alone is not a size limit.
export async function readJsonBody(request: Request): Promise<{body?: Record<string, unknown>; status?: number}> {
  if (!request.headers.get("content-type")?.startsWith("application/json")) return {status: 415};
  if (!request.body) return {status: 400};
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 8192) {await reader.cancel(); return {status: 413};}
      chunks.push(value);
    }
    const parsed: unknown = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? {body: parsed as Record<string, unknown>} : {status: 400};
  } catch {return {status: 400};}
  finally {reader.releaseLock();}
}
