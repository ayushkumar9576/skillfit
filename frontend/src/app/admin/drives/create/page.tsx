"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Building2, Briefcase, MapPin, IndianRupee, FileText, Calendar, Upload } from "lucide-react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";

export default function CreateDrivePage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    
    // We are creating a draft drive via POST /api/v1/drives
    // It requires company_name, role, placement_season, and source_type by default
    const payload = {
      company_name: formData.get("company_name") as string,
      role: formData.get("role") as string,
      placement_season: "2024-2025", 
      job_type: formData.get("job_type") as string || undefined,
      location: formData.get("location") as string || undefined,
      package: formData.get("package") as string || undefined,
      eligibility_criteria: formData.get("eligibility_criteria") as string || undefined,
      description: formData.get("description") as string || undefined,
      application_deadline: formData.get("application_deadline") as string || undefined,
      source_type: "manual", 
    };

    try {
      const response = await fetchApi("/api/v1/drives", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.id) {
        throw new Error("Failed to create drive");
      }

      // Step 2: Handle JD Ingestion
      const jdFile = formData.get("jd_file") as File;
      const jdText = formData.get("jd_text") as string;

      if (jdFile && jdFile.size > 0) {
        const fileData = new FormData();
        fileData.append("file", jdFile);
        
        // Cannot use fetchApi directly here because of FormData content-type issues
        const token = localStorage.getItem("access_token");
        const uploadRes = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/drives/${response.id}/upload`, {
          method: "POST",
          headers: token ? { "Authorization": `Bearer ${token}` } : {},
          body: fileData,
        });
        
        if (!uploadRes.ok) {
          const err = await uploadRes.json();
          throw new Error(err.detail || "Failed to upload JD PDF");
        }
      } else if (jdText && jdText.trim()) {
        await fetchApi(`/api/v1/drives/${response.id}/text`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: jdText }),
        });
      } else {
        throw new Error("A Job Description (PDF or Text) is mandatory.");
      }

      // Success, redirect to pending queue
      router.push("/admin/drives/pending");
    } catch (err: any) {
      setError(err.message);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Create New Drive</h2>
          <p className="text-slate-500 mt-1">Initialize a placement drive in draft state.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {error && (
          <div className="p-4 bg-red-50 border-b border-red-100 text-red-700 text-sm">
            {error}
          </div>
        )}
        
        <div className="p-6 md:p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label htmlFor="company_name" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-slate-400" /> Company Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="company_name"
                name="company_name"
                required
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="e.g. Google"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="role" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-slate-400" /> Role <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="role"
                name="role"
                required
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="e.g. Software Engineer"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="package" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <IndianRupee className="w-4 h-4 text-slate-400" /> Package Details
              </label>
              <input
                type="text"
                id="package"
                name="package"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="e.g. 18 LPA"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="location" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-slate-400" /> Location
              </label>
              <input
                type="text"
                id="location"
                name="location"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="e.g. Bangalore, Remote"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label htmlFor="eligibility_criteria" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-400" /> Eligibility Criteria
              </label>
              <textarea
                id="eligibility_criteria"
                name="eligibility_criteria"
                rows={2}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="e.g. B.Tech CSE/IT with 7.5+ CGPA"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="application_deadline" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" /> Application Deadline
              </label>
              <input
                type="date"
                id="application_deadline"
                name="application_deadline"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium text-slate-700 flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-400" /> Drive Description
            </label>
            <textarea
              id="description"
              name="description"
              rows={2}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Additional details about the role or company..."
            />
          </div>

          <div className="pt-6 border-t border-slate-100 space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Job Description Source <span className="text-red-500">*</span></h3>
              <p className="text-sm text-slate-500 mt-1">Provide the job description for intelligence extraction. You must provide either a PDF or raw text.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label htmlFor="jd_file" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <Upload className="w-4 h-4 text-slate-400" /> Upload JD (PDF)
                </label>
                <input
                  type="file"
                  id="jd_file"
                  name="jd_file"
                  accept="application/pdf"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="jd_text" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-400" /> Or Paste JD Text
                </label>
                <textarea
                  id="jd_text"
                  name="jd_text"
                  rows={4}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  placeholder="Paste the raw text of the job description here..."
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-50 p-6 border-t border-slate-200 flex items-center justify-between">
          <p className="text-sm text-slate-500">The drive will be saved as a draft. Analysis will not start automatically.</p>
          <div className="flex gap-3">
            <Link href="/admin/drives" className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {isSubmitting ? "Saving..." : "Save Draft"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
