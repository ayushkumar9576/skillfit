"use client";

/**
 * components/landing/WorkflowSection.tsx
 * ----------------------------------------
 * Step-by-step visual flow showing how SkillFit works.
 */

import { motion } from "framer-motion";
import { Upload, Cpu, Tag, BarChart2, MessageSquare } from "lucide-react";

const steps = [
  { icon: Upload, title: "Resume Upload", description: "Upload your resume in PDF format securely." },
  { icon: Cpu, title: "AI Analysis", description: "Our LLM pipeline processes and understands your resume." },
  { icon: Tag, title: "Skill Extraction", description: "Skills, projects, and experience are extracted with evidence." },
  { icon: BarChart2, title: "Readiness Assessment", description: "A composite score is generated across multiple dimensions." },
  { icon: MessageSquare, title: "Recommendations", description: "Receive personalized, actionable improvement suggestions." },
];

export default function WorkflowSection() {
  return (
    <section id="roadmap" className="bg-white py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-14 text-center"
        >
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-indigo-600">
            How It Works
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            From resume to readiness in minutes
          </h2>
        </motion.div>

        {/* Steps */}
        <div className="relative">
          {/* Connector line (desktop) */}
          <div
            aria-hidden="true"
            className="absolute left-1/2 top-8 hidden h-0.5 w-[calc(100%-8rem)] -translate-x-1/2 bg-gradient-to-r from-transparent via-slate-200 to-transparent lg:block"
          />

          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3 lg:grid-cols-5">
            {steps.map((step, index) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="flex flex-col items-center text-center"
              >
                {/* Step number + icon */}
                <div className="relative mb-5">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-indigo-100 bg-white shadow-md">
                    <step.icon className="h-6 w-6 text-indigo-600" aria-hidden="true" />
                  </div>
                  <div className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                    {index + 1}
                  </div>
                </div>
                <h3 className="mb-1.5 text-sm font-semibold text-slate-900">{step.title}</h3>
                <p className="text-xs leading-relaxed text-slate-500">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
