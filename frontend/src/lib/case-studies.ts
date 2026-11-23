import studies from "@/content/case-studies.json";

type Citation = { label: string; url: string };
// Coordinates are percentages of the source page, measured from the top left.
export type EvidenceHighlight = { left: number; top: number; width: number; height: number };

type Evidence = {
  id: number;
  title: string;
  explanation: string;
  page?: number;
  highlights?: EvidenceHighlight[];
};
type Passage = {
  source: string;
  status: string;
  chain: string;
  text: string;
  corpus?: { collection: string; number: number };
  citation?: Citation;
};
export type Study = {
  finding: string;
  passages?: Passage[];
  sections: {
    title: string;
    paragraphs: string[];
    evidence?: Evidence[];
    citations?: Citation[];
  }[];
};

export const caseStudies: Record<string, Study> = studies;

