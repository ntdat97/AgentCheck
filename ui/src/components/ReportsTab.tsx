import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  CheckCircle,
  XCircle,
  HelpCircle,
  RefreshCw,
  FileText,
} from "lucide-react";
import { api } from "../services/api";
import { ReportSummary, ComplianceReport } from "../types";
import ResultsDisplay from "./ResultsDisplay";

interface ReportsTabProps {
  reports: ReportSummary[];
  onRefresh: () => void;
}

export default function ReportsTab({ reports, onRefresh }: ReportsTabProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loadedReport, setLoadedReport] = useState<ComplianceReport | null>(
    null
  );
  const [loading, setLoading] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  const handleToggle = async (reportId: string) => {
    if (expandedId === reportId) {
      setExpandedId(null);
      setLoadedReport(null);
      return;
    }

    setExpandedId(reportId);
    setLoading(reportId);

    try {
      const report = await api.getReport(reportId);
      setLoadedReport(report);
    } catch (error) {
      console.error("Failed to load report:", error);
    } finally {
      setLoading(null);
    }
  };

  const getStatusIcon = (result: string) => {
    switch (result) {
      case "COMPLIANT":
        return (
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
        );
      case "NOT_COMPLIANT":
        return (
          <div className="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center">
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
            <HelpCircle className="w-4 h-4 text-amber-400" />
          </div>
        );
    }
  };

  const getStatusColor = (result: string) => {
    switch (result) {
      case "COMPLIANT":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
      case "NOT_COMPLIANT":
        return "text-rose-400 bg-rose-500/10 border-rose-500/30";
      default:
        return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 sm:mb-8">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold flex items-center gap-3">
            <span className="text-2xl sm:text-3xl">📋</span>
            Recent Reports
          </h2>
          <p className="text-slate-500 text-sm sm:text-base mt-1">
            {reports.length} verification{reports.length !== 1 ? "s" : ""}{" "}
            completed
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center justify-center gap-2 px-4 py-2.5 glass-light hover:bg-slate-200/50 rounded-xl transition-all duration-200 font-medium self-start disabled:opacity-70"
        >
          <RefreshCw
            className={`w-4 h-4 transition-transform duration-300 ${
              isRefreshing ? "animate-spin" : ""
            }`}
          />
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Reports List */}
      {reports.length === 0 ? (
        <div className="glass-card rounded-2xl p-10 sm:p-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-slate-200/50 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-slate-400" />
          </div>
          <p className="text-slate-500 text-lg mb-2">No reports yet</p>
          <p className="text-slate-400 text-sm">
            Verify a certificate to get started!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div
              key={report.id}
              className="glass-card rounded-xl overflow-hidden hover-lift"
            >
              <button
                onClick={() => handleToggle(report.id)}
                className="w-full px-4 sm:px-5 py-4 flex items-center justify-between hover:bg-slate-100/50 transition-colors"
              >
                <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                  {getStatusIcon(report.compliance_result)}
                  <div className="text-left min-w-0">
                    <p className="font-medium text-slate-800 truncate text-sm sm:text-base">
                      {report.pdf_filename}
                    </p>
                    <p className="text-xs sm:text-sm text-slate-500 truncate">
                      {report.university_identified || "Unknown University"} •{" "}
                      {new Date(report.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0 ml-2">
                  <span
                    className={`hidden sm:inline px-3 py-1 rounded-lg text-xs font-semibold border ${getStatusColor(
                      report.compliance_result
                    )}`}
                  >
                    {report.compliance_result}
                  </span>
                  {expandedId === report.id ? (
                    <ChevronDown className="w-5 h-5 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-slate-500" />
                  )}
                </div>
              </button>

              {expandedId === report.id && (
                <div className="border-t border-slate-300/30 p-4 sm:p-5 bg-slate-100/30">
                  {loading === report.id ? (
                    <div className="flex items-center justify-center py-10">
                      <div className="relative">
                        <div className="w-10 h-10 rounded-full border-2 border-blue-500/30" />
                        <div className="absolute inset-0 w-10 h-10 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                      </div>
                    </div>
                  ) : loadedReport ? (
                    <ResultsDisplay report={loadedReport} compact />
                  ) : (
                    <p className="text-slate-500 text-center py-6">
                      Failed to load report
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
