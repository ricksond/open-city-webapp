"use client";

import { motion } from "framer-motion";
import { VendorCard } from "@/components/vendor/VendorCard";


type Contract = {
  contract_id: string;
  description: string;
  start_date: string;
  end_date: string;
  is_expiring_soon: boolean;
};

type Entity = {
  po_count: number;
  spend: number;
};

type Vendor = {
  vendor_name: string;
  total_spend: number;
  contracts: Contract[];
  entities_served: Record<string, Entity>;
};

/* ---------- DATA ---------- */
const vendors: Vendor[] = [
  {
    vendor_name: "Itron Inc",
    total_spend: 72588.48,
    contracts: [
      {
        contract_id: "15000014256",
        description: "Gas and Water automated parts",
        start_date: "2011-01-31",
        end_date: "2022-03-04",
        is_expiring_soon: false,
      },
      {
        contract_id: "24000006477",
        description:
          "Sole Source Award; Two Year Initial Term; Five Two-Year Renewal Options",
        start_date: "2024-03-28",
        end_date: "2028-03-27",
        is_expiring_soon: false,
      },
    ],
    entities_served: {
      "Virginia Department of Energy": {
        po_count: 2,
        spend: 72588.48,
      },
    },
  },
  {
    vendor_name: "Acme Corp",
    total_spend: 43000,
    contracts: [
      {
        contract_id: "AC-001",
        description: "IT hardware supply",
        start_date: "2023-01-01",
        end_date: "2026-01-01",
        is_expiring_soon: true,
      },
    ],
    entities_served: {
      "City IT Department": {
        po_count: 3,
        spend: 43000,
      },
    },
  },
];

/* ---------- PAGE ---------- */
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
            key={v.vendor_name}
            vendorName={v.vendor_name}
            totalSpend={v.total_spend}
            contracts={v.contracts}
            entities={v.entities_served || {}} // 🔥 safety fallback
          />
        ))}
      </div>
    </motion.div>
  );
}