import React from 'react';

const CustomTooltip = ({ active, payload, label, prefix = '', suffix = '' }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white/95 backdrop-blur-md border border-gray-100 shadow-xl rounded-xl p-4 min-w-[150px] animate-in zoom-in-95 duration-200">
                <p className="font-semibold text-gray-900 mb-2 border-b border-gray-100 pb-2 text-sm">
                    {label || payload[0].name}
                </p>
                {payload.map((entry, index) => (
                    <div key={`item-${index}`} className="flex items-center justify-between text-sm py-1">
                        <div className="flex items-center gap-2">
                            <span
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: entry.color || entry.payload.fill }}
                            ></span>
                            <span className="text-gray-600 capitalize">{entry.name}:</span>
                        </div>
                        <span className="font-medium text-gray-900 ml-4">
                            {prefix}{entry.value}{suffix}
                        </span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export default CustomTooltip;
