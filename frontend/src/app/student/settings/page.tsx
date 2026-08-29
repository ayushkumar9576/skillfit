export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
        <p className="text-slate-500">
          Manage your account preferences and application settings.
        </p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Coming Soon</h3>
        <p className="mt-2 text-sm text-slate-500">
          The Settings feature is currently under development.
        </p>
      </div>
    </div>
  );
}
