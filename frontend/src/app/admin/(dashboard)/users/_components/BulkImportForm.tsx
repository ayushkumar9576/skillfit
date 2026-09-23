"use client";

import { useState, useRef } from "react";
import { Upload, FileSpreadsheet, Download, AlertCircle, CheckCircle2, X } from "lucide-react";
import { getToken } from "@/lib/auth/token";

interface BulkImportFormProps {
  type: "student" | "faculty";
}

interface ImportResult {
  success: boolean;
  processed?: number;
  created?: number;
  failed?: number;
  errors?: Array<{ row: number; message: string }>;
}

export default function BulkImportForm({ type }: BulkImportFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const title = type === "student" ? "Bulk Import Students" : "Bulk Import Faculty";
  const apiEndpoint = type === "student" 
    ? "/api/v1/admin/import/students" 
    : "/api/v1/admin/import/faculty";
  const templateEndpoint = type === "student"
    ? "/api/v1/admin/import/templates/student"
    : "/api/v1/admin/import/templates/faculty";

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    setResult(null);
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    if (!selectedFile.name.endsWith(".xlsx")) {
      setErrorMsg("Please upload a valid .xlsx file.");
      setFile(null);
      return;
    }
    if (selectedFile.size > 5 * 1024 * 1024) {
      setErrorMsg("File size exceeds 5MB limit.");
      setFile(null);
      return;
    }
    setFile(selectedFile);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) {
      setIsDragging(true);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    setErrorMsg(null);
    setResult(null);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setErrorMsg(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = getToken();
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${baseUrl}${apiEndpoint}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.errors) {
          setResult({ success: false, errors: data.errors });
        } else {
          setErrorMsg(data.detail || "Upload failed due to a server error.");
        }
      } else {
        setResult(data);
        setFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    } catch (err) {
      console.error("Upload error:", err);
      setErrorMsg("A network error occurred. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownloadTemplate = () => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const token = getToken();
    
    fetch(`${baseUrl}${templateEndpoint}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to download template");
        return res.blob();
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${type}_import_template.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      })
      .catch((err) => {
        console.error(err);
        setErrorMsg("Failed to download template.");
      });
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          <p className="text-sm text-slate-500 mt-1">
            Upload an Excel (.xlsx) file to create multiple accounts at once.
          </p>
        </div>
        <button
          onClick={handleDownloadTemplate}
          className="flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-4 py-2 rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          Download Template
        </button>
      </div>

      <div 
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          isDragging ? "border-indigo-500 bg-indigo-50" : "border-slate-200 bg-slate-50 hover:bg-slate-100"
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".xlsx"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
        />
        
        {file ? (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <FileSpreadsheet className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900">{file.name}</p>
              <p className="text-xs text-slate-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload File
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
            <div className="w-12 h-12 bg-white border border-slate-200 rounded-full flex items-center justify-center shadow-sm">
              <Upload className="w-5 h-5 text-slate-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900">Click to upload or drag and drop</p>
              <p className="text-xs text-slate-500 mt-1">XLSX up to 5MB (Max 1000 rows)</p>
            </div>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
          <div className="text-sm">{errorMsg}</div>
        </div>
      )}

      {result?.success && (
        <div className="p-4 bg-emerald-50 text-emerald-800 border border-emerald-100 rounded-lg flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 mt-0.5 shrink-0" />
          <div>
            <h4 className="text-sm font-semibold mb-1">Import Successful</h4>
            <p className="text-sm opacity-90">
              Successfully imported {result.created} {type} accounts. All new users will be required to change their passwords upon first login.
            </p>
          </div>
        </div>
      )}

      {result?.success === false && result.errors && (
        <div className="bg-red-50 border border-red-100 rounded-lg overflow-hidden">
          <div className="p-4 flex items-center gap-3 border-b border-red-100">
            <X className="w-5 h-5 text-red-600" />
            <h4 className="text-sm font-semibold text-red-800">Import Failed — Validation Errors</h4>
          </div>
          <div className="max-h-60 overflow-y-auto p-4 bg-white">
            <ul className="space-y-3">
              {result.errors.map((err, i) => (
                <li key={i} className="text-sm flex gap-3">
                  <span className="font-mono text-red-600 font-medium shrink-0">Row {err.row}:</span>
                  <span className="text-slate-700">{err.message}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
