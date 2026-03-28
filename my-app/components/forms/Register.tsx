"use client";
import { useState } from 'react';
import {motion} from 'framer-motion';
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Eye,EyeOff } from 'lucide-react';
import z from "zod";

const registerSchema=z.object({
    organization:z.string().min(5,"Organization name must be at least 5 characters long"),
    email:z.string().email("Invalid email address"),
    password:z.string().min(8,"Password must be at least 8 characters long").regex(/[A-Z]/,"Password must contain at least one uppercase letter").regex(/[a-z]/,"Password must contain at least one lowercase letter").regex(/[0-9]/,"Password must contain at least one number").regex(/[@$!%*?&]/,"Password must contain at least one special character"),
    confirmPassword:z.string().min(8,"Confirm password must be at least 8 characters long") 
}).refine (data => data.password ===data.confirmPassword,{
    message:"Passwords don't match",
    path:["confirmPassword"]
})


export default function Register(){
    const [organization,setOrganization]=useState("");
    const [email,setEmail]=useState("");
    const [password,setPassword]=useState("");
    const [confirmPassword,setConfirmPassword]=useState("");
    const [showPassword,setShowPassword]=useState(false);
    const [errors,setErrors]=useState<Record<string,string>>({});
    const [loading,setLoading]=useState(false);

    const handleSubmit=(e:React.FormEvent)=>{
        e.preventDefault();
        setErrors({});
        setLoading(true);

        const result=registerSchema.safeParse({organization,email,password,confirmPassword});


        try{
            // API call to register user
            console.log("Registering user with data:",result.data);
        } catch(error){
            console.log("Registration failed:",error);
            return setErrors({error:"Registration failed. Please try again."});
        }finally{
            setLoading(false);
        }
    }


    return (
        <div className="min-h-screen bg-linear-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
            <motion.div
            initial={{opacity:0,y:20 }}
            animate={{opacity:1,y:0}}
            transition={{duration:0.5}}
            className='w-full max-w-md opacity-70'>
                <div className="bg-white rounded-2xl shadow-xl p-8 space-y-6">
                    <div className='text-center space-y-2'>
                        <h1 className='tracking-wide font-bold text-black text-2xl'>Register</h1>
                        <p className="text-muted-foreground">
                            Create an account to get started
                        </p>
                    </div>
                    <form className='space-y-4' onSubmit={handleSubmit}>
                        <div className="space-y-2">
                            <Label htmlFor='text' className='tracking-wide text-black'>Organization</Label>
                            <Input id='text' type='text' placeholder='Enter your organization name' value={organization} onChange={(e) => setOrganization(e.target.value)} required />
                        </div>
                        <div className='space-y-2'>
                            <Label htmlFor='email' className='tracking-wide text-black'>Email</Label>
                            <Input id="email" type='email' placeholder="Test@richmond.gov" value={email} onChange={(e) => setEmail(e.target.value)} required />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor='password' className='tracking-wide text-black'>Password</Label>
                            <div className="relative">
                                <Input id='password' value={password} placeholder='Enter password' onClick={()=>setShowPassword(!showPassword)} required onChange={(e)=> setPassword(e.target.value)}></Input>
                                <button className='absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500'>
                                    {showPassword ? <EyeOff /> : <Eye />}
                                </button>
                            </div>
                        </div>
                        <div className='space-y-2'>
                            <Label htmlFor='confirmPassword' className='tracking-wide text-black'>Confirm Password</Label>
                            <div className="relative">
                                <Input id='confirmPassword' value={confirmPassword} placeholder='Confirm password' onClick={()=>setShowPassword(!showPassword)} required onChange={(e)=> setConfirmPassword(e.target.value)}></Input>
                                <button className='absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500'>
                                    {showPassword ? <EyeOff /> : <Eye />}
                                </button>
                            </div>
                        </div>
                        <div className='items-center justify-center'>
                            <div className='flex items-center rounded-2xl'>
                                <Button type='submit' className='w-full'>
                                {loading ? "Registering..": "Register"}
                            </Button>
                            </div>
                        </div>
                        <div className='flex justify-center items-center'>
                            <p className='text-sm text-muted-foreground'>Already have an account? <Link href="/login" className='text-black tracking-wide decoration-2'>Login</Link></p>
                        </div>
                    </form>
                </div>
            </motion.div>
        </div> 
    );
}

