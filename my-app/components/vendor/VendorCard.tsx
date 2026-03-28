"use client";
import {motion} from "framer-motion";
import {DollarSign,Users} from "lucide-react";
import Link from "next/link";
interface VendorCardProps{
    vendorName:string;
    totalSpend:number;
    contractCount?:number;
}


export function VendorCard({vendorName,totalSpend,contractCount}:VendorCardProps){
    return(
        <Link href={`/vendor/${vendorName}`} className="w-full">
            <motion.div
        whileHover={{ scale: 1.05 }}
        className="rounded-xl border border-neutral-700 bg-linear-to-r from-indigo-300 to-indigo-500 p-5 shadow cursor-pointer"
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-lg">{vendorName}</h3>
          <DollarSign className="w-5 h-5 text-green-400" />
        </div>
        <div className="flex items-center space-x-4 text-sm text-black">
          <span>Total Spend: ${totalSpend.toLocaleString()}</span>
          {contractCount && <span>Contracts: {contractCount}</span>}
        </div>
      </motion.div>
        </Link>
    )

}