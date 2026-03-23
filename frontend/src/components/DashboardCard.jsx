import React from 'react';

const DashboardCard = ({ title, value, icon: Icon, color, bg, trend, tooltip }) => {
    return (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 hover:shadow-xl transition-all duration-300 group relative">
            <div className="flex items-center justify-between mb-4">
                <div className={`p-2.5 rounded-xl ${bg || 'bg-blue-50'} ${color || 'text-blue-600'} group-hover:scale-110 transition-transform duration-300 shadow-sm border border-transparent group-hover:border-blue-100`}>
                    <Icon size={22} />
                </div>
                {trend && (
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100/50 shadow-sm`}>
                        {trend}
                    </span>
                )}
            </div>
            <div className="min-w-0 w-full overflow-hidden">
                <h3 className="text-base md:text-lg font-black text-slate-900 tracking-tight leading-tight mb-1 break-words">
                    {value}
                </h3>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest break-words">
                    {title}
                </p>
            </div>

            {/* Subtle bottom indicator */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

        </div>
    );
};

export default DashboardCard;
