import ActionCenter from "@/components/dashboards/ActionCenter";
import StatCard from "@/components/dashboards/StatCard";
import {motion} from 'framer-motion';

export default function Home() {
  return (
    <div className="space-y-6 mt-4">
      <ActionCenter />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Active Contracts" value={124} />
        <StatCard title="Expiring Soon" value={8} />
        <StatCard title="Savings Opportunities" value={124} />
      </div>
    </div>
  );
}
