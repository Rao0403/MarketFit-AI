import fs from "node:fs/promises";
import path from "node:path";

export type ProjectRecommendation = {
  title: string;
  why_valuable: string;
  skills_covered: string[];
  evidence_from_jds: string[];
  difficulty_level: string;
  portfolio_impact: string;
  roadmap: string[];
  target_roles?: string[];
};

export type RecommendationsPayload = {
  generated_at: string;
  project_count: number;
  available_roles?: string[];
  project_source?: string;
  projects: ProjectRecommendation[];
  ollama_raw_response?: string;
};

export async function getLatestRecommendations(): Promise<RecommendationsPayload | null> {
  const outputDir = path.resolve(process.cwd(), "..", "outputs", "project_recommendations");
  let files: string[] = [];

  try {
    files = await fs.readdir(outputDir);
  } catch {
    return null;
  }

  const jsonFiles = files
    .filter((name) => name.endsWith(".json"))
    .sort((a, b) => b.localeCompare(a));

  if (jsonFiles.length === 0) {
    return null;
  }

  const latestPath = path.join(outputDir, jsonFiles[0]);
  const content = await fs.readFile(latestPath, "utf-8");
  const parsed = JSON.parse(content) as RecommendationsPayload;

  const availableRoles = new Set<string>(parsed.available_roles ?? []);
  for (const project of parsed.projects ?? []) {
    for (const role of project.target_roles ?? []) {
      availableRoles.add(role);
    }
  }

  return {
    ...parsed,
    available_roles: [...availableRoles],
  };
}
