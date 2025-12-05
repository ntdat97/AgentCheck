// Types matching Python backend schemas

export enum VerificationStatus {
  VERIFIED = "VERIFIED",
  NOT_VERIFIED = "NOT_VERIFIED",
  INCONCLUSIVE = "INCONCLUSIVE",
}

export enum ComplianceResult {
  COMPLIANT = "COMPLIANT",
  NOT_COMPLIANT = "NOT_COMPLIANT",
  INCONCLUSIVE = "INCONCLUSIVE",
}

export enum TaskStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
}

export interface ExtractedFields {
  candidate_name: string | null;
  university_name: string | null;
  degree_name: string | null;
  issue_date: string | null;
  raw_text: string | null;
  extraction_confidence: number;
}

export interface UniversityContact {
  name: string;
  email: string;
  country: string | null;
  verification_department: string | null;
}

export interface OutgoingEmail {
  id: string;
  recipient_email: string;
  recipient_name: string;
  subject: string;
  body: string;
  reference_id: string;
  created_at: string;
  certificate_info: ExtractedFields;
}

export interface IncomingEmail {
  id: string;
  sender_email: string;
  sender_name: string;
  subject: string;
  body: string;
  reference_id: string;
  received_at: string;
}

export interface ReplyAnalysis {
  verification_status: VerificationStatus;
  confidence_score: number;
  key_phrases: string[];
  explanation: string;
}

export interface AuditLogEntry {
  timestamp: string;
  step: string;
  action: string;
  agent: string | null;
  tool: string | null;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  success: boolean;
  error_message: string | null;
}

export interface ComplianceReport {
  id: string;
  created_at: string;
  pdf_filename: string;
  extracted_fields: ExtractedFields;
  university_identified: string | null;
  university_contact: UniversityContact | null;
  outgoing_email: OutgoingEmail | null;
  incoming_email: IncomingEmail | null;
  reply_analysis: ReplyAnalysis | null;
  verification_status: VerificationStatus;
  compliance_result: ComplianceResult;
  decision_explanation: string;
  audit_log: AuditLogEntry[];
  processing_time_seconds: number | null;
  agent_version: string;
}

export interface VerificationResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
  report: ComplianceReport | null;
}

export interface ReportSummary {
  id: string;
  pdf_filename: string;
  compliance_result: string;
  created_at: string;
  university_identified: string | null;
}

export interface HealthStatus {
  status: string;
  llm_available: boolean;
  data_dir: string;
  config_dir: string;
}

export interface Stats {
  total: number;
  compliant: number;
  not_compliant: number;
  inconclusive: number;
}

export type SimulationScenario =
  | "verified"
  | "not_verified"
  | "inconclusive"
  | "suspicious"
  | "ambiguous";
