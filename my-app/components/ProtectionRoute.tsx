"use client";

import { useEffect,useState } from "react";
import { useRouter } from "next/navigation";
import { set } from "zod";


export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router=useRouter();
    const[isAuthenticated,setisAuthenticated]=useState(false);

    useEffect(()=>{
        const token=sessionStorage.getItem("token");

        if(!token){
            router.push("/login");
        }else {
            setisAuthenticated(true);
        }

    },[router]);

    if (!isAuthenticated) {
    return (
      <div className="h-screen w-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-green-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return <>{children}</>;
}