"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { VendorCard, EntityCard } from "@/components/vendor/VendorCard";
import { Loader2, AlertCircle, Search } from "lucide-react";


export type SearchResult = 
  | { type: "vendor"; data: any }
  | { type: "entity"; data: any }
  | null;

export default function ProcurementPage() {
  const [result, setResult] = useState<SearchResult>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const targetSearchName = "Virginia Department of Transportation"; 
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setResult(null);
      try {
        try {
          const vendorRes = await axios.get(
            `http://localhost:5000/info/vendors/${encodeURIComponent(targetSearchName)}`
          );
          if (vendorRes.data && vendorRes.data.vendor_name) {
            setResult({ type: "vendor", data: vendorRes.data });
            setLoading(false);
            return; 
          }
        } catch (vendorErr) {
          console.log("Not found as a vendor. Trying as entity...");
        }
        try {
          const entityRes = await axios.get(
            `http://localhost:5000/info/entities/${encodeURIComponent(targetSearchName)}`
          );
          if (entityRes.data && entityRes.data.entity_name) {
            setResult({ type: "entity", data: entityRes.data });
            setLoading(false);
            return; 
          }
        } catch (entityErr) {
          console.log("Not found as an entity either.");
        }
        setError(`Could not find any vendor or entity named "${targetSearchName}".`);
      } catch (err) {
        setError("Failed to connect to the server. Is Flask running?");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [targetSearchName]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen w-full bg-gradient-to-br from-slate-50 to-slate-200 p-6"
    >
      <header className="mb-8 max-w-4xl">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          <Search className="w-8 h-8 text-indigo-600" />
          Procurement Intelligence
        </h1>
        <p className="text-slate-600 mt-2">
          Searching for: <span className="font-semibold text-slate-800">{targetSearchName}</span>
        </p>
      </header>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 max-w-4xl">
          <Loader2 className="w-10 h-10 animate-spin text-indigo-600 mb-2" />
          <p className="text-slate-500 font-medium">Scanning Vendors & Entities...</p>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 p-4 max-w-4xl bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      ) : (
        <div className="max-w-4xl">
          {result?.type === "vendor" && <VendorCard data={result.data} />}
          {result?.type === "entity" && <EntityCard data={result.data} />}
        </div>
      )}
    </motion.div>
  );
}