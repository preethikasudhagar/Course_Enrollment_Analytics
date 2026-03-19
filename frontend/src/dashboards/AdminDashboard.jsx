import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import DashboardCard from '../components/DashboardCard';
import CourseEnrollmentChart from '../charts/CourseEnrollmentChart';
import MonthlyTrendChart from '../charts/MonthlyTrendChart';
import DepartmentPieChart from '../charts/DepartmentPieChart';
import SeatUtilizationChart from '../charts/SeatUtilizationChart';
import HorizontalBarChart from '../charts/HorizontalBarChart';
import HeatmapChart from '../charts/HeatmapChart';
import { analyticsService, courseService } from '../services/api';
import {
    Users,
    BookOpen,
    Shield,
    Zap,
    Globe,
    Plus,
    Download,
    TrendingUp,
    Calendar,
    Layout,
    X,
    CheckCircle2
} from 'lucide-react';




// ──────────────────────────────────────────
// Admin Dashboard
// ──────────────────────────────────────────
const AdminDashboard = () => {
    const [summary, setSummary] = useState({
        total_students: 0,
        total_courses: 0,
        total_enrollments: 0,
        top_course: 'N/A',
        most_popular_course_enrollment_count: 0,
        utilization: 0
    });
    const [charts, setCharts] = useState({
        trends: [],
        topCourses: [],
        utilDetail: [],
        deptEnroll: [],
        prediction: [],
        heatmap: [],
    });
    const [deptUtilization, setDeptUtilization] = useState([]);
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');
    
    // New States
    const [expansionLogs, setExpansionLogs] = useState([]);
    const [courseStudents, setCourseStudents] = useState([]);
    const [showStudentsModal, setShowStudentsModal] = useState(false);
    const [loadingStudents, setLoadingStudents] = useState(false);


    useEffect(() => {
        fetchAdminData();
    }, []);

    const fetchAdminData = async () => {
        const safeFetch = async (promise, fallback) => {
            try {
                const res = await promise;
                return res ?? fallback;
            } catch (e) {
                console.warn('Admin dashboard API failed:', e);
                return fallback;
            }
        };

        try {
            setLoading(true);
            setError(null);
            const [sRes, tRes, uRes, pRes, dRes, cRes, duRes, hmRes, logsRes] = await Promise.all([
                safeFetch(analyticsService.getDashboardStats(), null),
                safeFetch(analyticsService.getEnrollmentTrends(), []),
                safeFetch(analyticsService.getPopularity(), []),
                safeFetch(analyticsService.getDemandPrediction(), []),
                safeFetch(analyticsService.getDeptStats(), []),
                safeFetch(courseService.getAll(), []),
                safeFetch(analyticsService.getDeptUtilization(), []),
                safeFetch(analyticsService.getHeatmap(), []),
                safeFetch(analyticsService.getSeatExpansionLogs(), [])
            ]);

            setSummary(sRes || {
                total_students: 0,
                total_courses: 0,
                total_enrollments: 0,
                top_course: 'N/A',
                most_popular_course_enrollment_count: 0,
                utilization: 0
            });
            setCharts({
                trends: Array.isArray(tRes) ? tRes : [],
                topCourses: (Array.isArray(uRes) ? uRes : []).map(p => ({
                    name: p.course_name || p.name,
                    students: p.value || p.students || 0
                })),
                utilDetail: [
                    { name: 'Enrolled', value: sRes?.total_enrollments || 0 },
                    { name: 'Remaining', value: Math.max(0, (sRes?.total_seats || 0) - (sRes?.total_enrollments || 0)) }
                ],
                deptEnroll: (Array.isArray(dRes) ? dRes : []).map(d => ({
                    name: d.name || d.department,
                    enrollments: d.value || d.enrollments || 0
                })),
                prediction: (Array.isArray(pRes) ? pRes : []).map(p => ({
                    name: p.course_name || p.name,
                    enrollments: p.value || p.predicted || 0
                })),
                heatmap: Array.isArray(hmRes) ? hmRes : [],
            });
            setCourses(Array.isArray(cRes) ? cRes : []);
            setDeptUtilization(Array.isArray(duRes) ? duRes : []);
            setExpansionLogs(Array.isArray(logsRes) ? logsRes : []);
        } catch (error) {
            console.error("Dashboard fetch error:", error);
            setError(null);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (format, reportType = 'general') => {
        try {
            const res = await analyticsService.exportData(format, reportType);
            const blob = new Blob([res.data]);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${reportType}_report.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch (err) {
            console.error('Export failed', err);
        }
    };

    const handleCourseCreated = () => {
        setSuccessMsg('Course created successfully!');
        fetchAdminData();
        setTimeout(() => setSuccessMsg(''), 5000);
    };

    const handleViewStudents = async (course) => {
        setShowStudentsModal(true);
        setLoadingStudents(true);
        try {
            const data = await courseService.getStudents(course.id);
            setCourseStudents(Array.isArray(data) ? data : []);
        } catch (e) {
            console.error(e);
            setCourseStudents([]);
        } finally {
            setLoadingStudents(false);
        }
    };

    const metrics = [
        { title: 'Total Students', value: summary.total_students || 0, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50', trend: '↑ 4% this month' },
        { title: 'Total Courses', value: summary.total_courses || 0, icon: BookOpen, color: 'text-blue-600', bg: 'bg-blue-50', trend: 'Stable' },
        { title: 'Total Enrollments', value: summary.total_enrollments || 0, icon: Zap, color: 'text-amber-600', bg: 'bg-amber-50', trend: '↑ 12% this month' },
        {
            title: 'Most Popular',
            value: summary.top_course || 'N/A',
            icon: Shield,
            color: 'text-emerald-600',
            bg: 'bg-emerald-50',
            trend: `${summary.most_popular_course_enrollment_count || 0} enrolled`
        },
        { title: 'Overall Utilization', value: `${summary.utilization || 0}%`, icon: Globe, color: 'text-rose-600', bg: 'bg-rose-50', trend: '↑ 2.1%' },
    ];

    if (loading) {
        return (
            <DashboardLayout role="admin">
                <div className="flex items-center justify-center min-h-[60vh] text-slate-500">
                    <div className="flex flex-col items-center gap-4">
                        <div className="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
                        <p className="font-medium">Loading dashboard...</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout role="admin">
            {/* Success Toast */}
            {successMsg && (
                <div className="fixed top-6 right-6 z-[200] bg-emerald-50 border border-emerald-200 text-emerald-800 px-5 py-3 rounded-xl shadow-lg flex items-center gap-3 animate-in slide-in-from-top-4 duration-300">
                    <CheckCircle2 size={18} className="text-emerald-500" />
                    <span className="text-sm font-semibold">{successMsg}</span>
                </div>
            )}

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

            {/* Header */}
            <header className="mb-8 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-slate-900 tracking-tight">Institutional Analytics</h1>
                    <p className="text-slate-500 font-medium mt-1 flex items-center gap-2 text-sm">
                        <Calendar size={14} />
                        Semester Overview • Live Data Feed
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="dropdown relative group">
                        <button className="btn-secondary">
                            <Download size={16} className="text-slate-400" />
                            Export Report
                        </button>
                        <div className="absolute right-0 top-full mt-2 w-52 bg-white border border-slate-100 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 overflow-hidden">
                            <div className="px-4 py-2 text-[10px] font-bold text-slate-400 uppercase bg-slate-50 border-b border-slate-100">Enrollment Report</div>
                            <button onClick={() => handleExport('csv')} className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors">Export as CSV</button>
                            <button onClick={() => handleExport('pdf')} className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors">Export as PDF</button>
                            <div className="px-4 py-2 text-[10px] font-bold text-slate-400 uppercase bg-slate-50 border-t border-b border-slate-100">Dept Utilization</div>
                            <button onClick={() => handleExport('csv', 'department')} className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors">Export Dept CSV</button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
                {metrics.map((card, i) => (
                    <DashboardCard key={i} {...card} />
                ))}
            </div>

            {/* Department Utilization Panel */}
            <div className="ui-card p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-lg font-bold text-slate-900">Department Utilization</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Enrollment and capacity by department</p>
                    </div>
                    <Layout size={18} className="text-blue-500" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {deptUtilization.length === 0 ? (
                        <div className="col-span-full text-sm text-slate-400 text-center py-8">No department data available.</div>
                    ) : deptUtilization.map((dept, i) => (
                        <div key={i} className="space-y-3 p-4 bg-slate-50/50 rounded-xl">
                            <div className="flex justify-between items-center text-sm">
                                <span className="font-bold text-slate-700">{dept.department}</span>
                                <span className="text-slate-500 font-medium text-xs">{dept.total_students} / {dept.total_seats}</span>
                            </div>
                            <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-1000 ${dept.utilization_pct > 80 ? 'bg-rose-500' : dept.utilization_pct > 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                                    style={{ width: `${dept.utilization_pct}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-tight">
                                <span className={dept.utilization_pct > 80 ? 'text-rose-600' : dept.utilization_pct > 40 ? 'text-amber-600' : 'text-emerald-600'}>
                                    {dept.utilization_pct}% Utilized
                                </span>
                                <span className="text-slate-400">{dept.utilization_pct > 80 ? 'High Demand' : dept.utilization_pct > 40 ? 'Medium' : 'Stable'}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Charts Grid – 2x2 */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
                <div className="ui-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-base font-bold text-slate-900">Course Enrollment Distribution</h3>
                        <TrendingUp size={16} className="text-blue-500" />
                    </div>
                    <div className="h-72">
                        <HorizontalBarChart data={charts.topCourses} />
                    </div>
                </div>
                <div className="ui-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-base font-bold text-slate-900">Monthly Enrollment Trends</h3>
                        <Zap size={16} className="text-amber-500" />
                    </div>
                    <div className="h-72">
                        <MonthlyTrendChart data={charts.trends} />
                    </div>
                </div>
                <div className="ui-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-base font-bold text-slate-900">Department Distribution</h3>
                        <Layout size={16} className="text-purple-500" />
                    </div>
                    <div className="h-72">
                        <CourseEnrollmentChart data={charts.deptEnroll} />
                    </div>
                </div>
                <div className="ui-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-base font-bold text-slate-900">Seat Utilization</h3>
                        <Globe size={16} className="text-emerald-500" />
                    </div>
                    <div className="h-72">
                        <SeatUtilizationChart data={charts.utilDetail} />
                    </div>
                </div>
            </div>

            {/* Course Table */}
            <div className="ui-card overflow-hidden mb-8">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <div>
                        <h3 className="text-base font-bold text-slate-900">Course Inventory</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Real-time status for all courses</p>
                    </div>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{courses.length} courses</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50/50 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                            <tr>
                                <th className="px-6 py-3.5">Course Code</th>
                                <th className="px-6 py-3.5">Course Name</th>
                                <th className="px-6 py-3.5">Department</th>
                                <th className="px-6 py-3.5">Seat Limit</th>
                                <th className="px-6 py-3.5">Enrolled</th>
                                <th className="px-6 py-3.5">Remaining</th>
                                <th className="px-6 py-3.5">Status</th>
                                <th className="px-6 py-3.5 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {courses.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="px-6 py-12 text-center">
                                        <div className="text-slate-400">
                                            <BookOpen size={32} className="mx-auto mb-3 text-slate-300" />
                                            <p className="font-semibold">No courses available.</p>
                                            <p className="text-xs mt-1">Create your first course to start enrollment tracking.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : courses.map((c, i) => {
                                const limit = Number(c?.seat_limit) || 0;
                                const enrolled = Number(c?.enrolled_students) || 0;
                                const remaining = Math.max(0, limit - enrolled);

                                let statusLabel = "Open";
                                let statusClass = "badge-open";
                                if (remaining === 0) {
                                    statusLabel = "Full";
                                    statusClass = "badge-full";
                                } else if (remaining <= 5) {
                                    statusLabel = "Almost Full";
                                    statusClass = "badge-almost-full";
                                }

                                const handleDelete = async (id) => {
                                    if (window.confirm("Delete this course permanently?")) {
                                        try {
                                            await courseService.delete(id);
                                            fetchAdminData();
                                        } catch (e) {
                                            alert("Delete failed");
                                        }
                                    }
                                };

                                const handleIncreaseLimit = async (course) => {
                                    try {
                                        await courseService.update(course.id, { seat_limit: course.seat_limit + 10 });
                                        fetchAdminData();
                                    } catch (e) {
                                        alert("Update failed");
                                    }
                                };

                                return (
                                    <tr key={i} className="group hover:bg-slate-50/80 transition-all duration-200">
                                        <td className="px-6 py-4 text-slate-600 font-bold tracking-tight">
                                            {c.course_code || '—'}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="font-bold text-slate-900">{c.course_name}</div>
                                        </td>
                                        <td className="px-6 py-4 text-slate-600 font-medium">{c.department}</td>
                                        <td className="px-6 py-4 font-bold text-slate-700">{limit}</td>
                                        <td className="px-6 py-4">
                                            <span className="text-blue-600 font-bold">{enrolled}</span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 font-medium">{remaining}</td>
                                        <td className="px-6 py-4">
                                            <span className={statusClass}>{statusLabel}</span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-1">
                                                <button
                                                    title="View Students"
                                                    onClick={() => handleViewStudents(c)}
                                                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                                                >
                                                    <Users size={15} />
                                                </button>
                                                <button
                                                    title="Increase Seats +10"
                                                    onClick={() => handleIncreaseLimit(c)}
                                                    className="p-2 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all"
                                                >
                                                    <Plus size={15} />
                                                </button>
                                                <button
                                                    title="Delete Course"
                                                    onClick={() => handleDelete(c.id)}
                                                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
                                                >
                                                    <X size={15} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Seat Expansion History */}
            <div className="ui-card overflow-hidden mb-8">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                        <TrendingUp size={16} className="text-emerald-500" />
                        Seat Expansion History
                    </h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50/50 text-slate-500 font-bold uppercase text-[11px]">
                            <tr>
                                <th className="px-6 py-3.5">Date</th>
                                <th className="px-6 py-3.5">Course</th>
                                <th className="px-6 py-3.5">Old Limit</th>
                                <th className="px-6 py-3.5">New Limit</th>
                                <th className="px-6 py-3.5">Increment</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {expansionLogs.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-8 text-center text-slate-400">
                                        No automatic seat expansions recorded yet.
                                    </td>
                                </tr>
                            ) : expansionLogs.map((log, i) => (
                                <tr key={i} className="hover:bg-slate-50/50">
                                    <td className="px-6 py-3 text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                                    <td className="px-6 py-3 font-semibold text-slate-700">{log.course_name}</td>
                                    <td className="px-6 py-3 text-slate-500">{log.old_limit}</td>
                                    <td className="px-6 py-3 font-bold text-emerald-600">{log.new_limit}</td>
                                    <td className="px-6 py-3 text-slate-500">+{log.increment_by}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default AdminDashboard;
