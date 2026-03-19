import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const SeatUtilizationChart = ({ data }) => {
    // Expected format: [{ name: 'Enrolled', value: 40 }, { name: 'Remaining', value: 60 }]
    const COLORS = ['#2563EB', '#F1F5F9'];
    const safeData = Array.isArray(data) ? data : [];

    return (
        <div className="h-full w-full flex flex-col">
            <div className="flex-1 min-h-[150px]">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={safeData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                            stroke="none"
                        >
                            {safeData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                borderRadius: '8px',
                                border: '1px solid #E5E7EB',
                                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
                                fontSize: '12px',
                                color: '#1F2937',
                                padding: '12px'
                            }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center gap-6 mt-4">
                {safeData.map((entry, i) => (
                    <div key={i} className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }}></div>
                        <span className="text-sm font-medium text-gray-600">{entry.name}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SeatUtilizationChart;
