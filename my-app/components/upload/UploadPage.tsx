"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { UploadCloud, FileText, X } from "lucide-react";

export default function UploadCard() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleBrowseClick = () => fileInputRef.current?.click();

  const handleFiles = (newFiles: FileList | null) => {
    if (!newFiles) return;
    const pdfs = Array.from(newFiles).filter((f) => f.type === "application/pdf");
    setFiles(pdfs);
  };

  const removeFile = (index: number) => setFiles((prev) => prev.filter((_, i) => i !== index));

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error("Please select at least one PDF.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    files.forEach((f) => formData.append("file", f));

    try {
      const res = await fetch("/pdf_bot/process", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();

      // Redirect to /upload page with the filename
      const filename = encodeURIComponent(data.data.filename);
      router.push(`/upload?file=${filename}`);
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Something went wrong");
    } finally {
      setUploading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl shadow-lg p-6 flex flex-col"
    >
      <h3 className="text-lg font-semibold mb-2">Upload PDF Contracts</h3>
      <p className="text-sm text-neutral-500 mb-4">
        Drag & drop or browse PDF files to extract summaries.
      </p>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFiles(e.dataTransfer.files);
        }}
        className="flex flex-col items-center justify-center border-2 border-dashed border-neutral-300 rounded-xl p-4 mb-4 cursor-pointer hover:border-green-400 transition"
      >
        <UploadCloud className="w-12 h-12 text-green-500 mb-2 animate-bounce" />
        <p className="text-sm text-neutral-500">Drag & drop PDFs here or click browse</p>
        <button
          type="button"
          onClick={handleBrowseClick}
          className="mt-2 px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-semibold hover:bg-green-600 transition"
        >
          Browse Files
        </button>
        <input
          type="file"
          multiple
          accept="application/pdf"
          ref={fileInputRef}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="mb-4">
          {files.map((file, idx) => (
            <div
              key={idx}
              className="flex justify-between items-center bg-neutral-100 rounded-md p-2 mb-2"
            >
              <FileText className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium">{file.name}</span>
              <button onClick={() => removeFile(idx)}>
                <X className="w-4 h-4 text-red-500" />
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading}
        className="mt-auto px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition disabled:opacity-50"
      >
        {uploading ? "Uploading & Processing..." : "Upload & Process"}
      </button>
    </motion.div>
  );
}