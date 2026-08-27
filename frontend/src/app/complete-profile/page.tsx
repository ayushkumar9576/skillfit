import CompleteProfileForm from "@/components/auth/CompleteProfileForm";
import { UserCircle } from "lucide-react";

export default function CompleteProfilePage() {
  return (
    <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-md sm:p-10">
      <div className="mb-8 flex flex-col items-center text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50">
          <UserCircle className="h-8 w-8 text-indigo-600" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Complete Your Profile</h1>
        <p className="mt-2 text-sm text-slate-500 max-w-md">
          Tell us a bit more about yourself to personalize your SkillFit experience. You can always update these details later.
        </p>
      </div>

      <CompleteProfileForm />
    </div>
  );
}
