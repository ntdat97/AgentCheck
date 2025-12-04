import axios, { AxiosInstance } from "axios";
import {
  ComplianceReport,
  VerificationResponse,
  ReportSummary,
  HealthStatus,
  SimulationScenario,
} from "../types";

// API base URL - uses proxy in development
const API_BASE_URL = "/api";

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Extract error message from API response
        let errorMessage = "An unexpected error occurred";

        if (error.response?.data) {
          const data = error.response.data;
          // Handle FastAPI's standard error format: { "detail": "..." }
          if (typeof data.detail === "string") {
            errorMessage = data.detail;
          } else if (typeof data.message === "string") {
            errorMessage = data.message;
          } else if (typeof data.error === "string") {
            errorMessage = data.error;
          } else if (typeof data === "string") {
            errorMessage = data;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }

        // Create a new error with the extracted message
        const enhancedError = new Error(errorMessage);
        (enhancedError as any).status = error.response?.status;
        (enhancedError as any).originalError = error;

        return Promise.reject(enhancedError);
      }
    );
  }

  /**
   * Health check endpoint
   */
  async getHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>("/health");
    return response.data;
  }

  /**
   * Upload a PDF file
   */
  async uploadPdf(
    file: File
  ): Promise<{ filename: string; path: string; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await this.client.post("/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  }

  /**
   * Verify a certificate by PDF path
   */
  async verifyCertificate(
    pdfPath: string,
    scenario: SimulationScenario = "verified"
  ): Promise<VerificationResponse> {
    const response = await this.client.post<VerificationResponse>("/verify", {
      pdf_path: pdfPath,
      simulation_scenario: scenario,
    });
    return response.data;
  }

  /**
   * List all reports
   */
  async listReports(limit: number = 50): Promise<ReportSummary[]> {
    const response = await this.client.get<{ reports: ReportSummary[] }>(
      "/reports",
      {
        params: { limit },
      }
    );
    return response.data.reports;
  }

  /**
   * Get a specific report by ID
   */
  async getReport(reportId: string): Promise<ComplianceReport> {
    const response = await this.client.get<ComplianceReport>(
      `/reports/${reportId}`
    );
    return response.data;
  }

  /**
   * Get report as text
   */
  async getReportText(reportId: string): Promise<string> {
    const response = await this.client.get<string>(`/reports/${reportId}/text`);
    return response.data;
  }

  /**
   * Upload and verify in one step
   */
  async uploadAndVerify(
    file: File,
    scenario: SimulationScenario = "verified"
  ): Promise<VerificationResponse> {
    // First upload the file
    const uploadResult = await this.uploadPdf(file);

    // Then verify it
    return this.verifyCertificate(uploadResult.path, scenario);
  }

  /**
   * Verify using sample file
   */
  async verifySample(
    sampleName: string,
    scenario: SimulationScenario = "verified"
  ): Promise<VerificationResponse> {
    const pdfPath = `./data/sample_pdfs/${sampleName}.pdf`;
    return this.verifyCertificate(pdfPath, scenario);
  }
}

// Export singleton instance
export const api = new ApiService();
export default api;
