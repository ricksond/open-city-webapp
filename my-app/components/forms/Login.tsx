"use client";
import {useState} from "react";
import {Label} from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {Eye,EyeOff} from "lucide-react";
import { Button } from "@/components/ui/button";
import {motion} from 'framer-motion';
import Link from "next/link";


export default function Login(){
    const [email,setEmail]=useState("");
    const [password,setPassword]=useState("");
    const [showPassword,setShowPassword]=useState(false);
    const[loading,setLoading]=useState(false);

    return (
        <div className="min-h-screen bg-linear-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ duration: 0.5 }}
            className="w-full max-w-md opacity-70">
                <div className="bg-white rounded-2xl p-8 shadow-xl space-y-6">
                    <div className="text-center space-y-2">
                        <h1 className="text-3xl text-black font-bold tracking-tighter">Welcome Back!</h1>
                        <p className="text-muted-foreground">Login to your Account</p>
                    </div>
                    <form className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input id="email" type="email" placeholder="test@richmond.gov" value={email} onChange={(e) => setEmail(e.target.value)} required />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <div className="relative">
                                <Input id="password" type={showPassword ? "text" : "password"} placeholder="Enter your password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-grey-500">
                                    {showPassword ? <EyeOff /> : <Eye />}
                                </button>
                            </div>
                        </div>
                        <div className="items-center justify-center">
                            <div className="flex items-center rounded-2xl">
                                <Button type="submit" className="w-full">
                                    {loading ? "Logging in..": "Login"}
                                </Button>
                            </div>
                        </div>
                        <div className="flex justify-center items-center">
                            <p className="text-sm text-muted-foreground">Don't have an account? <Link href="/register" className="text-black tracking-wide decoration-2">Sign up</Link></p>
                        </div>
                    </form>
                </div>
            </motion.div>
        </div>
    )
}

