import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import DashboardCard from '../components/DashboardCard';
const CourseEnrollmentChart = React.lazy(() => import('../charts/CourseEnrollmentChart'));
const MonthlyTrendChart = React.lazy(() => import('../charts/MonthlyTrendChart'));
const DepartmentPieChart = React.lazy(() => import('../charts/DepartmentPieChart'));
const SeatUtilizationChart = React.lazy(() => import('../charts/SeatUtilizationChart'));
const HorizontalBarChart = React.lazy(() => import('../charts/HorizontalBarChart'));

import StatusBadge from '../components/StatusBadge';
import { analyticsService, courseService } from '../services/api';
import Skeleton, { SkeletonCard, SkeletonTable } from '../components/Skeleton';
import {
    Users,
    BookOpen,
    TrendingUp,
    Activity,
    Award,
    AlertTriangle,
    X
} from 'lucide-react';

const FacultyDashboard = () => {
    const [error, setError] = useState(null);
    // Single-cycle state for absolute rendering speed
    const [dashboardData, setDashboardData] = useState(() => {
        try {
            const cached = sessionStorage.getItem('faculty_vitals_full');
            return cached ? JSON.parse(cached) : null;
        } catch { return null; }
    });
    const [loading, setLoading] = useState(!dashboardData);
    const [courseStudents, setCourseStudents] = useState([]);
    const [showStudentsModal, setShowStudentsModal] = useState(false);
    const [loadingStudents, setLoadingStudents] = useState(false);

    const fetchFacultyData = React.useCallback(async () => {
        try {
            if (!dashboardData) setLoading(true);
            setError(null);
            
            const data = await analyticsService.getFacultyVitals();
            if (data) {
                setDashboardData(data);
                sessionStorage.setItem('faculty_vitals_full', JSON.stringify(data));
            }
        } catch (err) {
            console.error('Data sync failed', err);
            setError("We couldn't load your dashboard data. Please try again.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchFacultyData();
    }, []);

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

    // Destructure for easy access in JSX
    const { 
        summary = {}, 
        performance: performanceMetrics = [], 
        enrollmentData = [], 
        courses = [] 
    } = dashboardData || {};

    const chartData = React.useMemo(() => enrollmentData, [enrollmentData]);

    if (loading) {
        return (
            <DashboardLayout role="faculty">
                <div className="space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
                    </div>
                    <div className="ui-card p-6">
                        <SkeletonTable rows={10} />
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout role="faculty">
            {/* Header */}
            <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-slate-900 tracking-tight">Faculty Dashboard</h1>
                    <p className="text-slate-500 font-medium mt-1 text-sm">Monitor course enrollment metrics and manage performance.</p>
                </div>
            </header>

            {showStudentsModal && (
                <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[250] flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
                        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                            <h2 className="text-xl font-bold text-slate-900">Enrolled Students</h2>
                            <button onClick={() => setShowStudentsModal(false)} className="p-2 hover:bg-slate-100 rounded-xl transition-colors">
                                <X size={20} className="text-slate-500" />
                            </button>
                        </div>
                        <div className="p-5 overflow-y-auto">
                            {loadingStudents ? (
                                <div className="py-12 text-center text-slate-400">Loading students...</div>
                            ) : courseStudents.length === 0 ? (
                                <div className="py-12 text-center text-slate-400">No students enrolled.</div>
                            ) : (
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-[11px]">
                                        <tr>
                                            <th className="px-4 py-3 rounded-l-lg">Name</th>
                                            <th className="px-4 py-3">Email</th>
                                            <th className="px-4 py-3">Department</th>
                                            <th className="px-4 py-3 rounded-r-lg">Enrolled Date</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-50">
                                        {courseStudents.map((s, idx) => (
                                            <tr key={idx} className="hover:bg-slate-50/50">
                                                <td className="px-4 py-3 font-medium text-slate-900">{s.name}</td>
                                                <td className="px-4 py-3 text-slate-500">{s.email}</td>
                                                <td className="px-4 py-3 text-slate-500">{s.department || '—'}</td>
                                                <td className="px-4 py-3 text-slate-400">{new Date(s.enrollment_date).toLocaleDateString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>
            )}

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
                                <th className="px-6 py-3.5">Enrolled</th>
                                <th className="px-6 py-3.5">Capacity Status</th>
                                <th className="px-6 py-3.5 text-right">Actions</th>
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
                                            <td className="px-6 py-4 font-bold text-blue-600">{c?.enrolled_students || 0}</td>
                                            <td className="px-6 py-4">
                                                <StatusBadge enrolled={c?.enrolled_students || 0} limit={c?.seat_limit || 40} className="w-56" />
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button
                                                    title="View Students"
                                                    onClick={async () => {
                                                        setShowStudentsModal(true);
                                                        setLoadingStudents(true);
                                                        try {
                                                            const data = await courseService.getStudents(c.id);
                                                            setCourseStudents(Array.isArray(data) ? data : []);
                                                        } catch (e) {
                                                            setCourseStudents([]);
                                                        } finally {
                                                            setLoadingStudents(false);
                                                        }
                                                    }}
                                                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                                                >
                                                    <Users size={15} />
                                                </button>
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
