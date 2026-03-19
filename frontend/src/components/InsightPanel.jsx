import React, { useEffect, useState } from 'react';
import {
    Zap,
    Bell,
    Activity,
    TrendingUp,
    AlertCircle,
    Clock,
    ChevronRight
} from 'lucide-react';
import axios from 'axios';

const InsightPanel = () => {
    const [insights, setInsights] = useState([
        { type: 'growth', message: 'Machine Learning demand up 24% this week.', icon: TrendingUp, color: 'text-indigo-600 bg-indigo-50' },
{ type: 'alert', message: '3D Modelling is reaching 90% capacity.', icon: AlertCircle, color: 'text-amber-600 bg-amber-50' },
        { type: 'info', message: 'Institutional Registry update complete.', icon: Zap, color: 'text-emerald-600 bg-emerald-50' }
    ]);

    const [activities, setActivities] = useState([
        { id: 1, action: 'Admin added CS501', time: '2 mins ago' },
        { id: 2, action: 'Dr. Kumar expanded ML seats', time: '1 hour ago' },
        { id: 3, action: 'Waitlist cleared for DB Systems', time: '3 hours ago' },
        { id: 4, action: 'System Backup Successful', time: '5 hours ago' }
    ]);

    return (
        <aside className="hidden xl:flex flex-col w-[320px] bg-white border-l border-slate-200 h-screen sticky top-0 overflow-y-auto p-6 space-y-8">
            {/* Smart Insights */}
            <section className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Zap size={14} className="text-indigo-500" />
                        Smart Insights
                    </h3>
                    <span className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-[10px] font-bold rounded-full">AI Live</span>
                </div>
                <div className="space-y-3">
                    {insights.map((insight, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2 hover:border-indigo-100 transition-colors group">
                            <div className="flex items-center gap-2">
                                <div className={`p-1.5 rounded-lg ${insight.color}`}>
                                    <insight.icon size={14} />
                                </div>
                                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">{insight.type}</span>
                            </div>
                            <p className="text-sm font-semibold text-slate-800 leading-snug">{insight.message}</p>
                            <button className="flex items-center gap-1 text-[10px] font-bold text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity">
                                View Details <ChevronRight size={10} />
                            </button>
                        </div>
                    ))}
                </div>
            </section>

            {/* Notifications Registry */}
            <section className="space-y-4">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <Bell size={14} className="text-indigo-500" />
                    Priority Alerts
                </h3>
                <div className="space-y-1">
                    {activities.slice(0, 3).map((act) => (
                        <div key={act.id} className="flex gap-4 p-3 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer group">
                            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 shrink-0 group-hover:scale-125 transition-transform" />
                            <div className="flex flex-col gap-0.5">
                                <span className="text-xs font-bold text-slate-800">{act.action}</span>
                                <span className="text-[10px] font-medium text-slate-400 font-mono">{act.time}</span>
                            </div>
                        </div>
                    ))}
                </div>
                <button className="w-full py-2.5 text-[11px] font-bold text-slate-500 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors uppercase tracking-widest">
                    Open Notification Center
                </button>
            </section>

            {/* System Pulse */}
            <section className="space-y-4">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <Activity size={14} className="text-indigo-500" />
                    Activity Pulse
                </h3>
                <div className="relative pl-4 space-y-6 before:absolute before:left-0 before:top-2 before:bottom-2 before:w-px before:bg-slate-100">
                    {activities.map((act) => (
                        <div key={act.id} className="relative space-y-1">
                            <div className="absolute -left-[21px] top-1.5 w-2 h-2 rounded-full bg-white border-2 border-slate-200" />
                            <p className="text-xs font-medium text-slate-700 leading-tight">{act.action}</p>
                            <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                                <Clock size={10} />
                                {act.time}
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </aside>
    );
};

export default InsightPanel;
