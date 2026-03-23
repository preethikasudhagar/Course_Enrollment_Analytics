import React from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Cell } from 'recharts';

const HeatmapChart = ({ data }) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const safeData = Array.isArray(data) ? data : [];

    const getIntensity = (count) => {
        if (count > 10) return '#1e40af';
        if (count > 5) return '#3b82f6';
        if (count > 2) return '#93c5fd';
        return '#dbeafe';
    };

    return (
        <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <XAxis
                    dataKey="month"
                    type="category"
                    name="Month"
                    ticks={months}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                />
                <YAxis
                    dataKey="day"
                    type="category"
                    name="Day"
                    ticks={days}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                />
                <ZAxis dataKey="count" range={[100, 1000]} name="Enrollments" />
                <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                />
                <Scatter data={safeData}>
                    {safeData.map((entry, index) => (
                        <Cell
                            key={`cell-${index}`}
                            fill={getIntensity(entry.count)}
                            stroke="white"
                            strokeWidth={2}
                        />
                    ))}
                </Scatter>
            </ScatterChart>
        </ResponsiveContainer>
    );
};

export default React.memo(HeatmapChart);
