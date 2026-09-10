import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAnalysisHistory, triggerAnalysis } from "@/services/drives/analysisService";
import { AnalysisListResponse, AnalysisResponse, AnalyzeDriveRequest, DriveResponse } from "@/types/drives";

export const useAnalysisHistory = (driveId: string, drive?: DriveResponse) => {
  const queryClient = useQueryClient();

  return useQuery<AnalysisListResponse, Error>({
    queryKey: ["analysis", driveId],
    queryFn: () => getAnalysisHistory(driveId),
    staleTime: 5 * 1000, // 5 seconds
    enabled: !!driveId,
    refetchInterval: (query) => {
      // Determine if we should poll based on drive status OR latest analysis status
      const isDriveAnalyzing = drive?.status === "analyzing";
      const analyses = query.state.data?.analyses;
      const latestAnalysisStatus = analyses && analyses.length > 0 ? analyses[0].status : null;
      
      const isAnalysisPendingOrRunning = 
        latestAnalysisStatus === "pending" || latestAnalysisStatus === "running";

      if (isDriveAnalyzing || isAnalysisPendingOrRunning) {
        return 4000; // Poll every 4 seconds
      }
      return false; // Stop polling
    },
    // We can also trigger side-effects when data changes using React Query v5 conventions
    // Normally handled in useEffect in the component, or we can use structural sharing/meta
  });
};

export const useTriggerAnalysis = (driveId: string) => {
  const queryClient = useQueryClient();

  return useMutation<AnalysisResponse, Error, AnalyzeDriveRequest | void>({
    mutationFn: (req) => triggerAnalysis(driveId, req || {}),
    onSuccess: () => {
      // Immediate invalidation to start polling and reflect status
      queryClient.invalidateQueries({ queryKey: ["drive", driveId] });
      queryClient.invalidateQueries({ queryKey: ["analysis", driveId] });
    },
  });
};
