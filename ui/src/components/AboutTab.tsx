export default function AboutTab() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-10 sm:mb-12">
        <h1 className="text-3xl sm:text-4xl font-bold mb-4">
          About <span className="text-gradient">AgentCheck</span>
        </h1>
        <p className="text-slate-500 text-lg max-w-2xl mx-auto">
          AI-powered certificate verification system that automates the RegTech
          compliance workflow using a multi-agent architecture with full audit
          trails.
        </p>
      </div>

      {/* Architecture Section */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6">
          Multi-Agent Architecture
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <AgentCard
            title="Orchestrator"
            description="Coordinates the workflow: Extraction → Email → Decision → Report"
            color="blue"
          />
          <AgentCard
            title="Extraction Agent"
            description="Parses PDFs via LLM Vision and extracts structured certificate fields"
            color="purple"
          />
          <AgentCard
            title="Email Agent"
            description="Drafts verification emails and handles university communications"
            color="pink"
          />
          <AgentCard
            title="Decision Agent"
            description="Uses Function Calling to analyze replies and make compliance decisions"
            color="blue"
          />
        </div>
      </section>

      {/* Workflow Section */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6">
          Verification Workflow
        </h2>
        <div className="glass-card rounded-xl p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 text-sm">
            {[
              "PDF Upload",
              "LLM Vision Extract",
              "Identify University",
              "Draft Email",
              "Read Reply",
              "Analyze & Decide",
              "Generate Report",
            ].map((step, index, arr) => (
              <div key={step} className="flex items-center gap-2 sm:gap-3">
                <span className="px-3 py-1.5 glass-light rounded-lg text-slate-600 whitespace-nowrap">
                  {step}
                </span>
                {index < arr.length - 1 && (
                  <span className="text-slate-400 hidden sm:block">→</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6">Technology Stack</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <TechItem label="Backend" value="Python, FastAPI" />
          <TechItem label="AI/LLM" value="Groq LLM with Function Calling" />
          <TechItem label="Frontend" value="React, TypeScript, Tailwind CSS" />
          <TechItem label="PDF Processing" value="LLM Vision API" />
        </div>
      </section>

      {/* Compliance Features */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6">
          Compliance Features
        </h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            "Complete audit trail of all actions",
            "Explainable AI decisions",
            "Human-readable reports",
            "JSON export for integration",
          ].map((text, index) => (
            <div key={index} className="glass-light rounded-lg p-3">
              <span className="text-slate-600 text-sm">{text}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Limitations */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6">Demo Limitations</h2>
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 sm:p-5">
          <ul className="space-y-2">
            {[
              "University replies are simulated (demo mode)",
              "Limited university database",
              "No real email integration",
            ].map((item, index) => (
              <li key={index} className="text-amber-700 text-sm">
                • {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Footer */}
      <div className="text-center pt-6 border-t border-slate-300/30">
        <p className="text-slate-500 text-sm">
          Built for RegTech compliance automation
        </p>
      </div>
    </div>
  );
}

interface AgentCardProps {
  title: string;
  description: string;
  color: "blue" | "purple" | "pink";
}

function AgentCard({ title, description, color }: AgentCardProps) {
  const colorClasses = {
    blue: "from-blue-500/20 to-blue-900/10 border-blue-500/30",
    purple: "from-purple-500/20 to-purple-900/10 border-purple-500/30",
    pink: "from-pink-500/20 to-pink-900/10 border-pink-500/30",
  };

  return (
    <div
      className={`glass-card rounded-xl p-5 bg-gradient-to-br ${colorClasses[color]} hover-lift`}
    >
      <h3 className="font-semibold text-slate-800 mb-1">{title}</h3>
      <p className="text-slate-500 text-sm">{description}</p>
    </div>
  );
}

interface TechItemProps {
  label: string;
  value: string;
}

function TechItem({ label, value }: TechItemProps) {
  return (
    <div className="glass-light rounded-lg p-4 flex items-center gap-3">
      <span className="text-slate-400 text-sm min-w-[80px]">{label}:</span>
      <span className="text-slate-800 font-medium text-sm">{value}</span>
    </div>
  );
}
