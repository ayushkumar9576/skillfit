import React, { useCallback, useState } from "react";
import { UploadCloud, File as FileIcon, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadCardProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  accept?: string;
  maxSizeMB?: number;
}

export default function UploadCard({ 
  onUpload, 
  isUploading,
  accept = "application/pdf", 
  maxSizeMB = 10 
}: UploadCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const validateFile = (file: File): boolean => {
    setError(null);
    if (accept === "application/pdf" && file.type !== "application/pdf") {
      setError("Please upload a valid PDF file.");
      return false;
    }
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size must be less than ${maxSizeMB}MB.`);
      return false;
    }
    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  }, [accept, maxSizeMB]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setError(null);
  };

  const handleUploadClick = async () => {
    if (selectedFile) {
      try {
        await onUpload(selectedFile);
        setSelectedFile(null);
      } catch (err) {
        // Error handling is likely handled by the parent mutation, but we can set local if needed.
        console.error(err);
      }
    }
  };

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div 
          className={cn(
            "relative w-full h-64 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 transition-colors",
            dragActive ? "border-indigo-500 bg-indigo-50/50" : "border-slate-300 hover:border-slate-400 bg-slate-50/30",
            error ? "border-red-300 bg-red-50/30" : ""
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            accept={accept}
            onChange={handleChange}
            disabled={isUploading}
          />
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className={cn(
              "p-4 rounded-full transition-colors",
              dragActive ? "bg-indigo-100 text-indigo-600" : "bg-white text-slate-400 shadow-sm border border-slate-100",
              error ? "bg-red-100 text-red-500" : ""
            )}>
              <UploadCloud className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-slate-500 mt-1">
                PDF only (max. {maxSizeMB}MB)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="w-full border border-slate-200 rounded-xl bg-white p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 flex-1 min-w-0">
              <div className="p-3 bg-indigo-50 rounded-lg shrink-0">
                <FileIcon className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 ml-4 shrink-0">
              {!isUploading && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={handleUploadClick}
              disabled={isUploading}
              className="inline-flex items-center gap-2 px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
              {isUploading ? "Uploading & Processing..." : "Confirm Upload"}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
