"use client";
import { use, useState } from 'react';
import {motion} from 'framer-motion';
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Eye,EyeOff } from 'lucide-react';
import {z} from "zod";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";


const registerSchema=z.object({
    organization:z.string().min(5,"Organization name must be at least 5 characters long"),
    email:z.string().email("Invalid email address"),
    password:z.string().min(8,"Password must be at least 8 characters long").regex(/[A-Z]/,"Password must contain at least one uppercase letter")
    .regex(/[a-z]/,"Password must contain at least one lowercase letter").regex(/[0-9]/,"Password must contain at least one number").regex(/[@$!%*?&]/,"Password must contain at least one special character"),
    confirmPassword:z.string().min(8,"Confirm password must be at least 8 characters long") 
}).refine (data => data.password ===data.confirmPassword,{
    message:"Passwords do not match",
    path:["confirmPassword"]
});

type registerFormData=z.infer<typeof registerSchema>;


export default function Register(){
    const [showPassword,setShowPassword]=useState(false);
    const [error,setError]=useState("");
    const [loading,setLoading]=useState(false);

    const {register,handleSubmit,formState:{errors}}=useForm<registerFormData>({
    resolver:zodResolver(registerSchema)});

    const submitData=(data:registerFormData)=>{
     console.log("form Data",data);
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
                    <form className='space-y-4' onSubmit={handleSubmit(submitData)}>
                        <div className="space-y-2">
                            <Label htmlFor='text' className='tracking-wide text-black'>Organization</Label>
                            <Input id='text' type='text' placeholder='Enter your organization name' {...register("organization")}  required />
                            {errors.organization && <span className="text-red-500">{errors.organization.message}</span>}
                        </div>
                        <div className='space-y-2'>
                            <Label htmlFor='email' className='tracking-wide text-black'>Email</Label>
                            <Input id="email" type='email' placeholder="Test@richmond.gov" {...register("email")}  required />
                            {errors.email && <span className="text-red-500">{errors.email.message}</span>}
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor='password' className='tracking-wide text-black'>Password</Label>
                            <div className="relative">
                                <Input id='password' type="password"  placeholder='Enter password' required {...register("password")} ></Input>
                                {errors.password && <span className="text-red-500">{errors.password.message}</span>}
                                <button onClick={()=>setShowPassword(!showPassword)} className='absolute right-3 top-4 transform -translate-y-1/2 text-gray-500'>
                                    {showPassword ? <EyeOff /> : <Eye />}
                                </button>
                            </div>
                        </div>
                        <div className='space-y-2'>
                            <Label htmlFor='confirmPassword' className='tracking-wide text-black'>Confirm Password</Label>
                            <div className="relative">
                                <Input id='confirmPassword'type={showPassword? "text" : "password"}  {...register("confirmPassword")} placeholder='Confirm password' required ></Input>
                                {errors.confirmPassword && <span className="text-red-500">{errors.confirmPassword.message}</span>}
                                <button onClick={()=>setShowPassword(!showPassword)}  className='absolute right-3 top-4 transform -translate-y-1/2 text-gray-500'>
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

