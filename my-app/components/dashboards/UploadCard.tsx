"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { UploadCloud } from "lucide-react"; // Make sure this works

export default function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white shadow-2xl rounded-3xl p-12 max-w-sm w-full flex flex-col items-center text-center cursor-pointer transition"
      >
        <UploadCloud className="w-16 h-16 text-green-500 mb-4 animate-bounce" />
        <h2 className="text-2xl font-semibold mb-2">Upload Contracts</h2>
        <p className="text-neutral-500 mb-6">
          Click below to go to the Upload Page and manage your contract documents.
        </p>
        <Link href="/upload">
            Go to Upload Page
        </Link>
      </motion.div>
    </div>
  );
}