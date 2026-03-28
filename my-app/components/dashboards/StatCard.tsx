"use client";
import {motion} from 'framer-motion';

interface StatCardProps{
    title:string,
    value:number | string
}

export default function StatCard({title,value}:StatCardProps){
    return (
        <motion.div
        initial={{opacity:0, y:20}}
        animate={{opacity:1, y:0}}
        transition={{duration:0.3}} 
        className="p-6 rounded-2xl bg-linear-to-br from-neutral-900 to-neutral-800 shadow-md hover:shadow-xl transition-shadow duration-300 flex flex-col justify-between mx-4 md:mx-5">
            <div className='flex flex-col gap-3'>
                <p className="text-sm text-neutral-400">{title}</p>
                <h2 className="text-3xl font-bold text-white mt-2">{value}</h2>
            </div>
        </motion.div>
    )
}