"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getResumes, uploadResume } from "@/lib/api/resume";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import StatusBadge from "@/components/shared/StatusBadge";
import Card from "@/components/shared/Card";
import { UploadCloud, File as FileIcon, Loader2 } from "lucide-react";

export default function StudentResumePage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [resumeType, setResumeType] = useState<"generic" | "specialized">("generic");
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: resumesData, isLoading, error, refetch } = useQuery({
    queryKey: ["studentResumes"],
    queryFn: getResumes,
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadResume(file!, resumeType),
    onSuccess: () => {
      setFile(null);
      setTermsAccepted(false);
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ["studentResumes"] });
      queryClient.invalidateQueries({ queryKey: ["studentDashboard"] });
    },
    onError: (err: Record<string, unknown> | Error) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const errorResponse = err as any;
      setUploadError(errorResponse?.response?.data?.detail || errorResponse.message || "Failed to upload resume.");
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleUpload = () => {
    if (!file || !termsAccepted) return;
    setUploadError(null);
    uploadMutation.mutate();
  };

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Resume Management</h1>
        <p className="text-sm text-slate-500 mt-1">Upload your latest resume to receive AI-powered placement analysis.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Section */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Upload New Resume</h2>
            
            {uploadError && (
              <ErrorState 
                title="Upload Failed" 
                message={uploadError} 
                className="mb-6 p-4 border-red-200 bg-red-50 text-left rounded-lg"
              />
            )}

            {uploadMutation.isSuccess && (
              <div className="mb-6 rounded-lg bg-emerald-50 p-4 border border-emerald-200">
                <h3 className="text-sm font-semibold text-emerald-800">Resume uploaded successfully.</h3>
                <p className="text-xs text-emerald-600 mt-1">Waiting for administrator review.</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Resume Type</label>
                <select
                  value={resumeType}
                  onChange={(e) => setResumeType(e.target.value as "generic" | "specialized")}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                >
                  <option value="generic">Generic (Standard)</option>
                  <option value="specialized">Specialized (Targeted)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">File</label>
                <label
                  htmlFor="resume-upload"
                  className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                    file ? "border-indigo-400 bg-indigo-50/50" : "border-slate-300 bg-slate-50 hover:bg-slate-100"
                  }`}
                >
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    {file ? (
                      <>
                        <FileIcon className="w-8 h-8 text-indigo-500 mb-2" />
                        <p className="text-sm font-semibold text-indigo-700 truncate max-w-[200px]">{file.name}</p>
                      </>
                    ) : (
                      <>
                        <UploadCloud className="w-8 h-8 text-slate-400 mb-2" />
                        <p className="mb-1 text-sm text-slate-500">
                          <span className="font-semibold text-indigo-600">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-slate-400">PDF or DOCX (MAX. 10MB)</p>
                      </>
                    )}
                  </div>
                  <input
                    id="resume-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx"
                    onChange={handleFileChange}
                  />
                </label>
              </div>

              <div className="flex items-start gap-2 pt-2">
                <input
                  type="checkbox"
                  id="terms"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-1 shrink-0 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="terms" className="text-xs text-slate-600 leading-tight">
                  I confirm that the uploaded resume belongs to me and the information is accurate.
                </label>
              </div>

              <button
                type="button"
                onClick={handleUpload}
                disabled={!file || !termsAccepted || uploadMutation.isPending}
                className="w-full flex justify-center items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {uploadMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                {uploadMutation.isPending ? "Uploading..." : "Upload Resume"}
              </button>
            </div>
          </Card>
        </div>

        {/* Resumes Section */}
        <div className="lg:col-span-2">
          <Card className="overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-200">
              <h2 className="text-lg font-bold text-slate-800">Current Resumes</h2>
              <p className="text-sm text-slate-500">Your uploaded resumes. Analysis is performed on the currently stored resume.</p>
            </div>
            
            {isLoading ? (
              <LoadingState message="Loading your resumes..." />
            ) : error ? (
              <div className="p-6">
                <ErrorState message="Could not fetch resumes." retryAction={() => refetch()} />
              </div>
            ) : resumesData?.data?.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-sm">
                No resumes uploaded yet. Upload your first resume to begin.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200 uppercase">
                    <tr>
                      <th scope="col" className="px-6 py-3 font-semibold">Date</th>
                      <th scope="col" className="px-6 py-3 font-semibold">File</th>
                      <th scope="col" className="px-6 py-3 font-semibold">Type</th>
                      <th scope="col" className="px-6 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {resumesData?.data.map((resume) => (
                      <tr key={resume.id} className="bg-white hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 text-slate-600 whitespace-nowrap">
                          {new Date(resume.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-900 truncate max-w-[200px]" title={resume.filename}>
                          {resume.filename}
                        </td>
                        <td className="px-6 py-4 text-slate-600 capitalize">
                          {resume.resume_type}
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={resume.processing_status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

      </div>
    </div>
  );
}
