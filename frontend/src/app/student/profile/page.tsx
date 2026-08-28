import ProfileEditor from "@/components/student/ProfileEditor";

export default function StudentProfilePage() {
  return (
    <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Your Profile</h1>
        <p className="text-sm text-slate-500 mt-2">Manage your academic details and professional presence.</p>
      </div>

      <ProfileEditor />
    </div>
  );
}
