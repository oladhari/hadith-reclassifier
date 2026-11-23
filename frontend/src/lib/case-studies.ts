import studies from "@/content/case-studies.json";

type Citation = { label: string; url: string };
type Evidence = {
  id: number;
  title: string;
  explanation: string;
  page?: number;
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

