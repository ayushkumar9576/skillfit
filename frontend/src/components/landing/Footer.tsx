/**
 * components/landing/Footer.tsx
 * --------------------------------
 * Professional landing page footer.
 */

import Link from "next/link";
import { Zap } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-100 bg-white">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900 hover:opacity-80 transition-opacity">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600">
              <Zap className="h-3.5 w-3.5 text-white" aria-hidden="true" />
            </div>
            <span className="text-base tracking-tight">SkillFit</span>
          </Link>

          {/* Links */}
          <div className="flex items-center gap-6">
            <span className="text-xs text-slate-400 hover:text-slate-600 cursor-default transition-colors">
              About
            </span>
            <span className="text-xs text-slate-400 hover:text-slate-600 cursor-default transition-colors">
              Privacy
            </span>
            <span className="text-xs text-slate-400 hover:text-slate-600 cursor-default transition-colors">
              Contact
            </span>
          </div>

          {/* Copyright */}
          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} SkillFit. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
