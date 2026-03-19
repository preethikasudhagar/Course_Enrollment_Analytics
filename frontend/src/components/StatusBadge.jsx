import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const StatusBadge = ({ enrolled, limit, className }) => {
    const safeEnrolled = Number(enrolled || 0);
    const safeLimit = Number(limit || 1); // Avoid division by zero
    const usage = (safeEnrolled / safeLimit) * 100;
    const remainingSeats = Math.max(0, safeLimit - safeEnrolled);

    let status = { text: 'Open', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' };
    if (remainingSeats === 0) status = { text: 'Full', color: 'bg-rose-100 text-rose-700 border-rose-200' };
    else if (remainingSeats <= 5) status = { text: 'Almost Full', color: 'bg-amber-100 text-amber-700 border-amber-200' };

    return (
        <div className={twMerge("flex flex-col gap-2", className)}>
            <div className="flex items-center justify-between gap-4">
                <span className={clsx(
                    "px-2 py-0.5 rounded-full text-xs font-semibold border inline-flex items-center gap-1.5",
                    status.color
                )}>
                    <span className={clsx("w-1.5 h-1.5 rounded-full", status.text === 'Full' ? 'bg-rose-500' : status.text === 'Almost Full' ? 'bg-amber-500' : 'bg-emerald-500')}></span>
                    {status.text}
                </span>
                <span className="text-xs text-slate-500 font-medium">
                    {remainingSeats} seats left
                </span>
            </div>
            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                    className={clsx(
                        "h-full transition-all duration-500",
                        usage >= 100 ? "bg-rose-500" : usage >= 80 ? "bg-amber-500" : "bg-emerald-500"
                    )}
                    style={{ width: `${Math.min(100, usage)}%` }}
                />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 font-medium uppercase tracking-wider">
                <span>{safeEnrolled} Enrolled</span>
                <span>{safeLimit} Capacity</span>
            </div>
        </div>
    );
};

export default StatusBadge;
