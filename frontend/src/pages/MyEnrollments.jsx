import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { enrollmentService } from '../services/api';
import { Calendar, BookOpen, Clock, Download, ChevronRight, CheckCircle2, X } from 'lucide-react';

const MyEnrollments = () => {
    const [enrollments, setEnrollments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedEnrollment, setSelectedEnrollment] = useState(null);

    useEffect(() => {
        const fetchEnrollments = async () => {
            try {
                const res = await enrollmentService.getMyEnc();
                setEnrollments(res || []);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchEnrollments();
    }, []);

    if (loading) return (
        <DashboardLayout role="student">
            <div className="flex items-center justify-center h-64 text-gray-500">
                <p>Loading your enrollments...</p>
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout role="student">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">My Enrollments</h1>
                    <p className="text-gray-500 text-sm mt-1">Manage and view your currently enrolled courses</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors shadow-sm">
                    <Download size={16} /> Export Schedule
                </button>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm mb-8">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4">Course Name</th>
                                <th className="px-6 py-4">Enrollment Date</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 text-gray-700">
                            {enrollments.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-8 text-center text-gray-500">
                                        You are not enrolled in any courses yet.
                                    </td>
                                </tr>
                            ) : enrollments.map((enc) => (
                                <tr key={enc.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                                                <BookOpen size={20} />
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-900">{enc.course_name}</p>
                                                <p className="text-xs text-gray-500 mt-0.5">ID: {enc.course_id}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2 text-gray-600">
                                            <Calendar size={16} className="text-gray-400" />
                                            {enc?.enrollment_date ? new Date(enc.enrollment_date).toLocaleDateString(undefined, {
                                                year: 'numeric',
                                                month: 'short',
                                                day: 'numeric'
                                            }) : 'N/A'}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200">
                                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-600"></div>
                                            Active
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => setSelectedEnrollment(enc)}
                                            className="text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors inline-flex items-center gap-1"
                                        >
                                            View Details <ChevronRight size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 bg-blue-600 rounded-xl flex items-center gap-5 text-white shadow-md relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-700"></div>
                    <div className="p-3 bg-white/20 rounded-lg relative z-10">
                        <Clock size={28} />
                    </div>
                    <div className="relative z-10">
                        <h4 className="font-semibold text-lg mb-0.5">Next Class</h4>
                        <p className="text-sm text-blue-100">Monday, 10:00 AM • System Architecture</p>
                    </div>
                </div>
                <div className="p-6 bg-white border border-gray-200 rounded-xl flex items-center gap-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                        <Calendar size={28} />
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 text-lg mb-0.5">Academic Calendar</h4>
                        <p className="text-sm text-gray-500">Midterm examinations start in 12 days</p>
                    </div>
                </div>
            </div>

            {selectedEnrollment && (
                <div className="ui-modal" onClick={() => setSelectedEnrollment(null)}>
                    <div className="ui-modal-panel max-w-lg p-0 overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-slate-900">Enrollment Details</h3>
                            <button
                                onClick={() => setSelectedEnrollment(null)}
                                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                                aria-label="Close details"
                            >
                                <X size={18} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="ui-card-muted p-4">
                                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Course</p>
                                <p className="text-base font-bold text-slate-900">{selectedEnrollment.course_name || 'N/A'}</p>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="ui-card-muted p-4">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Course ID</p>
                                    <p className="text-sm font-semibold text-slate-700">{selectedEnrollment.course_id}</p>
                                </div>
                                <div className="ui-card-muted p-4">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Enrollment Date</p>
                                    <p className="text-sm font-semibold text-slate-700">
                                        {selectedEnrollment.enrollment_date
                                            ? new Date(selectedEnrollment.enrollment_date).toLocaleString()
                                            : 'N/A'}
                                    </p>
                                </div>
                            </div>
                            <div className="pt-2 flex justify-end">
                                <button className="btn-secondary" onClick={() => setSelectedEnrollment(null)}>
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
};

export default MyEnrollments;
