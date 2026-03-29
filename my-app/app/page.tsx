import ActionCenter from "@/components/dashboards/ActionCenter";
import StatCard from "@/components/dashboards/StatCard";
import UploadPage from "@/components/upload/UploadPage";
import ProtectedRoute from "@/components/ProtectionRoute";

export default function Home() {
  return (
    <ProtectedRoute>
    <div className="space-y-6 mt-4 bg-gradient-to-r from-indigo-100 to-emerald-100 min-h-screen">
      <ActionCenter />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Active Contracts" value={124} />
        <StatCard title="Expiring Soon" value={8} />
        <StatCard title="Savings Opportunities" value={124} />
           <UploadPage />
      </div>
    </div>
    </ProtectedRoute>
  );
}
