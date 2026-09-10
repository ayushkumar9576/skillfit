import { DriveIntelligenceProfile } from "./intelligence";

export interface SnapshotSummaryResponse {
  id: string;
  drive_id: string;
  source_id: string | null;
  analysis_id: string | null;
  analysis_version: string;
  prompt_version: string | null;
  model_name: string | null;
  intelligence_schema_version: string | null;
  created_at: string;
}

export interface SnapshotDetailResponse {
  id: string;
  drive_id: string;
  source_id: string | null;
  analysis_id: string | null;
  analysis_version: string;
  prompt_version: string | null;
  model_name: string | null;
  intelligence_schema_version: string | null;
  intelligence_payload: DriveIntelligenceProfile;
  metadata_payload: Record<string, unknown> | null;
  created_at: string;
}

export interface SnapshotListResponse {
  drive_id: string;
  total: number;
  snapshots: SnapshotSummaryResponse[];
}
