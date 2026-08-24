"use client";

/**
 * components/landing/HeroSection.tsx
 * ------------------------------------
 * Landing page hero with headline, subheading, and CTA buttons.
 * Framer Motion fade-in + slide-up animations per element.
 */

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

function fadeUp(delay: number = 0) {
  return {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] as [number, number, number, number] },
  };
}

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-white pt-20 pb-28 sm:pt-28 sm:pb-36">
      {/* Subtle grid background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, #e2e8f0 1px, transparent 0)",
          backgroundSize: "32px 32px",
          maskImage:
            "radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%)",
        }}
      />
      {/* Soft glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/4 h-96 w-96 rounded-full bg-indigo-100 opacity-60 blur-3xl"
      />

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        {/* Badge */}
        <motion.div {...fadeUp(0)} className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-4 py-1.5">
          <Sparkles className="h-3.5 w-3.5 text-indigo-600" aria-hidden="true" />
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-700">
            AI-Powered Placement Intelligence
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          {...fadeUp(0.1)}
          className="mb-6 text-5xl font-bold leading-tight tracking-tight text-slate-900 sm:text-6xl"
        >
          Transform Your Resume{" "}
          <span className="bg-gradient-to-r from-indigo-600 to-indigo-400 bg-clip-text text-transparent">
            Into Placement Intelligence
          </span>
        </motion.h1>

        {/* Subheading */}
        <motion.p
          {...fadeUp(0.2)}
          className="mb-10 mx-auto max-w-2xl text-lg leading-relaxed text-slate-500"
        >
          SkillFit analyzes your resume, extracts verified skills, identifies gaps, and generates
          a comprehensive readiness score — helping you land the placement you deserve.
        </motion.p>

        {/* CTAs */}
        <motion.div
          {...fadeUp(0.3)}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-7 py-3.5 text-sm font-semibold text-white shadow-md shadow-indigo-200 hover:bg-indigo-700 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-200"
          >
            Get Started Free
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-7 py-3.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 hover:border-slate-300 transition-all duration-200"
          >
            Sign In
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
