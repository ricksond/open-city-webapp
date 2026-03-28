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
  Sparkles,
  Briefcase,
  ShoppingCart,
} from "lucide-react";

export function VendorCard({ data }: { data: any }) {
  const [open, setOpen] = useState(false);
  const contracts = data.contracts || [];
  const expiringCount = contracts.filter((c: any) => c.is_expiring_soon).length;

  return (
    <motion.div
      layout
      className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
    >
      <div
        onClick={() => setOpen(!open)}
        className="p-6 cursor-pointer hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Briefcase className="w-6 h-6 text-indigo-700" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              {data.vendor_name}
            </h2>
          </div>
          <div
            className={`p-2 rounded-full bg-slate-100 transition-transform ${
              open ? "rotate-180" : ""
            }`}
          >
            <ChevronDown className="w-5 h-5 text-slate-600" />
          </div>
        </div>

        <div className="flex flex-wrap gap-6 text-sm">
          <div className="flex flex-col">
            <span className="text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              Total Earned
            </span>
            <span className="flex items-center gap-1 text-lg font-semibold text-emerald-600">
              <DollarSign className="w-4 h-4" />
              {data.total_spend?.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              Active Contracts
            </span>
            <span className="flex items-center gap-1 text-lg font-semibold text-slate-800">
              <FileText className="w-4 h-4" />
              {contracts.length}
            </span>
          </div>
          {expiringCount > 0 && (
            <div className="flex flex-col">
              <span className="text-red-500 uppercase text-[10px] font-bold tracking-wider">
                Alerts
              </span>
              <span className="flex items-center gap-1 text-lg font-semibold text-red-600">
                <AlertTriangle className="w-4 h-4" />
                {expiringCount} Expiring
              </span>
            </div>
          )}
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-100 bg-slate-50/50"
          >
            <div className="p-6 space-y-8">
              {data.ai_summary && (
                <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 text-indigo-700">
                    <Sparkles className="w-4 h-4" />
                    <h3 className="font-bold text-sm uppercase tracking-tight">
                      AI Executive Summary
                    </h3>
                  </div>
                  <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
                    {data.ai_summary}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
export function EntityCard({ data }: { data: any }) {
  const [open, setOpen] = useState(false);
  const vendors = data.vendors_used || {};
  const vendorCount = Object.keys(vendors).length;

  return (
    <motion.div
      layout
      className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
    >
      <div
        onClick={() => setOpen(!open)}
        className="p-6 cursor-pointer hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Building2 className="w-6 h-6 text-blue-700" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">
              {data.entity_name}
            </h2>
          </div>
          <div
            className={`p-2 rounded-full bg-slate-100 transition-transform ${
              open ? "rotate-180" : ""
            }`}
          >
            <ChevronDown className="w-5 h-5 text-slate-600" />
          </div>
        </div>

        <div className="flex flex-wrap gap-6 text-sm">
          <div className="flex flex-col">
            <span className="text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              Total Spend
            </span>
            <span className="flex items-center gap-1 text-lg font-semibold text-blue-600">
              <DollarSign className="w-4 h-4" />
              {data.total_spend?.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              Unique Vendors Used
            </span>
            <span className="flex items-center gap-1 text-lg font-semibold text-slate-800">
              <Briefcase className="w-4 h-4" />
              {vendorCount}
            </span>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-100 bg-slate-50/50"
          >
            <div className="p-6 space-y-8">
              {data.ai_summary && (
                <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 text-blue-700">
                    <Sparkles className="w-4 h-4" />
                    <h3 className="font-bold text-sm uppercase tracking-tight">
                      AI Procurement Analysis
                    </h3>
                  </div>
                  <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
                    {data.ai_summary}
                  </p>
                </div>
              )}
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase mb-4 border-b pb-2">
                  Top Vendors & Purchases
                </h3>
                <div className="space-y-4">
                  {Object.entries(vendors).map(
                    ([vendorName, vendorData]: [string, any]) => (
                      <div
                        key={vendorName}
                        className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm"
                      >
                        <div className="flex justify-between items-start mb-3 border-b border-slate-100 pb-2">
                          <div>
                            <h4 className="font-bold text-slate-800">
                              {vendorName}
                            </h4>
                            <span className="text-[10px] font-mono text-slate-400">
                              ID: {vendorData.vendor_id}
                            </span>
                          </div>
                          <span className="text-sm font-bold text-emerald-600">
                            $
                            {vendorData.total_spend_with_vendor?.toLocaleString()}
                          </span>
                        </div>
                        <div className="space-y-2">
                          {vendorData.items_bought?.map(
                            (item: any, idx: number) => (
                              <div
                                key={idx}
                                className="flex flex-col gap-1 text-xs text-slate-600 bg-slate-50 p-2 rounded"
                              >
                                <div className="flex justify-between font-medium text-slate-800">
                                  <span className="truncate w-3/4">
                                    {item.item_description}
                                  </span>
                                  <span>
                                    ${item.total_cost?.toLocaleString()}
                                  </span>
                                </div>
                                <div className="flex items-center gap-3 text-[10px] text-slate-500">
                                  <span className="flex items-center gap-1">
                                    <ShoppingCart className="w-3 h-3" /> Qty:{" "}
                                    {item.quantity}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Calendar className="w-3 h-3" /> {item.date}
                                  </span>
                                  <span>PO: {item.po_number}</span>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
