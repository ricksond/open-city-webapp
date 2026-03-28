import {motion} from "framer-motion"
import React from 'react'

export default function AnimatedContainer({
    children,
}:{children: React.ReactNode}) {
    return (
        <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6 md:p-8 shadow-lg mx-4 md:mx-6">
            {children}
        </motion.div>
    )
}