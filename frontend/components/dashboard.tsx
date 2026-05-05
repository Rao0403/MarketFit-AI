"use client";

import { useMemo, useState } from "react";

import type { ProjectRecommendation, RecommendationsPayload } from "@/lib/recommendations";

type DashboardProps = {
  payload: RecommendationsPayload;
};

function byRole(projects: ProjectRecommendation[], role: string) {
  if (role === "All") {
    return projects;
  }
  return projects.filter((project) =>
    (project.target_roles ?? []).some((r) => r.toLowerCase() === role.toLowerCase()),
  );
}

export function Dashboard({ payload }: DashboardProps) {
  const roles = useMemo(() => ["All", ...(payload.available_roles ?? [])], [payload.available_roles]);
  const [activeRole, setActiveRole] = useState<string>(roles[0] ?? "All");

  const visibleProjects = useMemo(
    () => byRole(payload.projects ?? [], activeRole),
    [payload.projects, activeRole],
  );

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">MarketFit-AI</p>
        <h1>Project Recommendations Dashboard</h1>
        <p>
          Generated: {new Date(payload.generated_at).toLocaleString()} | Source: {payload.project_source ?? "unknown"}
        </p>
      </section>

      <section className="toolbar">
        {roles.map((role) => (
          <button
            key={role}
            type="button"
            className={role === activeRole ? "chip chip-active" : "chip"}
            onClick={() => setActiveRole(role)}
          >
            {role}
          </button>
        ))}
      </section>

      <section className="stats-grid">
        <article className="stat-card">
          <h3>Total Projects</h3>
          <p>{payload.projects.length}</p>
        </article>
        <article className="stat-card">
          <h3>Visible Projects</h3>
          <p>{visibleProjects.length}</p>
        </article>
        <article className="stat-card">
          <h3>Tracked Roles</h3>
          <p>{(payload.available_roles ?? []).length}</p>
        </article>
      </section>

      <section className="project-grid">
        {visibleProjects.map((project) => (
          <article className="project-card" key={project.title}>
            <div className="card-top">
              <h2>{project.title}</h2>
              <span className="badge">{project.difficulty_level}</span>
            </div>
            <p className="why">{project.why_valuable}</p>

            <div className="roles">
              {(project.target_roles ?? []).map((role) => (
                <span key={role} className="role-pill">{role}</span>
              ))}
            </div>

            <h4>Skills Covered</h4>
            <p>{(project.skills_covered ?? []).join(", ")}</p>

            <h4>Portfolio Impact</h4>
            <p>{project.portfolio_impact}</p>

            <h4>Evidence From JDs</h4>
            <ul>
              {(project.evidence_from_jds ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <h4>Roadmap</h4>
            <ol>
              {(project.roadmap ?? []).map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </article>
        ))}
      </section>
    </main>
  );
}
