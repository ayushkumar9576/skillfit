import { DriveStatus, DriveSourceType } from "./enums";

export interface DriveResponse {
  id: string;
  company_name: string;
  role: string;
  placement_season: string;
  job_type: string | null;
  location: string | null;
  package: string | null;
  eligibility_criteria: string | null;
  description: string | null;
  application_deadline: string | null;
  status: DriveStatus;
  source_type: DriveSourceType;
  created_at: string;
  updated_at: string;
}

export interface DriveListResponse {
  drives: DriveResponse[];
  total: number;
}
