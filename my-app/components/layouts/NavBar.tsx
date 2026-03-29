"use client";
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

const NavBar = () => {
    const pathname=usePathname();
    const [isActive,setIsActive]=useState(pathname || "/");

    const navItems=[
        {name:"vendor",href:"/vendor"},
        {name:"contracts",href:"/contracts"},
        {name:"upload",href:"/upload"},
    ]

  return (
    <div className='border-b border-black bg-blue-200 opacity-70 top-0 z-50'>
        <div className='max-w-7xl mx-auto flex items-center justify-between p-4'>
            <motion.div whileHover={{scale:1.1}} className='rounded-xl border border-neutral-800 bg-neutral-900 p-4 md:text-5xl lg:text-6xl p4 shadow-lg'>
                <h1 className=' text-lg text-white hover:text-white'><Link href="/">City of Richmond Procurement</Link></h1>
            </motion.div>

            <div className='flex gap-6'>
                {navItems.map((item)=>(
                    <motion.div key={item.name} whileHover={{scale:1.1}} className='text-lg text-black'>
                        <Link href={item.href} className={`text-black-300 tracking-widest hover:text-indigo-500 ${isActive===item.href ? "text-black font-semibold" : ""}`} onClick={()=>setIsActive(item.href)}>
                            {item.name}
                        </Link>
                    </motion.div>
                ))}
            </div>
        </div>
    </div>
  )
}

export default NavBar;