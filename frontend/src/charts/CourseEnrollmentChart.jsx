import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import CustomTooltip from './CustomTooltip';

const CourseEnrollmentChart = ({ data }) => {
    const safeData = Array.isArray(data) ? data : [];

    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={safeData} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6B7280', fontSize: 12, fontWeight: 500 }}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12, fontWeight: 500 }} />
                <Tooltip cursor={{ fill: '#F8FAFC' }} content={<CustomTooltip />} />
                <Bar dataKey="enrollments" radius={[8, 8, 0, 0]} barSize={32} animationDuration={1500} animationEasing="ease-in-out">
                    {safeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#2563EB' : '#6366F1'} fillOpacity={0.8} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};

export default CourseEnrollmentChart;
