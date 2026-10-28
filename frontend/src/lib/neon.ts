import "server-only";
import { neon } from "@neondatabase/serverless";

export function usesNeon() {
  return Boolean(process.env.RESEARCH_READ_DATABASE_URL);
}

const state = globalThis as typeof globalThis & { othmaniPublicQueries?: Map<string, Promise<unknown[]>> };
const pending = state.othmaniPublicQueries ||= new Map<string, Promise<unknown[]>>();
export async function queryNeon<T>(text: string, values: unknown[] = []): Promise<T[]> {
  const url = process.env.RESEARCH_READ_DATABASE_URL;
  if (!url) throw new Error("Research database is not configured");
  const key = JSON.stringify([text, values]);
  const existing = pending.get(key);
  if (existing) return await existing as T[];
  // Share identical in-flight public reads during cache refreshes, rather than
  // launching the same large view query for every concurrent page request.
  const request = (async () => {
    const sql = neon(url, { fetchOptions: { signal: AbortSignal.timeout(20000), cache: "no-store" } });
    const [, rows] = await sql.transaction([
      sql.query("SELECT set_config('jit','off',true),set_config('enable_memoize','off',true)"),
      sql.query(text, values),
    ], { readOnly: true });
    return rows as unknown[];
  })().finally(() => pending.delete(key));
  pending.set(key, request);
  return await request as T[];
}
