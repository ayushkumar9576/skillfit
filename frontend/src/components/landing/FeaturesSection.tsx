"use client";

/**
 * components/landing/FeaturesSection.tsx
 * ----------------------------------------
 * Four feature cards describing SkillFit's core capabilities.
 */

import { motion } from "framer-motion";
import { FileSearch, Brain, TrendingUp, Lightbulb } from "lucide-react";

const features = [
  {
    icon: FileSearch,
    title: "Resume Analysis",
    description:
      "Automatically parse and extract structured data from your resume — sections, skills, projects, and experience — with high accuracy.",
  },
  {
    icon: Brain,
    title: "Skill Intelligence",
    description:
      "Cross-reference your extracted skills against industry requirements to get evidence-backed proficiency assessments.",
  },
  {
    icon: TrendingUp,
    title: "Placement Readiness",
    description:
      "Receive a composite readiness score across multiple dimensions — technical, leadership, academics, and more.",
  },
  {
    icon: Lightbulb,
    title: "AI Insights",
    description:
      "Get personalized, actionable recommendations powered by an LLM pipeline trained on real placement data.",
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="bg-slate-50 py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-14 text-center"
        >
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-indigo-600">
            Core Capabilities
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Built for serious placement prep
          </h2>
          <p className="mt-4 mx-auto max-w-2xl text-base text-slate-500">
            Every feature is designed to give you a data-driven edge in your placement journey.
          </p>
        </motion.div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.08 }}
              whileHover={{ y: -4 }}
              className="group rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow duration-200 hover:shadow-md"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 group-hover:bg-indigo-100 transition-colors">
                <feature.icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h3 className="mb-2 text-sm font-semibold text-slate-900">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-slate-500">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
