import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import DashboardCard from '../components/DashboardCard';
import CourseEnrollmentChart from '../charts/CourseEnrollmentChart';
import StatusBadge from '../components/StatusBadge';
import { analyticsService, courseService } from '../services/api';
import {
    Users,
    BookOpen,
    TrendingUp,
    Activity,
    Award,
    AlertTriangle
} from 'lucide-react';

const FacultyDashboard = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [summary, setSummary] = useState({ total_courses: 0, total_enrollments: 0, top_course: 'N/A' });
    const [performance, setPerformance] = useState([]);
    const [enrollmentData, setEnrollmentData] = useState([]);
    const [courses, setCourses] = useState([]);

    useEffect(() => {
        fetchFacultyData();
    }, []);

    const fetchFacultyData = async () => {
        try {
            setLoading(true);
            setError(null);
            const safeFetch = async (promise, fallback) => {
                try {
                    const res = await promise;
                    return res || fallback;
                } catch (e) {
                    console.warn("Safe fetch failed:", e);
                    return fallback;
                }
            };

            const [sRes, pRes, eRes, cRes] = await Promise.all([
                safeFetch(analyticsService.getSummary(), { total_courses: 0, total_enrollments: 0, top_course: 'N/A' }),
                safeFetch(analyticsService.getFacultyStats(), []),
                safeFetch(analyticsService.getEnrollmentsChart(), []),
                safeFetch(courseService.getAll(), [])
            ]);

            setSummary(sRes || { total_courses: 0, total_enrollments: 0, top_course: 'N/A' });
            setPerformance(Array.isArray(pRes) ? pRes : []);
            setEnrollmentData(Array.isArray(eRes) ? eRes : []);
            setCourses(Array.isArray(cRes) ? cRes : []);
        } catch (err) {
            console.error('Data sync failed', err);
            setError("We couldn't load your dashboard data. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    if (error) return (
        <DashboardLayout role="faculty">
            <div className="flex items-center justify-center min-h-[60vh] text-slate-500">
                <div className="text-center max-w-sm">
                    <AlertTriangle size={40} className="mx-auto text-rose-500 mb-4" />
                    <h2 className="text-lg font-bold text-slate-900 mb-2">Sync Error</h2>
                    <p className="text-sm mb-6">{error}</p>
                    <button onClick={fetchFacultyData} className="btn-primary">Retry</button>
                </div>
            </div>
        </DashboardLayout>
    );

    if (loading) return (
        <DashboardLayout role="faculty">
            <div className="flex items-center justify-center min-h-[60vh] text-slate-400">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-slate-100 border-t-blue-600 rounded-full animate-spin"></div>
                    <p className="font-medium">Loading dashboard...</p>
                </div>
            </div>
        </DashboardLayout>
    );

    const performanceMetrics = performance && performance.length > 0 ? performance : [
        { label: "Courses Handled", value: "0", icon: "book", trend: "Active" },
        { label: "Total Enrollments", value: "0", icon: "users", trend: "↑ 12%" },
        { label: "Average Demand", value: "0%", icon: "star", trend: "Stable" },
        { label: "Retention Rate", value: "0%", icon: "thumbs-up", trend: "Good" }
    ];

    return (
        <DashboardLayout role="faculty">
            {/* Header */}
            <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-slate-900 tracking-tight">Faculty Dashboard</h1>
                    <p className="text-slate-500 font-medium mt-1 text-sm">Monitor course enrollment metrics and manage performance.</p>
                </div>
            </header>

            {/* Core Metrics */}
            <div className="mb-8">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Performance Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {performanceMetrics.map((stat, i) => {
                        const Icon = { book: BookOpen, users: Users, star: TrendingUp, 'thumbs-up': Award }[stat.icon] || Award;
                        return (
                            <DashboardCard
                                key={i}
                                title={stat.label}
                                value={stat.value || '0'}
                                icon={Icon}
                                color="text-blue-600"
                                bg="bg-blue-50"
                                trend={stat.trend}
                            />
                        );
                    })}
                </div>
            </div>

            {/* Enrollment Chart */}
            <div className="ui-card p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-base font-bold text-slate-900">Course Enrollment Breakdown</h3>
                    <Activity size={16} className="text-blue-500" />
                </div>
                {enrollmentData.length === 0 ? (
                    <div className="h-72 flex items-center justify-center text-slate-400 text-sm">
                        <div className="text-center">
                            <Activity size={28} className="mx-auto mb-2 text-slate-300" />
                            <p>No enrollment data available yet.</p>
                        </div>
                    </div>
                ) : (
                    <div className="h-72">
                        <CourseEnrollmentChart data={enrollmentData} />
                    </div>
                )}
            </div>

            {/* Course Table */}
            <div className="ui-card overflow-hidden mb-8">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                    <h3 className="text-base font-bold text-slate-900">Course Inventory</h3>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{courses.length} courses</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50/50 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                            <tr>
                                <th className="px-6 py-3.5">Course Code</th>
                                <th className="px-6 py-3.5">Course Name</th>
                                <th className="px-6 py-3.5">Department</th>
                                <th className="px-6 py-3.5">Capacity Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {!courses || courses.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-10 text-center text-slate-400">
                                        <BookOpen size={28} className="mx-auto mb-2 text-slate-300" />
                                        <p className="font-medium">No courses assigned to your portfolio.</p>
                                    </td>
                                </tr>
                            ) : (
                                courses.map((c, i) => {
                                    const remaining = Math.max(0, Number(c?.seat_limit || 0) - Number(c?.enrolled_students || 0));
                                    return (
                                        <tr key={i} className="hover:bg-slate-50/80 transition-all duration-200">
                                            <td className="px-6 py-4 text-slate-600 font-bold tracking-tight">
                                                {c?.course_code || '—'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="font-bold text-slate-900">{c?.course_name || 'Unnamed'}</div>
                                            </td>
                                            <td className="px-6 py-4 text-slate-600 font-medium">{c?.department || 'General'}</td>
                                            <td className="px-6 py-4">
                                                <StatusBadge enrolled={c?.enrolled_students || 0} limit={c?.seat_limit || 40} className="w-56" />
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </DashboardLayout >
    );
};

export default FacultyDashboard;
