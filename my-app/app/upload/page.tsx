// "use client";
// import { useEffect, useState } from "react";
// import { useSearchParams } from "next/navigation";
// import { motion } from "framer-motion";

// export default function UploadPage() {
//   const searchParams = useSearchParams();
//   const filename = searchParams.get("file");
//   const [summary, setSummary] = useState<string | null>(null);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     if (!filename) return;

//     const fetchSummary = async () => {
//       try {
//         const res = await fetch(`/pdf_bot/processed-data?filename=${filename}`);
//         const data = await res.json();

//         // Combine all LLM extraction results into a single string
//         const summaryText = Object.entries(data.data.extracted_data || {})
//           .map(([k, v]) => `${k.toUpperCase()}: ${v}`)
//           .join("\n\n");

//         setSummary(summaryText);
//       } catch (err) {
//         console.error(err);
//         setSummary("Failed to fetch summary.");
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchSummary();
//   }, [filename]);

//   return (
//     <div className="min-h-screen flex flex-col items-center justify-start p-8 space-y-4">
//       <motion.h1
//         initial={{ opacity: 0, y: 10 }}
//         animate={{ opacity: 1, y: 0 }}
//         className="text-2xl font-semibold"
//       >
//         Contract Summary
//       </motion.h1>

//       {loading && <p className="text-neutral-500">Generating summary, please wait...</p>}

//       {!loading && summary && (
//         <pre className="bg-white shadow-lg rounded-xl p-6 w-full max-w-3xl whitespace-pre-wrap">
//           {summary}
//         </pre>
//       )}
//     </div>
//   );
// }

"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

interface ExtractedField {
  key: string;
  value: string;
  page: number | null;
  quote: string | null;
}

export default function UploadPage() {
  const searchParams = useSearchParams();
  const filename = searchParams.get("file");

  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [docSummary, setDocSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const processData = (rawData: any) => {
      const extracted =
        rawData?.data?.extracted_data || rawData?.extracted_data || {};
      const formattedFields: ExtractedField[] = [];
      Object.entries(extracted).forEach(([key, details]: [string, any]) => {
        if (key === "summary") {
          setDocSummary(details);
          return;
        }
        if (typeof details === "string") {
          formattedFields.push({
            key: key.replace(/_/g, " ").toUpperCase(),
            value: details,
            page: null,
            quote: null,
          });
        } else if (details && typeof details === "object") {
          formattedFields.push({
            key: key.replace(/_/g, " ").toUpperCase(),
            value: details.value || "Not Found",
            page: details.page || null,
            quote: details.quote || null,
          });
        }
      });

      setFields(formattedFields);
    };

    const getData = async () => {
      try {
        const storedData = sessionStorage.getItem("summary");
        if (storedData) {
          processData(JSON.parse(storedData));
        } else if (filename) {
          const res = await fetch(
            `/pdf_bot/processed-data?filename=${filename}`
          );
          const data = await res.json();
          processData(data);
        }
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    getData();
  }, [filename]);

  return (
    <div className="min-h-screen bg-slate-50 p-8 flex flex-col items-center">
      <div className="w-full max-w-3xl space-y-6">
        <header className="border-b pb-4">
          <h1 className="text-2xl font-bold text-slate-900">
            Document Analysis
          </h1>
          <p className="text-sm text-slate-500">File: {filename}</p>
        </header>

        {loading ? (
          <p className="text-center py-10 text-slate-400 animate-pulse">
            Analyzing document...
          </p>
        ) : (
          <>
            {docSummary && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-blue-600 text-white p-6 rounded-2xl shadow-lg shadow-blue-200"
              >
                <h2 className="text-xs font-bold uppercase tracking-widest mb-2 opacity-80">
                  AI Assessment
                </h2>
                <p className="text-lg leading-relaxed font-medium">
                  {docSummary}
                </p>
              </motion.div>
            )}
            <div className="grid gap-4">
              <h2 className="text-sm font-bold text-slate-400 uppercase mt-4">
                Extracted Metadata
              </h2>
              {fields.map((item) => (
                <div
                  key={item.key}
                  className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden"
                >
                  <h3 className="text-[10px] font-bold text-slate-400 uppercase mb-1">
                    {item.key}
                  </h3>
                  <p
                    className={`text-base font-semibold ${
                      item.value === "Not Found"
                        ? "text-slate-300"
                        : "text-slate-800"
                    }`}
                  >
                    {item.value}
                  </p>

                  {item.page && (
                    <span className="absolute top-4 right-4 bg-slate-100 text-slate-500 text-[10px] px-2 py-0.5 rounded font-bold">
                      PAGE {item.page}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
