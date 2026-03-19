import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import CustomTooltip from './CustomTooltip';

const DepartmentPieChart = ({ data }) => {
    const COLORS = ['#2563EB', '#6366F1', '#8B5CF6', '#EC4899', '#F59E0B'];
    const safeData = Array.isArray(data) ? data : [];

    return (
        <ResponsiveContainer width="100%" height="100%">
            <PieChart>
                <Pie
                    data={safeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={8}
                    dataKey="value"
                    stroke="none"
                    animationDuration={1500}
                >
                    {safeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                    formatter={(value) => <span className="text-sm font-medium text-gray-600 ml-1">{value}</span>}
                />
            </PieChart>
        </ResponsiveContainer>
    );
};

export default DepartmentPieChart;
