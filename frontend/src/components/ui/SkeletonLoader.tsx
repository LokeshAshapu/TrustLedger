import React from "react";

interface SkeletonLoaderProps {
  className?: string;
  rows?: number;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  className = "h-4 w-full",
  rows = 1,
}) => {
  return (
    <div className="space-y-2 w-full animate-pulse">
      {Array.from({ length: rows }).map((_, idx) => (
        <div
          key={idx}
          className={`bg-background-surface/80 border border-border-subtle/50 rounded-control ${className}`}
        />
      ))}
    </div>
  );
};
