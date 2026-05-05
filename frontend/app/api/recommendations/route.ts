import { NextRequest, NextResponse } from "next/server";

import { getLatestRecommendations } from "@/lib/recommendations";

export async function GET(request: NextRequest) {
  const payload = await getLatestRecommendations();
  if (!payload) {
    return NextResponse.json({ error: "No recommendation outputs found." }, { status: 404 });
  }

  const requestedRole = request.nextUrl.searchParams.get("role");
  if (!requestedRole) {
    return NextResponse.json(payload);
  }

  const filtered = payload.projects.filter((project) =>
    (project.target_roles ?? []).some(
      (role) => role.toLowerCase() === requestedRole.toLowerCase(),
    ),
  );

  return NextResponse.json({
    ...payload,
    project_count: filtered.length,
    projects: filtered,
  });
}
