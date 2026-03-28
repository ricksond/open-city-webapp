"use client";
import {useState,useRef} from "react"
import React from "react";
import { AnimatePresence,motion } from "framer-motion";
import toast, { Toaster } from "react-hot-toast";
import { UploadCloud,FileText, X } from "lucide-react";


export default function UploadPage(){
    const [files,setFiles]=useState<File[]>([]);
    const [dragging,setDragging]=useState(false);
    const [uploading,setUploading]=useState(false);
    const fileInputRef=useRef<HTMLInputElement>(null);

    const handleBrowseClick=()=>{
        fileInputRef.current?.click();
    }
    // Handle files
    const handleFiles=(newfiles:FileList|null)=>{
        if(!newfiles) return;
        const fileArray=Array.from(newfiles).filter((file)=>file.type === "application/pdf");
        setFiles((prev)=>[...prev,...fileArray]);
    };

    // Handle drops
    const handleDrops=(e:React.DragEvent<HTMLDivElement>)=>{
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
    }
    // Remove File
    const removeFile=(index:number)=>{
        setFiles((prev)=>prev.filter((_,i)=>i!==index));
    };
    // Upload files
    const handleUpload=async()=>{
        if(files.length===0) {
            toast.error("No files to Upload");
            return;
        }
        setUploading(true);
        // animate or mock api call
        await new Promise((res)=>setTimeout(res,500));

        setUploading(false);
        setFiles([]);
        toast.success("Files uploaded successfully");
    };

    return (
        <motion.div className="min-h-screen w-full bg-linear-to-br from-green-100 to-blue-300">
        <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.8}} className="max-w-2xl mx-auto px-4 py-12">
            <Toaster position="top-right" />

            <h1 className="text-4xl font-medium opacity-80 text-black tracking-wider text-center">Upload Contract Documents</h1>
            <p className="text-neutral-500 text-center mb-8">Drag and drop contracts here or click the button below  to select files
                Make sure each file is a PDF and valid contract document
            </p>
            <motion.div
            onDragOver={(e)=>{ 
                e.preventDefault(); 
                setDragging(true);}}
            onDragLeave={()=>{
                setDragging(false);
            }}  
            onDrop={handleDrops}
            whileHover={{scale:1.02}}
            initial={{opacity:0,y:30}}
            animate={{opacity:1,y:0}}
            className={`relative flex flex-col items-center justify-center border-4 border-green rounded-3xl p-12 cursor-pointer transition-colors ${dragging ? "border-green-400 bg-green-900/20" : "border-neutral-300 hover:border-green-400 bg-neutral-900/20"}`}>
                <UploadCloud className="w-16 h-16 text-green-400 mb-4  animate-bounce" />
                <p className="text-black text-lg font-semibold tracking-widest mb-2">Drag and Drop PDF Contracts Here</p>
                <p className="text-neutral-500 text-sm mb-4 tracking-widest">or Click To Browse Files</p>
                <button
                   type="button"
                   onClick={handleBrowseClick}
                   className="flex items-center gap-2 px-6 py-3 rounded-xl bg-green-500 text-white font-semibold hover:bg-green-600 transition shadow-lg"
                    >
                    <UploadCloud className="w-5 h-5" /> {uploading ? "Uploading...": "Browse Files"}
                </button>
                  <input
                  type="file"
                  multiple
                  ref={fileInputRef}
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) => handleFiles(e.target.files)}
                  />
            </motion.div>
            <AnimatePresence>
                {files.length > 0 && (
                    <motion.div
                    initial={{opacity:0,y:20}}
                    animate={{opacity:1,y:0}}
                    exit={{opacity:0,y:-20}}
                    className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4"
                    >
                       {files.map((file,index)=>(
                        <motion.div
                         key={index}
                        whileHover={{scale:1.02}}
                        className="flex items-center justify-between bg-neutral-800 p-4 rounded-2xl shadow-lg border border-neutral-700">
                            <div className="flex items-center gap-3">
                            <FileText className="w-8 h-8 text-green-400" />
                            <p className="text-white font-semibold text-sm tracking-wide">{file.name}</p>
                            </div>
                            <button onClick={()=> removeFile(index)}>
                                <X className="w-5 h-5 text-netural-400 hover:text-red-500 transition"/>
                            </button>
                        </motion.div>
                       ))}
                    </motion.div>
                )}
            </AnimatePresence>
            </motion.div>
    </motion.div>
    )
}