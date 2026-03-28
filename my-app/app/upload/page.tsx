"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

export default function UploadPage() {
  const searchParams = useSearchParams();
  const filename = searchParams.get("file");
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!filename) return;

    const fetchSummary = async () => {
      try {
        const res = await fetch(`/pdf_bot/processed-data?filename=${filename}`);
        const data = await res.json();

        // Combine all LLM extraction results into a single string
        const summaryText = Object.entries(data.data.extracted_data || {})
          .map(([k, v]) => `${k.toUpperCase()}: ${v}`)
          .join("\n\n");

        setSummary(summaryText);
      } catch (err) {
        console.error(err);
        setSummary("Failed to fetch summary.");
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [filename]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-start p-8 space-y-4">
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-semibold"
      >
        Contract Summary
      </motion.h1>

      {loading && <p className="text-neutral-500">Generating summary, please wait...</p>}

      {!loading && summary && (
        <pre className="bg-white shadow-lg rounded-xl p-6 w-full max-w-3xl whitespace-pre-wrap">
          {summary}
        </pre>
      )}
    </div>
  );
}