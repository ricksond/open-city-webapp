"use client";
import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import Link from "next/link";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";

const loginSchema = z.object({
  email: z.string().email("invalid email address"),
  password: z
    .string()
    .min(8, "password must be at least 8 Characters long")
    .regex(/[A-Z]/, "password must contain at least one uppercase letter") // ✅ fixed
    .regex(/[a-z]/, "password must contain at least one lowercase letter")
    .regex(/[0-9]/, "password must contain at least one number")
    .regex(/[@$!%*?&]/, "password must contain at least one special character"),
});

type loginFormData = z.infer<typeof loginSchema>;

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<loginFormData>({
    resolver: zodResolver(loginSchema),
  });
  const loginData = async (data: loginFormData) => {
    try {
      setLoading(true);
      setError("");
      const res = await axios.post("http://127.0.0.1:5000/login", {
        email: data.email,
        password: data.password,
      });
      sessionStorage.setItem("token", res.data.idToken);
      sessionStorage.setItem("uid", res.data.uid);
      sessionStorage.setItem("organization_name", res.data.organization_name);
      console.log("Login success:", res.data);
      window.location.href = "/";
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || "Login failed";
      setError(msg);
      console.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md opacity-70"
      >
        <div className="bg-white rounded-2xl p-8 shadow-xl space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-3xl text-black font-bold tracking-tighter">
              Welcome Back!
            </h1>
            <p className="text-muted-foreground">Login to your Account</p>
          </div>
          <form className="space-y-4" onSubmit={handleSubmit(loginData)}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="test@richmond.gov"
                {...register("email")}
              />
              {errors.email && (
                <span className="text-red-500 text-sm">
                  {errors.email.message}
                </span>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2"
                >
                  {showPassword ? <EyeOff /> : <Eye />}
                </button>
              </div>

              {errors.password && (
                <span className="text-red-500 text-sm">
                  {errors.password.message}
                </span>
              )}
            </div>
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            <Button type="submit" className="w-full">
              {loading ? "Logging in.." : "Login"}
            </Button>
            <div className="flex justify-center items-center">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{" "}
                <Link href="/register" className="text-black">
                  Sign up
                </Link>
              </p>
            </div>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
