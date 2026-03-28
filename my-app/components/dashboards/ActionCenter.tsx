"use client";
import AnimatedContainer from '../ui/animated-container';
import { motion } from 'framer-motion';
import { AlertTriangle,DollarSign,RefreshCw } from 'lucide-react';


 const actions=[
        {
            icon:AlertTriangle,
            title:"Expiring Contracts",
            desc:"Staff should review contracts across City, VITA, GSA, and eVA sources before expiration.",
            color:"text-red-500"
        },
         {
            icon:DollarSign,
            title:"2 Cheaper Alternatives Found",
            desc:"GSA and VITA contracts offer better pricing for similar procurement needs.",
            color:"text-green-500"
        },
         {
            icon:RefreshCw,
            title:"1 Renewal Window Open",
            desc:"Eligible for extension within policy compliance, staff can act now.",
            color:"text-yellow-500"
        },
    ]

export default function ActionCenter(){ 
    return (
        <AnimatedContainer>
            <h2 className="text-2xl font-bold mb-6 text-white">Action Center</h2>
            <div className="grid md:grid-cols-3 gap-4">
                {actions.map((item, i) => (
                    <div
                    key={i}
                    className="flex items-start gap-4 p-5 rounded-2xl bg-linear-to-br from-neutral-900 to-neutral-800 shadow-lg hover:scale-105 hover:shadow-xl transition-transform duration-300 cursor-pointer"
                    >
                    <item.icon className={`w-7 h-7 mt-1 ${item.color}`} />
                    <div className="flex-1">
                        <p className="font-semibold text-white text-lg">{item.title}</p>
                        <p className="text-neutral-400 text-sm mt-1">{item.desc}</p>
                    </div>
                    </div>
        ))}
            </div>
        </AnimatedContainer>
    );
}