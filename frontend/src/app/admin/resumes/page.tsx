"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPendingResumes, triggerAnalysis, triggerBatchAnalysis, PendingResume } from "@/lib/api/admin";
import PageHeader from "@/components/shared/PageHeader";
import DataTable from "@/components/shared/DataTable";
import StatusBadge from "@/components/shared/StatusBadge";
import ConfirmationModal from "@/components/shared/ConfirmationModal";
import { Play, PlayCircle, Clock } from "lucide-react";

export default function AdminResumesPage() {
  const [page, setPage] = useState(0);
  const limit = 50;
  
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["adminPendingResumes", page],
    queryFn: () => getPendingResumes(page * limit, limit),
  });

  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [isProcessingBatch, setIsProcessingBatch] = useState(false);
  
  const [singleAnalyzeId, setSingleAnalyzeId] = useState<string | null>(null);
  const [isProcessingSingle, setIsProcessingSingle] = useState(false);

  const handleBatchAnalyze = async () => {
    try {
      setIsProcessingBatch(true);
      await triggerBatchAnalysis(50);
      await refetch();
      setIsBatchModalOpen(false);
    } catch (error) {
      console.error("Batch analyze failed", error);
    } finally {
      setIsProcessingBatch(false);
    }
  };

  const handleSingleAnalyze = async () => {
    if (!singleAnalyzeId) return;
    try {
      setIsProcessingSingle(true);
      await triggerAnalysis(singleAnalyzeId);
      await refetch();
      setSingleAnalyzeId(null);
    } catch (error) {
      console.error("Single analyze failed", error);
    } finally {
      setIsProcessingSingle(false);
    }
  };

  const columns = [
    {
      header: "Student",
      accessor: (row: PendingResume) => (
        <span className="font-medium text-slate-900">{row.student_name}</span>
      ),
    },
    {
      header: "Type",
      accessor: (row: PendingResume) => (
        <span className="text-slate-600 capitalize">{row.resume_type}</span>
      ),
    },
    {
      header: "Upload Date",
      accessor: (row: PendingResume) => (
        <span className="text-slate-600">{new Date(row.upload_date).toLocaleDateString()}</span>
      ),
    },
    {
      header: "Status",
      accessor: (row: PendingResume) => (
        <StatusBadge status={row.processing_status} />
      ),
    },
    {
      header: "Actions",
      accessor: (row: PendingResume) => (
        <button
          onClick={() => setSingleAnalyzeId(row.resume_id)}
          className="text-indigo-600 hover:text-indigo-800 font-medium text-sm flex items-center gap-1 transition-colors"
        >
          <Play className="h-4 w-4" /> Analyze
        </button>
      ),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <PageHeader 
        title="Pending Resume Queue" 
        description="Manage resumes that are awaiting AI analysis or have failed processing."
        action={
          <button
            onClick={() => setIsBatchModalOpen(true)}
            disabled={!data?.items?.length}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            <PlayCircle className="h-5 w-5" />
            Process Next 50
          </button>
        }
      />

      <DataTable 
        columns={columns} 
        data={data?.items || []} 
        isLoading={isLoading} 
        emptyIcon={Clock}
        emptyTitle="Queue is empty"
        emptyDescription="There are no pending or failed resumes awaiting processing."
      />

      {data && data.total > limit && (
        <div className="flex justify-between items-center bg-white p-4 border border-slate-200 rounded-xl shadow-sm">
          <button 
            disabled={page === 0} 
            onClick={() => setPage(p => p - 1)}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">Page {page + 1}</span>
          <button 
            disabled={data.items.length < limit} 
            onClick={() => setPage(p => p + 1)}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      <ConfirmationModal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        onConfirm={handleBatchAnalyze}
        isProcessing={isProcessingBatch}
        title="Trigger Batch Analysis"
        description="This will enqueue up to 50 pending resumes for asynchronous processing. This operation may consume significant AI resources."
        confirmText="Start Processing"
      />

      <ConfirmationModal
        isOpen={!!singleAnalyzeId}
        onClose={() => setSingleAnalyzeId(null)}
        onConfirm={handleSingleAnalyze}
        isProcessing={isProcessingSingle}
        title="Trigger Analysis"
        description="This will enqueue the selected resume for asynchronous processing."
        confirmText="Start Analysis"
      />
    </div>
  );
}
