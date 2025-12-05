import {
  Search,
  Cpu,
  Mail,
  Brain,
  CheckCircle,
  AlertTriangle,
  Shield,
  ArrowRight,
} from "lucide-react";

export default function AboutTab() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-10 sm:mb-12">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto mb-6 glow-md shadow-lg">
          <Search className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-4">
          About <span className="text-gradient">AgentCheck</span>
        </h1>
        <p className="text-slate-500 text-lg max-w-2xl mx-auto">
          AI-powered certificate verification system that automates the
          compliance workflow for credential verification.
        </p>
      </div>

      {/* Architecture Section */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center gap-3">
          <span className="text-xl sm:text-2xl">🔧</span>
          Multi-Agent Architecture
        </h2>
        <div className="grid sm:grid-cols-3 gap-4">
          <AgentCard
            icon={<Cpu className="w-6 h-6" />}
            title="Extraction Agent"
            description="Parses PDFs and extracts certificate information"
            color="blue"
          />
          <AgentCard
            icon={<Mail className="w-6 h-6" />}
            title="Email Agent"
            description="Handles verification communications"
            color="purple"
          />
          <AgentCard
            icon={<Brain className="w-6 h-6" />}
            title="Decision Agent"
            description="Analyzes replies and makes compliance decisions"
            color="pink"
          />
        </div>
      </section>

      {/* Workflow Section */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center gap-3">
          <span className="text-xl sm:text-2xl">📊</span>
          Verification Workflow
        </h2>
        <div className="glass-card rounded-xl p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 text-sm">
            {[
              "PDF Upload",
              "Extract Fields",
              "Identify University",
              "Draft Email",
              "Simulate Reply",
              "AI Analysis",
              "Compliance Decision",
            ].map((step, index, arr) => (
              <div key={step} className="flex items-center gap-2 sm:gap-3">
                <span className="px-3 py-1.5 glass-light rounded-lg text-slate-600 whitespace-nowrap">
                  {step}
                </span>
                {index < arr.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-slate-500 hidden sm:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center gap-3">
          <span className="text-xl sm:text-2xl">🛠️</span>
          Technology Stack
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <TechItem label="Backend" value="Python, FastAPI" />
          <TechItem label="AI/LLM" value="OpenAI GPT with function calling" />
          <TechItem label="Frontend" value="React, TypeScript, Tailwind CSS" />
          <TechItem label="PDF Processing" value="PyMuPDF + LLM Vision" />
        </div>
      </section>

      {/* Compliance Features */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center gap-3">
          <span className="text-xl sm:text-2xl">🔒</span>
          Compliance Features
        </h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            {
              icon: <CheckCircle className="w-4 h-4" />,
              text: "Complete audit trail of all actions",
            },
            {
              icon: <Brain className="w-4 h-4" />,
              text: "Explainable AI decisions",
            },
            {
              icon: <Shield className="w-4 h-4" />,
              text: "Human-readable reports",
            },
            {
              icon: <ArrowRight className="w-4 h-4" />,
              text: "JSON export for integration",
            },
          ].map((item, index) => (
            <div
              key={index}
              className="flex items-center gap-3 glass-light rounded-lg p-3"
            >
              <span className="text-emerald-400">{item.icon}</span>
              <span className="text-slate-600 text-sm">{item.text}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Limitations */}
      <section className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center gap-3">
          <span className="text-xl sm:text-2xl">⚠️</span>
          Demo Limitations
        </h2>
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 sm:p-5">
          <ul className="space-y-2">
            {[
              "University replies are simulated (demo mode)",
              "Limited university database",
              "No real email integration",
            ].map((item, index) => (
              <li
                key={index}
                className="flex items-start gap-3 text-amber-700 text-sm"
              >
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-500" />
                {item}
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
  icon: React.ReactNode;
  title: string;
  description: string;
  color: "blue" | "purple" | "pink";
}

function AgentCard({ icon, title, description, color }: AgentCardProps) {
  const colorClasses = {
    blue: "from-blue-500/20 to-blue-900/10 border-blue-500/30 text-blue-400",
    purple:
      "from-purple-500/20 to-purple-900/10 border-purple-500/30 text-purple-400",
    pink: "from-pink-500/20 to-pink-900/10 border-pink-500/30 text-pink-400",
  };

  return (
    <div
      className={`glass-card rounded-xl p-5 bg-gradient-to-br ${colorClasses[color]} hover-lift`}
    >
      <div className="mb-3">{icon}</div>
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
