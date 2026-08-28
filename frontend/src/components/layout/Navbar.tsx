"use client";

/**
 * components/layout/Navbar.tsx
 * ----------------------------
 * Sticky landing page navbar with blur backdrop.
 * Shows logo, nav links, and CTA buttons.
 * Collapses to mobile menu on small screens.
 */

import Link from "next/link";
import { useState } from "react";
import { Menu, X, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-100 bg-white/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6" aria-label="Main navigation">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900 hover:opacity-80 transition-opacity">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600">
            <Zap className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <span className="text-lg tracking-tight">SkillFit</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-8 md:flex">
          <Link
            href="#features"
            className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            Features
          </Link>
          <Link
            href="#roadmap"
            className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            Roadmap
          </Link>
        </div>

        {/* Desktop CTA */}
        <div className="hidden items-center gap-3 md:flex">
          <Link
            href="/auth/login"
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 transition-colors shadow-sm"
          >
            Access Portal
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <button
          type="button"
          className="flex md:hidden items-center justify-center rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition-colors"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMenuOpen}
        >
          {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobile dropdown */}
      <div
        className={cn(
          "overflow-hidden border-t border-slate-100 transition-all duration-200 md:hidden",
          isMenuOpen ? "max-h-64" : "max-h-0"
        )}
      >
        <div className="flex flex-col gap-1 px-6 py-4">
          <Link
            href="#features"
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
            onClick={() => setIsMenuOpen(false)}
          >
            Features
          </Link>
          <Link
            href="#roadmap"
            className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
            onClick={() => setIsMenuOpen(false)}
          >
            Roadmap
          </Link>
          <div className="mt-2 flex flex-col gap-2 border-t border-slate-100 pt-2">
            <Link
              href="/auth/login"
              className="rounded-lg bg-indigo-600 px-3 py-2 text-center text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Access Portal
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
