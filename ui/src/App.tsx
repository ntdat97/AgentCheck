import { useState, useEffect } from "react";
import {
  Search,
  FileText,
  Info,
  Settings,
  Menu,
  X,
  ChevronDown,
  Activity,
} from "lucide-react";
import { api } from "./services/api";
import { ReportSummary, Stats, SimulationScenario } from "./types";
import VerifyTab from "./components/VerifyTab";
import ReportsTab from "./components/ReportsTab";
import AboutTab from "./components/AboutTab";

type TabType = "verify" | "reports" | "about";

function App() {
  const [activeTab, setActiveTab] = useState<TabType>("verify");
  const [scenario, setScenario] = useState<SimulationScenario>("verified");
  const [stats, setStats] = useState<Stats>({
    total: 0,
    compliant: 0,
    not_compliant: 0,
    inconclusive: 0,
  });
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [activeTab]);

  const loadReports = async () => {
    try {
      const data = await api.listReports(100);
      setReports(data);

      const newStats: Stats = {
        total: data.length,
        compliant: data.filter((r) => r.compliance_result === "COMPLIANT")
          .length,
        not_compliant: data.filter(
          (r) => r.compliance_result === "NOT_COMPLIANT"
        ).length,
        inconclusive: data.filter((r) => r.compliance_result === "INCONCLUSIVE")
          .length,
      };
      setStats(newStats);
    } catch (error) {
      console.error("Failed to load reports:", error);
    }
  };

  const handleVerificationComplete = () => {
    loadReports();
  };

  return (
    <div className="min-h-screen text-slate-800">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass border-b border-slate-300/50">
        <div className="flex items-center justify-between px-3 py-2">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-slate-200/50 transition-colors"
            aria-label="Toggle menu"
          >
            {sidebarOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>

          {/* Mobile Tab Navigation */}
          <nav className="flex gap-1">
            <MobileTabButton
              active={activeTab === "verify"}
              onClick={() => setActiveTab("verify")}
              icon={<FileText className="w-4 h-4" />}
              label="Verify"
            />
            <MobileTabButton
              active={activeTab === "reports"}
              onClick={() => setActiveTab("reports")}
              icon={<Search className="w-4 h-4" />}
              label="Reports"
            />
            <MobileTabButton
              active={activeTab === "about"}
              onClick={() => setActiveTab("about")}
              icon={<Info className="w-4 h-4" />}
              label="About"
            />
          </nav>

          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-slate-200/50 transition-colors opacity-0 pointer-events-none"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40 overlay-enter"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside
          className={`
            fixed lg:sticky top-0 left-0 z-40
            w-72 lg:w-80 h-screen
            glass-card overflow-y-auto
            transform transition-transform duration-300 ease-out
            ${
              sidebarOpen
                ? "translate-x-0"
                : "-translate-x-full lg:translate-x-0"
            }
            lg:border-r border-slate-300/30
          `}
        >
          <div className="p-6">
            {/* Logo */}
            <div className="mb-8 hidden lg:block">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center glow-sm shadow-md">
                  <Search className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gradient">
                    AgentCheck
                  </h1>
                  <p className="text-xs text-slate-500">
                    AI-Powered Verification
                  </p>
                </div>
              </div>
            </div>

            {/* Settings Section */}
            <div className="mb-8 mt-16 lg:mt-0">
              <div className="flex items-center gap-2 mb-4">
                <Settings className="w-4 h-4 text-slate-500" />
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                  Settings
                </h2>
              </div>

              <div className="glass-light rounded-xl p-4">
                <label className="block text-sm text-slate-600 mb-2 font-medium">
                  Simulation Mode
                </label>
                <div className="relative">
                  <select
                    value={scenario}
                    onChange={(e) =>
                      setScenario(e.target.value as SimulationScenario)
                    }
                    className="w-full bg-white border border-slate-300 rounded-lg px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 appearance-none cursor-pointer transition-all"
                  >
                    <option value="verified">✓ Verified</option>
                    <option value="not_verified">✗ Not Verified</option>
                    <option value="inconclusive">? Inconclusive</option>
                    <option value="suspicious">
                      ⚠ Suspicious (Fraud Test)
                    </option>
                    <option value="ambiguous">🔍 Ambiguous (Multi-step)</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Choose simulated university response
                </p>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-slate-500" />
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                  Quick Stats
                </h2>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Total" value={stats.total} />
                <StatCard
                  label="Compliant"
                  value={stats.compliant}
                  color="green"
                />
                <StatCard
                  label="Not Compliant"
                  value={stats.not_compliant}
                  color="red"
                />
                <StatCard
                  label="Inconclusive"
                  value={stats.inconclusive}
                  color="yellow"
                />
              </div>
            </div>

            {/* Workflow Guide */}
            <div className="glass-light rounded-xl p-4">
              <h3 className="text-sm font-semibold text-blue-400 mb-3 flex items-center gap-2">
                <span className="text-base">💡</span>
                How it works
              </h3>
              <ol className="text-xs text-slate-500 space-y-2">
                {[
                  "Upload a certificate PDF",
                  "AI extracts key information",
                  "System drafts verification email",
                  "University reply is simulated",
                  "AI analyzes and decides compliance",
                ].map((step, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-[10px] font-medium">
                      {index + 1}
                    </span>
                    <span className="pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-h-screen lg:ml-0 pt-14 lg:pt-0">
          {/* Desktop Header with Tabs - Hidden on mobile */}
          <header className="hidden lg:block sticky top-0 z-30 glass border-b border-slate-300/30">
            <div className="px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-center h-16">
                <nav className="flex gap-2">
                  <TabButton
                    active={activeTab === "verify"}
                    onClick={() => setActiveTab("verify")}
                    icon={<FileText className="w-4 h-4" />}
                    label="Verify"
                    fullLabel="Verify Certificate"
                  />
                  <TabButton
                    active={activeTab === "reports"}
                    onClick={() => setActiveTab("reports")}
                    icon={<Search className="w-4 h-4" />}
                    label="Reports"
                    fullLabel="View Reports"
                  />
                  <TabButton
                    active={activeTab === "about"}
                    onClick={() => setActiveTab("about")}
                    icon={<Info className="w-4 h-4" />}
                    label="About"
                    fullLabel="About"
                  />
                </nav>
              </div>
            </div>
          </header>

          {/* Tab Content */}
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="animate-fade-in">
              {activeTab === "verify" && (
                <VerifyTab
                  scenario={scenario}
                  onVerificationComplete={handleVerificationComplete}
                />
              )}
              {activeTab === "reports" && (
                <ReportsTab reports={reports} onRefresh={loadReports} />
              )}
              {activeTab === "about" && <AboutTab />}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  color?: "green" | "red" | "yellow";
}

function StatCard({ label, value, color }: StatCardProps) {
  const colorClasses = {
    green: "text-emerald-400",
    red: "text-rose-400",
    yellow: "text-amber-400",
  };

  const bgClasses = {
    green: "from-emerald-500/10 to-transparent",
    red: "from-rose-500/10 to-transparent",
    yellow: "from-amber-500/10 to-transparent",
  };

  return (
    <div
      className={`glass-light rounded-xl p-3 bg-gradient-to-br ${
        color ? bgClasses[color] : "from-slate-500/10"
      }`}
    >
      <div
        className={`text-2xl font-bold ${
          color ? colorClasses[color] : "text-slate-800"
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  fullLabel: string;
}

function TabButton({
  active,
  onClick,
  icon,
  label,
  fullLabel,
}: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg font-medium transition-all duration-200
        ${
          active
            ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/20"
            : "text-slate-500 hover:text-slate-800 hover:bg-slate-200/50"
        }
      `}
    >
      {icon}
      <span className="hidden sm:inline">{fullLabel}</span>
      <span className="sm:hidden">{label}</span>
    </button>
  );
}

interface MobileTabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

function MobileTabButton({
  active,
  onClick,
  icon,
  label,
}: MobileTabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200
        ${
          active
            ? "bg-blue-600 text-white"
            : "text-slate-500 hover:text-slate-800"
        }
      `}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

export default App;
