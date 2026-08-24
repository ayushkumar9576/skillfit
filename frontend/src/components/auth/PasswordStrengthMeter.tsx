"use client";

/**
 * components/auth/PasswordStrengthMeter.tsx
 * ------------------------------------------
 * Live password strength checklist component.
 * Shows real-time pass/fail indicators for each requirement.
 */

import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface PasswordRule {
  label: string;
  test: (password: string) => boolean;
}

const RULES: PasswordRule[] = [
  { label: "At least 12 characters", test: (p) => p.length >= 12 },
  { label: "One uppercase letter (A-Z)", test: (p) => /[A-Z]/.test(p) },
  { label: "One lowercase letter (a-z)", test: (p) => /[a-z]/.test(p) },
  { label: "One number (0-9)", test: (p) => /[0-9]/.test(p) },
  { label: "One special character (!@#$...)", test: (p) => /[^A-Za-z0-9]/.test(p) },
];

function getStrength(password: string): { score: number; label: string; color: string } {
  const passed = RULES.filter((r) => r.test(password)).length;
  if (passed <= 1) return { score: passed, label: "Weak", color: "bg-red-500" };
  if (passed <= 3) return { score: passed, label: "Fair", color: "bg-amber-500" };
  if (passed === 4) return { score: passed, label: "Strong", color: "bg-emerald-500" };
  return { score: passed, label: "Very Strong", color: "bg-emerald-600" };
}

interface PasswordStrengthMeterProps {
  password: string;
}

export default function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps) {
  if (!password) return null;

  const strength = getStrength(password);

  return (
    <div className="mt-2 space-y-2" aria-live="polite" aria-label="Password strength">
      {/* Strength bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-300", strength.color)}
            style={{ width: `${(strength.score / RULES.length) * 100}%` }}
          />
        </div>
        <span className={cn(
          "text-xs font-medium",
          strength.score <= 1 ? "text-red-600" : strength.score <= 3 ? "text-amber-600" : "text-emerald-600"
        )}>
          {strength.label}
        </span>
      </div>

      {/* Rule checklist */}
      <ul className="space-y-1">
        {RULES.map((rule) => {
          const passed = rule.test(password);
          return (
            <li key={rule.label} className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-4 w-4 shrink-0 items-center justify-center rounded-full",
                  passed ? "bg-emerald-100 text-emerald-600" : "bg-slate-100 text-slate-400"
                )}
                aria-hidden="true"
              >
                {passed ? <Check className="h-2.5 w-2.5" /> : <X className="h-2.5 w-2.5" />}
              </span>
              <span className={cn("text-xs", passed ? "text-emerald-700" : "text-slate-500")}>
                {rule.label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
