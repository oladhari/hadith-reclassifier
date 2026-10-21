import "server-only";
import { neon } from "@neondatabase/serverless";

export function usesNeon() {
  return Boolean(process.env.RESEARCH_READ_DATABASE_URL);
}

export async function queryNeon<T>(text: string, values: unknown[] = []): Promise<T[]> {
  const url = process.env.RESEARCH_READ_DATABASE_URL;
  if (!url) throw new Error("Research database is not configured");
  const sql = neon(url, { fetchOptions: { signal: AbortSignal.timeout(20000), cache: "no-store" } });
  return await sql.query(text, values) as T[];
}
