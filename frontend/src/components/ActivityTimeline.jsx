import React from 'react';
import { User, Settings, PlusCircle, RefreshCw, FileText } from 'lucide-react';

const ActivityTimeline = ({ activities }) => {
    if (!activities || activities.length === 0) return null;
    const normalizedActivities = activities.map((act) => (typeof act === 'string' ? act : act?.action || 'System activity'));

    const getIcon = (action) => {
        if (action.includes('enrolled')) return <User size={14} />;
        if (action.includes('seat')) return <Settings size={14} />;
        if (action.includes('added')) return <PlusCircle size={14} />;
        if (action.includes('expanded')) return <RefreshCw size={14} />;
        return <FileText size={14} />;
    };

    const getBg = (action) => {
        if (action.includes('enrolled')) return 'bg-blue-50 text-blue-600';
        if (action.includes('seat')) return 'bg-amber-50 text-amber-600';
        if (action.includes('added')) return 'bg-emerald-50 text-emerald-600';
        if (action.includes('expanded')) return 'bg-purple-50 text-purple-600';
        return 'bg-slate-50 text-slate-600';
    };

    return (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-6">System Activity</h3>
            <div className="relative space-y-6 before:absolute before:left-[15px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
                {normalizedActivities.map((act, i) => (
                    <div key={i} className="relative pl-10 group">
                        <div className={`absolute left-0 top-0 w-8 h-8 rounded-full border-4 border-white flex items-center justify-center transition-transform group-hover:scale-110 z-10 ${getBg(act)}`}>
                            {getIcon(act)}
                        </div>
                        <div className="p-3 rounded-xl border border-transparent hover:border-slate-100 hover:bg-slate-50 transition-all">
                            <p className="text-sm font-medium text-slate-700 leading-snug">
                                {act}
                            </p>
                            <span className="text-[11px] text-slate-400 font-medium mt-1 inline-block">
                                Just now
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ActivityTimeline;
