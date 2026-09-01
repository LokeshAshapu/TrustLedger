import React from "react";
import { IndianRupee } from "lucide-react";

interface MoneyDisplayProps {
  amountMinor: number;
  currency?: string;
  size?: "sm" | "md" | "lg" | "xl";
  label?: string;
  isExposure?: boolean;
}

export const MoneyDisplay: React.FC<MoneyDisplayProps> = ({
  amountMinor,
  currency = "INR",
  size = "md",
  label,
  isExposure = false,
}) => {
  const inrValue = amountMinor / 100;

  // Format large values compactly if > ₹1 Lakh (e.g. ₹97.74L)
  let formattedText = "";
  if (inrValue >= 100000) {
    const lakh = inrValue / 100000;
    formattedText = `${lakh.toFixed(2)}L`;
  } else {
    formattedText = inrValue.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  const sizeClasses = {
    sm: "text-xs font-mono font-medium",
    md: "text-sm font-mono font-semibold",
    lg: "text-lg font-mono font-bold",
    xl: "text-2xl font-mono font-extrabold",
  };

  return (
    <div className="inline-flex flex-col">
      {label && <span className="text-[11px] font-sans text-text-muted uppercase tracking-wider">{label}</span>}
      <div className={`inline-flex items-center gap-0.5 text-text-primary ${sizeClasses[size]} ${isExposure ? "text-verdict-block" : ""}`}>
        {currency === "INR" ? <IndianRupee className="h-[0.85em] w-[0.85em] inline-block" /> : <span>{currency} </span>}
        <span>{formattedText}</span>
      </div>
    </div>
  );
};
