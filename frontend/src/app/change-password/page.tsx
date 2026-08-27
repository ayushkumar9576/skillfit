import ChangePasswordForm from "@/components/auth/ChangePasswordForm";
import { KeyRound } from "lucide-react";

export default function ChangePasswordPage() {
  return (
    <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-md">
      <div className="mb-8 flex flex-col items-center text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50">
          <KeyRound className="h-6 w-6 text-indigo-600" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">Change Your Password</h1>
        <p className="mt-2 text-sm text-slate-500">
          For your security, please change your temporary password to a permanent one before continuing.
        </p>
      </div>

      <ChangePasswordForm />
    </div>
  );
}
