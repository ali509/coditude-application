export const dynamic = "force-dynamic";

type BackendMessage = {
  message: string;
  environment: string;
  source: string;
};

async function getBackendMessage(): Promise<BackendMessage> {
  const backendUrl =
    process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

  try {
    const response = await fetch(`${backendUrl}/api/v1/message`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    return (await response.json()) as BackendMessage;
  } catch {
    return {
      message: "Backend is currently unavailable",
      environment: "unknown",
      source: "unavailable",
    };
  }
}

export default async function Home() {
  const backend = await getBackendMessage();

  return (
    <main>
      <section className="panel">
        <p className="eyebrow">Coditude DevOps Assessment</p>
        <h1>Application Status</h1>

        <dl>
          <div>
            <dt>Frontend</dt>
            <dd className="healthy">Healthy</dd>
          </div>
          <div>
            <dt>Backend</dt>
            <dd>{backend.message}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{backend.environment}</dd>
          </div>
          <div>
            <dt>Data Source</dt>
            <dd>{backend.source}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
