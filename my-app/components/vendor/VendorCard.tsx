"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DollarSign,
  FileText,
  Calendar,
  AlertTriangle,
  ChevronDown,
  Building2,
} from "lucide-react";

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

interface VendorCardProps {
  vendorName: string;
  totalSpend: number;
  contracts: Contract[];
  entities: Record<string, Entity>;
}

export function VendorCard({
  vendorName,
  totalSpend,
  contracts,
  entities,
}: VendorCardProps) {
  const [open, setOpen] = useState(false);

  // 🔥 derived insights (important for scoring)
  const expiringCount = contracts.filter(c => c.is_expiring_soon).length;
  const soleSourceCount = contracts.filter(c =>
    c.description.toLowerCase().includes("sole source")
  ).length;

  return (
    <motion.div
      layout
      className="rounded-xl border border-neutral-700 bg-gradient-to-r from-indigo-300 to-indigo-500 p-5 shadow-lg"
    >
      {/* HEADER */}
      <div onClick={() => setOpen(!open)} className="cursor-pointer">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">{vendorName}</h2>
          <ChevronDown
            className={`transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>

        <div className="flex flex-wrap gap-4 mt-3 text-sm text-black">
          <span className="flex items-center gap-1">
            <DollarSign className="w-4 h-4" />
            ${totalSpend.toLocaleString()}
          </span>

          <span className="flex items-center gap-1">
            <FileText className="w-4 h-4" />
            {contracts.length} Contracts
          </span>

          {expiringCount > 0 && (
            <span className="flex items-center gap-1 text-red-600">
              <AlertTriangle className="w-4 h-4" />
              {expiringCount} Expiring
            </span>
          )}

          {soleSourceCount > 0 && (
            <span className="text-yellow-800 font-medium">
              ⚠ {soleSourceCount} Sole Source
            </span>
          )}
        </div>
      </div>

      {/* EXPAND SECTION */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-5 space-y-5"
          >
            {/* CONTRACTS */}
            <div>
              <h3 className="font-semibold mb-2">Contracts</h3>
              <div className="space-y-3">
                {contracts.map((c) => (
                  <div
                    key={c.contract_id}
                    className="p-3 rounded-lg bg-white/30 backdrop-blur"
                  >
                    <p className="font-medium text-sm">{c.contract_id}</p>
                    <p className="text-xs">{c.description}</p>

                    <div className="flex items-center gap-2 text-xs mt-2">
                      <Calendar className="w-3 h-3" />
                      {new Date(c.start_date).toLocaleDateString()} →{" "}
                      {new Date(c.end_date).toLocaleDateString()}
                    </div>

                    {c.is_expiring_soon && (
                      <p className="text-red-600 text-xs mt-1">
                        Expiring Soon
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* ENTITIES */}
            <div>
              <h3 className="font-semibold mb-2">Entities Served</h3>
              <div className="space-y-2">
                {Object.entries(entities).map(([name, data]) => (
                  <div
                    key={name}
                    className="flex justify-between text-sm bg-white/30 p-2 rounded"
                  >
                    <span className="flex items-center gap-1">
                      <Building2 className="w-4 h-4" />
                      {name}
                    </span>
                    <span>
                      ${data.spend.toLocaleString()} • {data.po_count} POs
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}