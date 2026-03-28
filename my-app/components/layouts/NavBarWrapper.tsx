"use client";
import NavBar from "./NavBar";
import { usePathname } from "next/navigation";

export default function NavBarWrapper() {
    const pathname=usePathname();

    const hideNavBar=pathname === "/login" || pathname ==="/register";

    if (hideNavBar) return null;

    return <NavBar/>
}