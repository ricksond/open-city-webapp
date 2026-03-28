"use client";
import React,{
    createContext,
    useContext,
    useState,
    useEffect,
    ReactNode
} from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

interface User{
    email:string,
}

