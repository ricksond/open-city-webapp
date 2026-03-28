"use client";
import AnimatedContainer from '../ui/animated-container';
import { motion } from 'framer-motion';

export default function ContractInsights(){
    return (
        <AnimatedContainer>
            <h2 className="text-lg font-semibold mb-4">Insights</h2>

            <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                    <span>Expiry Risk</span>
                    <span className="text-red-400">High</span>
                </div>

                <div className="flex justify-between">
                  <span>Renewal Window</span>
                  <span className="text-yellow-400">Open</span>
                </div>

                <div className="flex justify-between">
                  <span>Price Competitiveness</span>
                  <span className="text-green-400">Below Market</span>
                </div>

                <div className="flex justify-between">
                  <span>Alternative Sources</span>
                  <span className="text-blue-400">Available</span>
                </div>
           </div>
        </AnimatedContainer>
    )
}