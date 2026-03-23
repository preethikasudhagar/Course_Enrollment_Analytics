import React from 'react';

const Skeleton = ({ className, variant = 'rect' }) => {
  const baseClass = "bg-slate-200 animate-pulse rounded";
  const variantClasses = {
    rect: "h-4 w-full",
    circle: "h-12 w-12 rounded-full",
    card: "h-32 w-full rounded-xl",
    text: "h-3 w-3/4",
    title: "h-6 w-1/2 mb-4"
  };

  return (
    <div className={`${baseClass} ${variantClasses[variant]} ${className}`} />
  );
};

export const SkeletonCard = () => (
  <div className="ui-card p-6 flex flex-col gap-4">
    <Skeleton variant="circle" />
    <Skeleton variant="title" />
    <Skeleton variant="text" />
  </div>
);

export const SkeletonTable = ({ rows = 5 }) => (
  <div className="w-full space-y-4">
    <Skeleton variant="title" className="w-1/4" />
    {[...Array(rows)].map((_, i) => (
      <div key={i} className="flex gap-4">
        <Skeleton className="flex-1" />
        <Skeleton className="flex-1" />
        <Skeleton className="flex-1" />
      </div>
    ))}
  </div>
);

export default Skeleton;
