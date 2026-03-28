"use client";

import { motion } from "framer-motion";
import {VendorCard}from "@/components/vendor/VendorCard";

const vendors = [
  { name: "Itron Inc", totalSpend: 72588.48, contractsCount: 4 },
  { name: "Acme Corp", totalSpend: 43000.0, contractsCount: 2 },
  { name: "Tech Solutions", totalSpend: 98000.5, contractsCount: 5 },
];

export default function VendorsPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen w-full bg-gradient-to-br from-green-100 to-blue-300 p-6"
    >
      <h1 className="text-3xl font-bold mb-6">Vendors</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {vendors.map((v) => (
          <VendorCard
            key={v.name}
            vendorName={v.name}
            totalSpend={v.totalSpend}
            contractCount={v.contractsCount}
          />
        ))}
      </div>
    </motion.div>
  );
}