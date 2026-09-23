import React, { useState } from "react";
import { FileText, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface PasteTextFormProps {
  onSubmit: (text: string) => Promise<void>;
  isSubmitting: boolean;
  minChars?: number;
}

export default function PasteTextForm({ 
  onSubmit, 
  isSubmitting,
  minChars = 50 
}: PasteTextFormProps) {
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (text.length < minChars) {
      setError(`Job description must be at least ${minChars} characters long.`);
      return;
    }
    
    setError(null);
    try {
      await onSubmit(text);
      setText("");
    } catch (err) {
      console.error(err);
      // Handled by parent typically
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    if (error && e.target.value.length >= minChars) {
      setError(null);
    }
  };

  const progress = Math.min((text.length / minChars) * 100, 100);
  const isValid = text.length >= minChars;

  return (
    <div className="w-full space-y-4">
      <div className="relative">
        <div className="absolute top-4 left-4 p-2 bg-indigo-50 rounded-lg pointer-events-none">
          <FileText className="w-5 h-5 text-indigo-600" />
        </div>
        <textarea
          value={text}
          onChange={handleTextChange}
          disabled={isSubmitting}
          placeholder="Paste the raw job description text here..."
          className={cn(
            "w-full h-64 pl-16 pr-4 py-4 text-sm border rounded-xl resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-colors bg-white",
            error ? "border-red-300 focus:border-red-500" : "border-slate-200 focus:border-indigo-500",
            isSubmitting ? "opacity-70 bg-slate-50" : ""
          )}
        />
        
        {/* Character Count Indicator */}
        <div className="absolute bottom-4 right-4 flex items-center gap-3 bg-white px-3 py-1.5 rounded-full border border-slate-100 shadow-sm text-xs font-medium">
          <span className={cn(isValid ? "text-emerald-600" : "text-slate-500")}>
            {text.length} {isValid ? "chars" : `/ ${minChars} min chars`}
          </span>
          {!isValid && text.length > 0 && (
            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <div className="flex justify-end pt-2">
        <button
          onClick={handleSubmit}
          disabled={!isValid || isSubmitting}
          className="inline-flex items-center gap-2 px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
          {isSubmitting ? "Processing Text..." : "Submit Text"}
        </button>
      </div>
    </div>
  );
}
