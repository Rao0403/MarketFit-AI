import { Dashboard } from "@/components/dashboard";
import { getLatestRecommendations } from "@/lib/recommendations";

export default async function Page() {
  const payload = await getLatestRecommendations();

  if (!payload) {
    return (
      <main className="page-shell">
        <section className="hero">
          <p className="eyebrow">MarketFit-AI</p>
          <h1>Project Recommendations Dashboard</h1>
          <p>No recommendation output found in outputs/project_recommendations.</p>
        </section>
      </main>
    );
  }

  return <Dashboard payload={payload} />;
}
