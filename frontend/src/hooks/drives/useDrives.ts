import { useQuery } from "@tanstack/react-query";
import { getDrive } from "@/services/drives/driveService";
import { DriveResponse } from "@/types/drives";

export const useDrive = (id: string) => {
  return useQuery<DriveResponse, Error>({
    queryKey: ["drive", id],
    queryFn: () => getDrive(id),
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!id,
  });
};
