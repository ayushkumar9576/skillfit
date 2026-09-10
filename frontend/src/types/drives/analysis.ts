export interface AnalysisResponse {
  id: string;
  drive_id: string;
  source_id: string | null;
  snapshot_id: string | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  created_at: string;
  analysis_version: string;
  prompt_version: string;
  model_name: string;
  error_message: string | null;
  processing_metadata: Record<string, unknown> | null;
}

export interface AnalysisListResponse {
  drive_id: string;
  total: number;
  analyses: AnalysisResponse[];
}

export interface AnalyzeDriveRequest {
  prompt_version?: string;
}
