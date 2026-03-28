"use client";
import react from 'react';
import {motion} from 'framer-motion';
import {
    FileText,
    Calendar,
    DollarSign,
    Users,
    CheckSquare
} from 'lucide-react';

const response = {
    ai_summary:"*Procurement Analysis: Itron Inc.\n\n1. Executive Summary\n\nTotal recorded spend with Itron Inc. is *$72,588.48*. Activity spans four contracts, primarily with the Department of Public Utilities (DPU), focusing on gas and water infrastructure components, repair parts, and software upgrades. Notable aspects include long-term agreements, renewal options, and the explicit designation of two contracts as sole-source awards. A discrepancy exists between the total reported spend and a specific payment amount detailed within a contract description.\n\n2. Key Insights\n\n   *Total Spend:* The aggregate expenditure with Itron Inc. is *$72,588.48.\n   *Largest Purchase/Activity (Identified in Contract Description):* Contract 21000014202, for an Itron Software Upgrade (MVRS to FC) for the DPU, explicitly mentions a \"Demand Payment $76,150.00.\" This amount exceeds the reported total spend, suggesting either a partial payment, a payment outside the current reporting scope for total spend, or a data discrepancy requiring further investigation.\n*   *Main Entity Involved:* The *Department of Public Utilities (DPU)* is the primary internal entity engaging with Itron Inc., being explicitly mentioned in three of the four contracts.\n*   *Nature of Goods/Services:* Procurement centers on critical utility infrastructure, including \"Gas and Water automated parts,\" \"Gas Regulators and Repair Parts,\" and \"Itron Software Upgrade.\"\n*   *Procurement Method:* Two contracts (24000006477 and 21000014202) are explicitly designated as *Sole Source Awards, indicating a lack of competitive bidding for these specific engagements.\n   *Contract Durations:* Contracts demonstrate a mix of durations, from a one-year term for the software upgrade (2021-2022) to a long-standing agreement for automated parts (2011-2022) and a new sole-source contract (2024-2028) with five two-year renewal options.\n\n*3. Top 3 Highlights\n\n1.  **Sole-Source Reliance:* Two of the four identified contracts, including a recent award (24000006477 starting 2024) and a significant software upgrade (21000014202), are explicitly sole-source. This highlights a strategic dependency on Itron Inc. for specialized products and services, warranting a review of sole-source justifications and potential for future competitive alternatives.\n2.  *Spend Discrepancy:* The reported total spend of $72,588.48 is less than the $76,150.00 \"Demand Payment\" explicitly stated within the description of contract 21000014202. This discrepancy requires immediate reconciliation to ensure accurate financial reporting and understanding of actual expenditures.\n3.  *Strategic DPU Partner:* Itron Inc. is a critical supplier for the Department of Public Utilities, providing essential components for gas and water infrastructure and vital software solutions. The presence of long-term contracts and extensive renewal options (e.g., contract 24000006477 with five two-year renewals) underscores a sustained and strategic relationship.",
    contracts: [
    {
      contract_id: "15000014256",
      description: "Gas and Water automated parts",
      start_date: "2011-01-31",
      end_date: "2022-03-04",
      vendor_name: "Itron Inc",
    },
    {
      contract_id: "18000004407",
      description:
        "IFB / Goods and Services / Department of Public Utilities / Gas Regulators and Repair Parts / Initial term of Two (2) years with Three (3) - One (1) year renewals and extension",
      start_date: "2019-09-28",
      end_date: "2023-04-28",
      vendor_name: "Itron Inc",
    },
    {
      contract_id: "24000006477",
      description: "Sole Source Award; Two Year Initial Term; Five Two-Year Renewal Options",
      start_date: "2024-03-28",
      end_date: "2028-03-27",
      vendor_name: "Itron Inc",
    },
    {
      contract_id: "21000014202",
      description:
        "no renewal options Sole Source / Demand Payment / Department of Public Utilities / Itron Software Upgrade MVRS to FC/Requisition 220005949 / DPU / Demand Payment $76,150.00",
      start_date: "2021-12-31",
      end_date: "2022-12-30",
      vendor_name: "Itron Inc",
    },
  ],
  total_spend: 72588.48,
  vendor_name: "Itron Inc",
};

export default function ContractPage(){
    return (
        <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.5}} className='min-h-screen w-full bg-linear-to-br from-green-100 to-blue-300'>
        <motion.div
        initial={{opacity:0,y:20}}
        animate={{opacity:1,y:0}}
        transition={{duration:0.5}}
        className='max-w-7xl mx-auto p-6 space-y-6'>
            <motion.div
            initial={{opacity:0,y:20}}
            animate={{opacity:1,y:0}}
            transition={{duration:0.5,delay:0.2}}
            className='rounded-md bg-linear-to-r from-indigo-300 to-indigo-300 p-6 shadow-xl text-black'
            >
                <div className="flex items-center space-x-3 mb-4">
                    <FileText className='w-6 h-6 text-white' />
                    <h2 className='text-2xl tracking-wide'>AI Summary</h2>
                </div>
                <p className="whitespace-pre-line text-sm md:text-base">
                    {response.ai_summary}
                </p>

            </motion.div>
            {/* Contracts grid */}
            <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
                {response.contracts.map((c)=>(
                    <motion.div
                    initial={{opacity:0,y:20}}
                    animate={{opacity:1,y:0}}
                    transition={{duration:0.5,delay:0.3}}
                    className='rounded-xl border border-neutral-700 bg-linear-to-r from-indigo-300 to-indigo-300 p-5 shadow hover:scale-105 transition-transform'>
                        <div className='flex items-center justify-between mb-2'>
                            <h3 className='font-semibold text-lg tracking-wide'>{c.vendor_name}</h3>
                            <CheckSquare className='w-5 h-5 text-green-400 animate-bounce'/>
                        </div>
                        <p className='text-sm text-black-300'>{c.description}</p>
                        <div className='flex items-center text-sm text-neutral-400 space-x-4'>
                            <div className='flex items-center space-x-1'>
                                <Calendar className='w-5 h-5 text-black'/>
                                <span className='text-black tracking-wide gap-5'>
                                    {new Date(c.start_date).toLocaleDateString()} -{" "}
                                    {new Date(c.end_date).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </motion.div>
    </motion.div>
    )
}