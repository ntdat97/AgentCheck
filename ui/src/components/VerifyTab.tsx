import { useState, useRef } from "react";
import {
  Upload,
  FileCheck,
  AlertCircle,
  CheckCircle,
  XCircle,
  HelpCircle,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { api } from "../services/api";
import {
  ComplianceReport,
  SimulationScenario,
  ComplianceResult,
} from "../types";
import ResultsDisplay from "./ResultsDisplay";

interface VerifyTabProps {
  scenario: SimulationScenario;
  onVerificationComplete: () => void;
}

const VERIFICATION_STEPS = [
  { step: 1, label: "Parsing PDF..." },
  { step: 2, label: "Extracting fields..." },
  { step: 3, label: "Identifying university..." },
  { step: 4, label: "Drafting verification email..." },
  { step: 5, label: "AI analyzing university reply..." },
  { step: 6, label: "Generating compliance report..." },
];

export default function VerifyTab({
  scenario,
  onVerificationComplete,
}: VerifyTabProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ComplianceReport | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === "application/pdf") {
      setUploadedFile(file);
      setError(null);
      setReport(null);
    } else {
      setError("Please select a valid PDF file");
    }
  };

  const handleSampleSelect = async (sampleName: string) => {
    setError(null);
    setReport(null);
    setUploadedFile(null);
    await runVerification(sampleName, true);
  };

  const handleVerify = async () => {
    if (!uploadedFile) return;
    await runVerification(uploadedFile);
  };

  const runVerification = async (
    fileOrSample: File | string,
    isSample = false
  ) => {
    setIsVerifying(true);
    setCurrentStep(0);
    setProgress(0);
    setError(null);
    setReport(null);

    try {
      for (let i = 0; i < VERIFICATION_STEPS.length - 1; i++) {
        setCurrentStep(i + 1);
        setProgress(((i + 1) / VERIFICATION_STEPS.length) * 100);
        await new Promise((resolve) => setTimeout(resolve, 300));
      }

      let result;
      // Always use function calling for AI-driven interpretation
      if (isSample && typeof fileOrSample === "string") {
        result = await api.verifySample(fileOrSample, scenario, true);
      } else if (fileOrSample instanceof File) {
        result = await api.uploadAndVerify(fileOrSample, scenario, true);
      } else {
        throw new Error("Invalid input");
      }

      setCurrentStep(VERIFICATION_STEPS.length);
      setProgress(100);

      if (result.report) {
        setReport(result.report);
        onVerificationComplete();
      } else {
        setError("No report returned from verification");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setIsVerifying(false);
    }
  };

  const getComplianceIcon = (result: ComplianceResult) => {
    switch (result) {
      case ComplianceResult.COMPLIANT:
        return (
          <CheckCircle className="w-7 h-7 sm:w-8 sm:h-8 text-emerald-400" />
        );
      case ComplianceResult.NOT_COMPLIANT:
        return <XCircle className="w-7 h-7 sm:w-8 sm:h-8 text-rose-400" />;
      default:
        return <HelpCircle className="w-7 h-7 sm:w-8 sm:h-8 text-amber-400" />;
    }
  };

  const getComplianceBanner = (result: ComplianceResult) => {
    switch (result) {
      case ComplianceResult.COMPLIANT:
        return {
          bg: "from-emerald-100 to-emerald-50 border-emerald-400",
          text: "text-emerald-700",
          message: "COMPLIANT - Certificate verified successfully",
        };
      case ComplianceResult.NOT_COMPLIANT:
        return {
          bg: "from-rose-100 to-rose-50 border-rose-400",
          text: "text-rose-700",
          message: "NOT COMPLIANT - Certificate could not be verified",
        };
      default:
        return {
          bg: "from-amber-100 to-amber-50 border-amber-400",
          text: "text-amber-700",
          message: "INCONCLUSIVE - Manual review required",
        };
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="mb-6 sm:mb-8">
        <h2 className="text-2xl sm:text-3xl font-bold mb-2 flex items-center gap-3">
          <span className="text-2xl sm:text-3xl">📄</span>
          Upload Certificate
        </h2>
        <p className="text-slate-500 text-sm sm:text-base">
          Upload a PDF certificate to verify its authenticity
        </p>
      </div>

      {/* File Upload Area */}
      <div
        className={`
          glass-card rounded-2xl p-6 sm:p-10 text-center cursor-pointer transition-all duration-300 hover-lift
          ${
            uploadedFile
              ? "border-emerald-500/50 bg-gradient-to-br from-emerald-500/10 to-transparent"
              : "hover:border-blue-500/50"
          }
        `}
        onClick={() => !uploadedFile && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
        />

        {uploadedFile ? (
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <FileCheck className="w-7 h-7 text-emerald-400" />
            </div>
            <div className="text-center sm:text-left">
              <p className="text-emerald-400 font-semibold text-lg break-all">
                {uploadedFile.name}
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setUploadedFile(null);
                }}
                className="text-sm text-slate-500 hover:text-slate-800 transition-colors mt-1"
              >
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-slate-200/50 flex items-center justify-center mx-auto mb-4 sm:mb-6">
              <Upload className="w-8 h-8 sm:w-10 sm:h-10 text-slate-500" />
            </div>
            <p className="text-slate-600 text-base sm:text-lg mb-2">
              Drag and drop a PDF file here, or{" "}
              <span className="text-blue-400 hover:underline">browse</span>
            </p>
            <p className="text-sm text-slate-400">Accepts PDF files only</p>
          </div>
        )}
      </div>

      {/* Sample Certificates */}
      <div className="mt-6 sm:mt-8">
        <p className="text-slate-500 mb-4 text-sm sm:text-base">
          Or try a sample certificate:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <SampleButton
            onClick={() => handleSampleSelect("certificate_verified")}
            sampleName="certificate_verified"
            icon={<CheckCircle className="w-4 h-4" />}
            label="Verified Sample"
            color="green"
            disabled={isVerifying}
          />
          <SampleButton
            onClick={() =>
              handleSampleSelect(
                "Graduate-Diploma-University-of-Western-Australia"
              )
            }
            sampleName="Graduate-Diploma-University-of-Western-Australia"
            icon={<XCircle className="w-4 h-4" />}
            label="Denied Sample"
            color="red"
            disabled={isVerifying}
          />
          <SampleButton
            onClick={() => handleSampleSelect("certificate_unknown")}
            sampleName="certificate_unknown"
            icon={<HelpCircle className="w-4 h-4" />}
            label="Unknown Sample"
            color="yellow"
            disabled={isVerifying}
          />
        </div>
      </div>

      {/* Verify Button */}
      {uploadedFile && !isVerifying && !report && (
        <div className="mt-6 sm:mt-8">
          <button
            onClick={handleVerify}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-semibold py-3.5 sm:py-4 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-3 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30"
          >
            <Sparkles className="w-5 h-5" />
            Verify Certificate
          </button>
        </div>
      )}

      {/* Progress */}
      {isVerifying && (
        <div className="mt-8 glass-card rounded-2xl p-6 section-enter">
          <div className="flex items-center gap-4 mb-5">
            <div className="relative">
              <div className="w-10 h-10 rounded-full border-2 border-blue-500/30" />
              <div className="absolute inset-0 w-10 h-10 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
            </div>
            <div>
              <span className="text-slate-800 font-medium block">
                {currentStep > 0 && currentStep <= VERIFICATION_STEPS.length
                  ? VERIFICATION_STEPS[currentStep - 1].label
                  : "Initializing..."}
              </span>
              <span className="text-slate-400 text-sm">
                Step {currentStep} of {VERIFICATION_STEPS.length}
              </span>
            </div>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start gap-3 section-enter">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <span className="text-rose-300">{error}</span>
        </div>
      )}

      {/* Results */}
      {report && (
        <div className="mt-8 sm:mt-10 section-enter">
          <hr className="border-slate-300/50 mb-8" />

          {/* Compliance Banner */}
          {(() => {
            const banner = getComplianceBanner(report.compliance_result);
            return (
              <div
                className={`bg-gradient-to-r ${banner.bg} border rounded-xl p-4 sm:p-5 flex items-center gap-4 mb-8`}
              >
                {getComplianceIcon(report.compliance_result)}
                <span className={`text-lg sm:text-xl font-bold ${banner.text}`}>
                  {banner.message}
                </span>
              </div>
            );
          })()}

          <ResultsDisplay report={report} />
        </div>
      )}
    </div>
  );
}

interface SampleButtonProps {
  onClick: () => void;
  sampleName: string;
  icon: React.ReactNode;
  label: string;
  color: "green" | "red" | "yellow";
  disabled?: boolean;
}

function SampleButton({
  onClick,
  sampleName,
  icon,
  label,
  color,
  disabled,
}: SampleButtonProps) {
  const colorClasses = {
    green:
      "from-emerald-100 to-emerald-50 border-emerald-400 text-emerald-600 hover:border-emerald-500 hover:bg-emerald-100",
    red: "from-rose-100 to-rose-50 border-rose-400 text-rose-600 hover:border-rose-500 hover:bg-rose-100",
    yellow:
      "from-amber-100 to-amber-50 border-amber-400 text-amber-600 hover:border-amber-500 hover:bg-amber-100",
  };

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(`/sample/${sampleName}.pdf`, "_blank");
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex items-center justify-center gap-2 px-4 py-3 rounded-xl border
        bg-gradient-to-br transition-all duration-200
        disabled:opacity-40 disabled:cursor-not-allowed
        ${colorClasses[color]}
      `}
    >
      {icon}
      <span className="font-medium">{label}</span>
      <span title="Preview PDF" onClick={handlePreview}>
        <ExternalLink className="w-4 h-4 ml-1 opacity-60 hover:opacity-100 cursor-pointer" />
      </span>
    </button>
  );
}
