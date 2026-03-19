import React from 'react';
import { TrendingUp, AlertCircle, BarChart3, Info, ChevronRight } from 'lucide-react';

const iconMap = {
    'trending-up': TrendingUp,
    'alert-circle': AlertCircle,
    'bar-chart': BarChart3,
    'info': Info
};

const InsightsPanel = ({ insights }) => {
    if (!insights || insights.length === 0) return null;

    return (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <TrendingUp className="text-blue-600" size={20} />
                    Smart Insights
                </h3>
            </div>
            <div className="space-y-4">
                {insights.map((insight, idx) => {
                    const Icon = iconMap[insight.icon] || Info;
                    return (
                        <div key={idx} className="group p-4 bg-slate-50 border border-slate-100 rounded-xl hover:bg-white hover:border-blue-200 transition-all cursor-default">
                            <div className="flex gap-4">
                                <div className={`p-2 rounded-lg shrink-0 ${insight.type === 'growth' ? 'bg-emerald-100 text-emerald-600' :
                                        insight.type === 'warning' ? 'bg-amber-100 text-amber-600' :
                                            'bg-blue-100 text-blue-600'
                                    }`}>
                                    <Icon size={18} />
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm font-medium text-slate-700 leading-relaxed group-hover:text-slate-900">
                                        {insight.message}
                                    </p>
                                </div>
                                <ChevronRight className="text-slate-300 group-hover:text-blue-400 transition-colors" size={16} />
                            </div>
                        </div>
                    );
                })}
            </div>
            <button className="w-full mt-6 py-2.5 text-sm font-semibold text-blue-600 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors">
                View Full Report
            </button>
        </div>
    );
};

export default InsightsPanel;
