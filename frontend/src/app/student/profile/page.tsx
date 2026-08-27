import ProfileEditor from "@/components/student/ProfileEditor";

export default function StudentProfilePage() {
  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Your Profile</h1>
        <p className="text-sm text-slate-500 mt-1">Manage your account details and professional presence.</p>
      </div>

      <ProfileEditor />
    </div>
  );
}
