import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { collections } from "./research";
export type LocalHadith = {
  hadithnumber: number;
  text: string;
  grades?: { name?: string; grade?: string }[];
  reference?: { book?: number; hadith?: number };
};
const cache = new Map<string, Promise<LocalHadith[]>>();
export function readCollection(name: string) {
  if (!Object.hasOwn(collections, name)) return Promise.resolve([]);
  if (!cache.has(name))
    cache.set(
      name,
      readFile(
        path.join(
          process.env.HADITH_DATA_DIR ||
            path.resolve(
              /* turbopackIgnore: true */ process.cwd(),
              ".corpus",
            ),
          `ara-${name}.json`,
        ),
        "utf8",
      )
        .then((s) => (JSON.parse(s) as { hadiths: LocalHadith[] }).hadiths)
        .catch((error) => {
          cache.delete(name);
          throw error;
        }),
    );
  return cache.get(name)!;
}
