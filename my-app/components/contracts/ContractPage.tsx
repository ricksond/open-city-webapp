"use client";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import axios from "axios";
import { FileText, Calendar, CheckSquare } from "lucide-react";

export default function VendorDetails() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchVendor = async () => {
      try {
        const res = await axios.get(
          "http://localhost:5000/info/vendors/ITRON%20INC"
        );

        console.log("API DATA:", res.data);
        setData(res.data);
      } catch (err: any) {
        const msg = err.response?.data?.error || "Failed to fetch vendor";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchVendor();
  }, []);

  if (loading) return <p className="text-center mt-10">Loading...</p>;
  if (error) return <p className="text-center text-red-500 mt-10">{error}</p>;
  const entitiesServed = data?.entities_served
    ? Array.isArray(data.entities_served)
      ? data.entities_served
      : Object.keys(data.entities_served)
    : [];

  const contracts = data?.contracts || [];

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-10">
      <div className="flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-2xl space-y-6"
        >
          <h1 className="text-2xl font-bold text-black">
            {data?.vendor_name || "N/A"}
          </h1>

          <div className="flex items-center gap-3">
            <FileText className="text-blue-500" />
            <p className="text-lg">
              Total Spend:{" "}
              <span className="font-semibold">${data?.total_spend ?? 0}</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <CheckSquare className="text-green-500" />
            <p className="text-lg">
              Contracts:{" "}
              <span className="font-semibold">{contracts.length}</span>
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

          <div className="bg-gray-100 p-4 rounded-xl">
            <h2 className="font-semibold mb-2">AI Summary</h2>
            <p className="text-gray-700">
              {data?.ai_summary || "No summary available"}
            </p>
          </div>
        </motion.div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {contracts.length > 0 ? (
          contracts.map((c: any, index: number) => (
            <motion.div
              key={c.contract_id || index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="rounded-xl border border-neutral-300 bg-gradient-to-r from-indigo-200 to-indigo-300 p-5 shadow hover:scale-105 transition-transform"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-lg tracking-wide">
                  {c.vendor_name || data.vendor_name}
                </h3>
                <CheckSquare className="w-5 h-5 text-green-500" />
              </div>

              <p className="text-sm text-black mb-3">
                {c.description || "No description"}
              </p>

              <div className="flex items-center text-sm text-black space-x-4">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-5 h-5 text-black" />
                  <span>
                    {c.start_date
                      ? new Date(c.start_date).toLocaleDateString()
                      : "N/A"}{" "}
                    -{" "}
                    {c.end_date
                      ? new Date(c.end_date).toLocaleDateString()
                      : "N/A"}
                  </span>
                </div>
              </div>
            </motion.div>
          ))
        ) : (
          <p className="text-center col-span-full text-gray-500">
            No contracts available
          </p>
        )}
      </div>
    </div>
  );
}
