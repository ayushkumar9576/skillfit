"use client";

import { useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import CreateStudentForm from "./_components/CreateStudentForm";
import CreateFacultyForm from "./_components/CreateFacultyForm";
import BulkImportStudentForm from "./_components/BulkImportStudentForm";
import BulkImportFacultyForm from "./_components/BulkImportFacultyForm";

export default function AdminUsersPage() {
  const [activeTab, setActiveTab] = useState<"student" | "faculty" | "bulk-student" | "bulk-faculty" | "search">("student");

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <PageHeader 
        title="User Management" 
        description="Provision accounts for students and faculty members."
      />

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="flex border-b border-slate-200 bg-slate-50 flex-wrap">
          <button
            onClick={() => setActiveTab("student")}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "student" ? "border-indigo-600 text-indigo-600 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Create Student
          </button>
          <button
            onClick={() => setActiveTab("bulk-student")}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "bulk-student" ? "border-indigo-600 text-indigo-600 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Bulk Import Students
          </button>
          <button
            onClick={() => setActiveTab("faculty")}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "faculty" ? "border-indigo-600 text-indigo-600 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Create Faculty
          </button>
          <button
            onClick={() => setActiveTab("bulk-faculty")}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "bulk-faculty" ? "border-indigo-600 text-indigo-600 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Bulk Import Faculty
          </button>
          <button
            onClick={() => setActiveTab("search")}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "search" ? "border-indigo-600 text-indigo-600 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Search Users
          </button>
        </div>

        <div className="p-6 md:p-8">
          {activeTab === "student" && <CreateStudentForm />}
          {activeTab === "bulk-student" && <BulkImportStudentForm />}
          {activeTab === "faculty" && <CreateFacultyForm />}
          {activeTab === "bulk-faculty" && <BulkImportFacultyForm />}
          {activeTab === "search" && (
            <div className="text-center py-12">
              <div className="text-slate-400 mb-2">🔍</div>
              <h3 className="text-lg font-bold text-slate-900">User Search</h3>
              <p className="text-slate-500 mt-1">User search functionality is coming soon.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
