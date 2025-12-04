import { useState } from "react";
import {
  Download,
  ChevronDown,
  ChevronRight,
  User,
  GraduationCap,
  Building2,
  Calendar,
  Mail,
  MessageSquare,
  Brain,
  ClipboardList,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { ComplianceReport } from "../types";

interface ResultsDisplayProps {
  report: ComplianceReport;
  compact?: boolean;
}

export default function ResultsDisplay({
  report,
  compact = false,
}: ResultsDisplayProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(compact ? [] : ["details", "decision"])
  );

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report_${report.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <MetricCard
          label="Result"
          value={report.compliance_result}
          color={
            report.compliance_result === "COMPLIANT"
              ? "green"
              : report.compliance_result === "NOT_COMPLIANT"
              ? "red"
              : "yellow"
          }
        />
        <MetricCard
          label="Confidence"
          value={
            report.reply_analysis
              ? `${Math.round(report.reply_analysis.confidence_score * 100)}%`
              : "N/A"
          }
        />
        <MetricCard
          label="Processing Time"
          value={
            report.processing_time_seconds
              ? `${report.processing_time_seconds.toFixed(2)}s`
              : "N/A"
          }
        />
        <MetricCard
          label="Audit Steps"
          value={report.audit_log.length.toString()}
        />
      </div>

      {/* Certificate Details */}
      <CollapsibleSection
        title="Certificate Details"
        emoji="📜"
        icon={<GraduationCap className="w-5 h-5" />}
        expanded={expandedSections.has("details")}
        onToggle={() => toggleSection("details")}
      >
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-slate-300 mb-3 text-sm uppercase tracking-wider">
              Extracted Information
            </h4>
            <div className="space-y-3">
              <InfoRow
                icon={<User className="w-4 h-4" />}
                label="Candidate"
                value={report.extracted_fields.candidate_name}
              />
              <InfoRow
                icon={<Building2 className="w-4 h-4" />}
                label="University"
                value={report.extracted_fields.university_name}
              />
              <InfoRow
                icon={<GraduationCap className="w-4 h-4" />}
                label="Degree"
                value={report.extracted_fields.degree_name}
              />
              <InfoRow
                icon={<Calendar className="w-4 h-4" />}
                label="Issue Date"
                value={report.extracted_fields.issue_date}
              />
            </div>
          </div>

          {report.university_contact && (
            <div>
              <h4 className="font-semibold text-slate-300 mb-3 text-sm uppercase tracking-wider">
                University Contact
              </h4>
              <div className="space-y-3">
                <InfoRow
                  icon={<Building2 className="w-4 h-4" />}
                  label="Name"
                  value={report.university_contact.name}
                />
                <InfoRow
                  icon={<Mail className="w-4 h-4" />}
                  label="Email"
                  value={report.university_contact.email}
                />
                <InfoRow
                  icon={<User className="w-4 h-4" />}
                  label="Department"
                  value={report.university_contact.verification_department}
                />
              </div>
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* Decision Explanation */}
      <CollapsibleSection
        title="Decision Explanation"
        emoji="🧠"
        icon={<Brain className="w-5 h-5" />}
        expanded={expandedSections.has("decision")}
        onToggle={() => toggleSection("decision")}
      >
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
          <p className="text-slate-300 leading-relaxed">
            {report.decision_explanation}
          </p>
        </div>
      </CollapsibleSection>

      {/* Email Trail */}
      {(report.outgoing_email || report.incoming_email) && (
        <CollapsibleSection
          title="Email Trail"
          emoji="📧"
          icon={<Mail className="w-5 h-5" />}
          expanded={expandedSections.has("email")}
          onToggle={() => toggleSection("email")}
        >
          <div className="grid md:grid-cols-2 gap-4">
            {report.outgoing_email && (
              <div className="glass-light rounded-xl p-5">
                <h4 className="font-semibold text-blue-400 mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400" />
                  Outgoing Request
                </h4>
                <div className="mb-4 space-y-1">
                  <p className="text-sm text-slate-400">
                    To:{" "}
                    <span className="text-white font-medium">
                      {report.outgoing_email.recipient_email}
                    </span>
                  </p>
                  <p className="text-sm text-slate-400">
                    Subject:{" "}
                    <span className="text-white font-medium">
                      {report.outgoing_email.subject}
                    </span>
                  </p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/30">
                  <pre className="text-base text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">
                    {report.outgoing_email.body}
                  </pre>
                </div>
              </div>
            )}

            {report.incoming_email && (
              <div className="glass-light rounded-xl p-5">
                <h4 className="font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  University Reply
                </h4>
                <div className="mb-4 space-y-1">
                  <p className="text-sm text-slate-400">
                    From:{" "}
                    <span className="text-white font-medium">
                      {report.incoming_email.sender_email}
                    </span>
                  </p>
                  <p className="text-sm text-slate-400">
                    Subject:{" "}
                    <span className="text-white font-medium">
                      {report.incoming_email.subject}
                    </span>
                  </p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/30">
                  <pre className="text-base text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">
                    {report.incoming_email.body}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* AI Analysis */}
      {report.reply_analysis && (
        <CollapsibleSection
          title="AI Analysis"
          emoji="🤖"
          icon={<MessageSquare className="w-5 h-5" />}
          expanded={expandedSections.has("analysis")}
          onToggle={() => toggleSection("analysis")}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-light rounded-lg p-3">
                <span className="text-xs text-slate-500 uppercase tracking-wider">
                  Status
                </span>
                <p className="font-semibold text-white mt-1">
                  {report.reply_analysis.verification_status}
                </p>
              </div>
              <div className="glass-light rounded-lg p-3">
                <span className="text-xs text-slate-500 uppercase tracking-wider">
                  Confidence
                </span>
                <p className="font-semibold text-white mt-1">
                  {Math.round(report.reply_analysis.confidence_score * 100)}%
                </p>
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wider">
                Explanation
              </span>
              <p className="text-slate-300 mt-2 leading-relaxed">
                {report.reply_analysis.explanation}
              </p>
            </div>
            {report.reply_analysis.key_phrases.length > 0 && (
              <div>
                <span className="text-xs text-slate-500 uppercase tracking-wider">
                  Key Phrases
                </span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {report.reply_analysis.key_phrases.map((phrase, index) => (
                    <span
                      key={index}
                      className="px-3 py-1.5 bg-slate-700/50 rounded-lg text-xs text-slate-300 border border-slate-600/30"
                    >
                      {phrase}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* Audit Trail */}
      <CollapsibleSection
        title="Audit Trail"
        emoji="📋"
        icon={<ClipboardList className="w-5 h-5" />}
        expanded={expandedSections.has("audit")}
        onToggle={() => toggleSection("audit")}
      >
        <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
          {report.audit_log.map((entry, index) => (
            <div
              key={index}
              className="flex items-start gap-3 py-3 border-b border-slate-700/50 last:border-0"
            >
              <div className="flex-shrink-0 mt-0.5">
                {entry.success ? (
                  <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle className="w-3 h-3 text-emerald-400" />
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full bg-rose-500/20 flex items-center justify-center">
                    <XCircle className="w-3 h-3 text-rose-400" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white font-medium">{entry.step}</p>
                <p className="text-xs text-slate-400 mt-0.5">{entry.action}</p>
                {entry.agent && (
                  <p className="text-xs text-slate-500 mt-0.5">
                    Agent: {entry.agent}
                  </p>
                )}
              </div>
              <span className="text-xs text-slate-500 flex-shrink-0">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Download */}
      {!compact && (
        <div className="flex gap-3 pt-4">
          <button
            onClick={downloadJson}
            className="flex items-center gap-2 px-5 py-2.5 glass-light hover:bg-slate-700/50 rounded-xl transition-all duration-200 font-medium"
          >
            <Download className="w-4 h-4" />
            Download JSON Report
          </button>
        </div>
      )}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  color?: "green" | "red" | "yellow";
}

function MetricCard({ label, value, color }: MetricCardProps) {
  const colorClasses = {
    green: "text-emerald-400",
    red: "text-rose-400",
    yellow: "text-amber-400",
  };

  const bgClasses = {
    green: "from-emerald-500/10",
    red: "from-rose-500/10",
    yellow: "from-amber-500/10",
  };

  return (
    <div
      className={`glass-light rounded-xl p-3 sm:p-4 bg-gradient-to-br ${
        color ? bgClasses[color] : "from-slate-500/10"
      } to-transparent`}
    >
      <div
        className={`text-base sm:text-lg font-bold ${
          color ? colorClasses[color] : "text-white"
        } truncate`}
      >
        {value}
      </div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  );
}

interface InfoRowProps {
  icon: React.ReactNode;
  label: string;
  value: string | null | undefined;
}

function InfoRow({ icon, label, value }: InfoRowProps) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-slate-500 flex-shrink-0">{icon}</span>
      <span className="text-slate-400 flex-shrink-0 min-w-[80px]">
        {label}:
      </span>
      <span className="text-white truncate">{value || "N/A"}</span>
    </div>
  );
}

interface CollapsibleSectionProps {
  title: string;
  emoji: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function CollapsibleSection({
  title,
  emoji,
  icon,
  expanded,
  onToggle,
  children,
}: CollapsibleSectionProps) {
  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 sm:px-5 py-3.5 sm:py-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
      >
        <div className="flex items-center gap-3 text-slate-300">
          <span className="text-lg">{emoji}</span>
          <span className="font-semibold text-sm sm:text-base">{title}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          {expanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </div>
      </button>
      {expanded && (
        <div className="px-4 sm:px-5 pb-4 sm:pb-5 border-t border-slate-700/30 pt-4">
          {children}
        </div>
      )}
    </div>
  );
}
