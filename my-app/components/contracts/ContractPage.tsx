"use client";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import axios from "axios";
import { FileText, Calendar, CheckSquare, Building, ShoppingCart } from "lucide-react";

interface ContractsPageProps {
  name: string;
}

export default function ContractsPage({ name }: ContractsPageProps) {
  const [data, setData] = useState<any>(null);
  const [type, setType] = useState<"vendor" | "entity" | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError("");
      
      try {
        const vendorRes = await axios.get(`http://localhost:5000/info/vendors/${encodeURIComponent(name)}`);
        
        // Defensive check: Sometimes APIs return 200 OK but with an error message
        if (vendorRes.data && vendorRes.data.error) throw new Error("Vendor not found");
        
        setData(vendorRes.data);
        setType("vendor");
      } catch (vendorErr: any) {
        console.log("Not found as vendor, trying entity...");
        
        try {
          const entityRes = await axios.get(`http://localhost:5000/info/entities/${encodeURIComponent(name)}`);
          console.log(entityRes);
          setData(entityRes.data);
          setType("entity");
        } catch (entityErr: any) {
          setError("Failed to fetch details. The name is neither a valid vendor nor an entity.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (name) fetchData();
  }, [name]);

  if (loading) return <p className="text-center mt-10 text-lg animate-pulse">Loading data...</p>;
  if (error) return <p className="text-center text-red-500 mt-10 text-lg">{error}</p>;
  if (!data) return null;

  const entitiesServed = data?.entities_served
    ? Array.isArray(data.entities_served)
      ? data.entities_served
      : Object.keys(data.entities_served)
    : [];
  const contracts = data?.contracts || [];
  const vendorsUsed = data?.vendors_used || {};
  const vendorNames = Object.keys(vendorsUsed);

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-10">
      <div className="flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-2xl space-y-6"
        >
          <div className="flex items-center gap-3">
            {type === "vendor" ? <Building className="text-indigo-600 w-8 h-8" /> : <Building className="text-emerald-600 w-8 h-8" />}
            <h1 className="text-2xl font-bold text-black">
              {/* Safely fetch title */}
              {type === "vendor" ? (data?.vendor_name || "Unknown Vendor") : (data?.entity_name || "Unknown Entity")}
              <span className="ml-3 text-sm font-normal text-gray-500 bg-gray-100 px-3 py-1 rounded-full uppercase tracking-wide">
                {type}
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <FileText className="text-blue-500" />
            <p className="text-lg">
              Total Spend:{" "}
              <span className="font-semibold">
                {/* Safely format total spend */}
                ${data?.total_spend ? data.total_spend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "0.00"}
              </span>
            </p>
          </div>
          {type === "vendor" && (
            <>
              <div className="flex items-center gap-3">
                <CheckSquare className="text-green-500" />
                <p className="text-lg">
                  Contracts: <span className="font-semibold">{contracts.length}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="text-purple-500" />
                <p className="text-lg">
                  Entities Served:{" "}
                  <span className="font-semibold">
                    {entitiesServed.length > 0 ? entitiesServed.join(", ") : "N/A"}
                  </span>
                </p>
              </div>
            </>
          )}
          {type === "entity" && (
            <div className="flex items-center gap-3">
              <ShoppingCart className="text-purple-500" />
              <p className="text-lg">
                Unique Vendors Used: <span className="font-semibold">{vendorNames.length}</span>
              </p>
            </div>
          )}
          <div className="bg-gray-100 p-4 rounded-xl">
            <h2 className="font-semibold mb-2">AI Summary</h2>
            <div className="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">
              {data?.ai_summary || "No summary available"}
            </div>
          </div>
        </motion.div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {type === "vendor" && (
          contracts.length > 0 ? (
            contracts.map((c: any, index: number) => (
              <motion.div
                key={c.contract_id || index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="rounded-xl border border-neutral-300 bg-gradient-to-r from-indigo-100 to-indigo-200 p-5 shadow hover:scale-105 transition-transform"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg tracking-wide truncate">
                    {c.vendor_name || data?.vendor_name || "Unknown"}
                  </h3>
                  <CheckSquare className="w-5 h-5 text-indigo-500 flex-shrink-0" />
                </div>
                <p className="text-sm text-black mb-3 line-clamp-3">
                  {c.description || "No description"}
                </p>
                <div className="flex items-center text-sm text-black space-x-4">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4 text-black" />
                    <span>
                      {c.start_date ? new Date(c.start_date).toLocaleDateString() : "N/A"} -{" "}
                      {c.end_date ? new Date(c.end_date).toLocaleDateString() : "N/A"}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))
          ) : (
            <p className="text-center col-span-full text-gray-500">No contracts available</p>
          )
        )}
        
        {type === "entity" && (
          vendorNames.length > 0 ? (
            vendorNames.map((vendorName, index) => {
              const vendorData = vendorsUsed[vendorName];
              
              // Calculate total spend safely if it exists, otherwise show N/A
              const displaySpend = vendorData?.total_spend_with_vendor 
                  ? `$${vendorData.total_spend_with_vendor.toLocaleString()}` 
                  : "N/A";

              return (
                <motion.div
                  key={vendorData?.vendor_id || index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.05 }}
                  className="rounded-xl border border-neutral-300 bg-gradient-to-r from-emerald-100 to-emerald-200 p-5 shadow hover:scale-105 transition-transform"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-lg tracking-wide capitalize truncate" title={vendorName}>
                      {vendorName}
                    </h3>
                    <Building className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  </div>
                  
                  <div className="space-y-2 mt-4">
                    <p className="text-sm text-black">
                      <span className="font-semibold">Total Spend:</span> {displaySpend}
                    </p>
                    <p className="text-sm text-black">
                      <span className="font-semibold">Items Bought:</span> {vendorData?.items_bought?.length || 0} transactions
                    </p>
                    
                    {vendorData?.items_bought && vendorData.items_bought.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-emerald-300/50">
                        <p className="text-xs text-black/80 font-medium mb-1">Recent Purchase:</p>
                        <p className="text-xs text-black/70 line-clamp-2">
                          {vendorData.items_bought[0].item_description || "No description provided"}
                        </p>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })
          ) : (
            <p className="text-center col-span-full text-gray-500">No vendor data available for this entity.</p>
          )
        )}
      </div>
    </div>
  );
}