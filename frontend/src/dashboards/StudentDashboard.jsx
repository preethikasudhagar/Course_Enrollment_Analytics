import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import DashboardCard from '../components/DashboardCard';
import StatusBadge from '../components/StatusBadge';
import { analyticsService, courseService, enrollmentService, getErrorMessage, userService } from '../services/api';
import {
    Book,
    Layers,
    Star,
    Search,
    CheckCircle2,
    AlertCircle,
    Zap,
    XCircle,
    BookOpen,
} from 'lucide-react';

const StudentDashboard = () => {
    const [courses, setCourses] = useState([]);
    const [myEnrollments, setMyEnrollments] = useState([]);
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);

    // Get the logged-in user's department from localStorage
    const getUser = () => {
        try {
            const stored = localStorage.getItem('user');
            return stored ? JSON.parse(stored) : {};
        } catch {
            return {};
        }
    };
    const [user, setUser] = useState(getUser());
    const userDept = user?.department || 'General';

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const safeFetch = async (promise, fallback) => {
            try {
                const res = await promise;
                return res ?? fallback;
            } catch (e) {
                console.warn('Student dashboard API failed:', e);
                return fallback;
            }
        };

        try {
            setError(null);
            const [cRes, mRes, rRes, pRes] = await Promise.all([
                safeFetch(courseService.getAll(), []),
                safeFetch(enrollmentService.getMyEnc(), []),
                safeFetch(analyticsService.getRecommendations(), []),
                safeFetch(userService.getProfile(), null)
            ]);

            setCourses(Array.isArray(cRes) ? cRes : []);
            setMyEnrollments(Array.isArray(mRes) ? mRes : []);
            setRecommendations(Array.isArray(rRes) ? rRes : []);
            if (pRes) {
                setUser(pRes);
                localStorage.setItem('user', JSON.stringify(pRes));
            }
        } catch (err) {
            console.error('Data sync failed', err);
            setError(null);
        } finally {
            setLoading(false);
        }
    };

    const handleEnroll = async (id) => {
        try {
            const data = await enrollmentService.enroll(id);
            const courseName = data?.course_name || 'the course';

            if (data?.seat_expanded) {
                setMessage({
                    type: 'success',
                    text: `Seats were full! Capacity increased by 10 and you were enrolled in ${courseName}.`
                });
            } else {
                setMessage({ type: 'success', text: `Enrolled in ${courseName} successfully.` });
            }
            fetchData();
            window.dispatchEvent(new Event('refreshNotifications'));
        } catch (err) {
            setMessage({ type: 'error', text: getErrorMessage(err, 'Enrollment failed.') });
        }
        setTimeout(() => setMessage(null), 6000);
    };

    const filtered = (courses || []).filter((c) =>
        (c?.course_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c?.department || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
    const prioritizedCourses = [...filtered].sort((a, b) => {
        const aMatch = userDept !== 'General' && a?.department === userDept;
        const bMatch = userDept !== 'General' && b?.department === userDept;
        if (aMatch === bMatch) return 0;
        return aMatch ? -1 : 1;
    });

    const isEnrolled = (cid) => myEnrollments.some(e => e.course_id === cid);

    if (loading) return (
        <DashboardLayout role="student">
            <div className="flex items-center justify-center min-h-[60vh] text-slate-400">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
                    <p className="font-medium">Loading your dashboard...</p>
                </div>
            </div>
        </DashboardLayout>
    );

    if (error) {
        return (
            <DashboardLayout role="student">
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="text-center">
                        <p className="text-rose-600 mb-3">{error}</p>
                        <button onClick={fetchData} className="btn-primary">Retry</button>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    const summaryCards = [
        { title: 'My Enrollments', value: myEnrollments.length, icon: Layers, color: 'text-blue-600', bg: 'bg-blue-50', trend: 'Active' },
        { title: 'Available Courses', value: courses.length, icon: Book, color: 'text-blue-600', bg: 'bg-blue-50', trend: 'Catalog' },
        { title: 'My Department', value: userDept, icon: Star, color: 'text-amber-600', bg: 'bg-amber-50', trend: 'Primary' },
    ];

    return (
        <DashboardLayout role="student">
            {/* Header */}
            <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Student Dashboard</h1>
                        <span className="px-3 py-1 bg-blue-50 text-blue-600 text-[10px] font-bold uppercase rounded-full border border-blue-100">
                            {userDept}
                        </span>
                    </div>
                    <p className="text-slate-500 font-medium text-sm">Department: {userDept}</p>
                </div>
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input
                        type="text"
                        placeholder="Search courses..."
                        className="ui-input pl-11 pr-4 py-2.5 w-full md:w-72"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </header>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {summaryCards.map((card, i) => (
                    <DashboardCard key={i} {...card} />
                ))}
            </div>

            {/* Success/Error Message */}
            {message && (
                <div className={`mb-8 p-4 rounded-xl border flex items-center justify-between shadow-sm ${message.type === 'success'
                    ? 'bg-emerald-50 border-emerald-100 text-emerald-800'
                    : 'bg-rose-50 border-rose-100 text-rose-800'
                    }`}>
                    <div className="flex items-center gap-3 text-sm font-semibold">
                        {message.type === 'success' ? <CheckCircle2 size={20} className="text-emerald-500" /> : <AlertCircle size={20} className="text-rose-500" />}
                        {message.text}
                    </div>
                    <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-slate-600">
                        <XCircle size={16} />
                    </button>
                </div>
            )}

            {/* AI Recommendations */}
            {recommendations.length > 0 && (
                <div className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="p-2 bg-blue-600 rounded-lg text-white shadow-sm">
                            <Zap size={14} />
                        </div>
                        <h3 className="text-lg font-bold text-slate-900">Recommended for You</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {recommendations.map((rec, i) => (
                            <div key={i} className="ui-card p-5 flex flex-col items-center text-center group">
                                <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                                    <Star size={20} />
                                </div>
                                <h4 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{rec.course_name}</h4>
                                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mt-1">{rec.department}</p>
                                <p className="mt-2 text-xs text-slate-500 italic">"{rec.reason}"</p>
                                <button
                                    onClick={() => handleEnroll(rec?.course_id)}
                                    disabled={!rec?.course_id}
                                    className="w-full mt-4 py-2 bg-blue-50 text-blue-600 rounded-xl text-sm font-semibold hover:bg-blue-600 hover:text-white transition-all"
                                >
                                    Enroll
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Available Courses */}
            <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-slate-900">Available Courses</h3>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{prioritizedCourses.length} courses</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {prioritizedCourses.length === 0 ? (
                        <div className="col-span-full ui-card p-10 text-center">
                            <BookOpen size={32} className="mx-auto mb-3 text-slate-300" />
                            <p className="text-slate-500 font-semibold">No courses available.</p>
                            <p className="text-xs text-slate-400 mt-1">Check back later for new offerings.</p>
                        </div>
                    ) : prioritizedCourses.map((c, i) => {
                        const remaining = Math.max(0, Number(c?.seat_limit || 0) - Number(c?.enrolled_students || 0));
                        return (
                            <div key={i} className="ui-card p-5 flex flex-col gap-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <h4 className="text-base font-bold text-slate-900">{c?.course_name || 'Untitled Course'}</h4>
                                        <p className="text-sm text-slate-500 mt-0.5">{c?.department || 'General'}</p>
                                    </div>
                                    <span className={`shrink-0 ${remaining === 0 ? 'badge-full' : remaining <= 5 ? 'badge-almost-full' : 'badge-open'
                                        }`}>
                                        {remaining === 0 ? 'Full' : remaining <= 5 ? 'Almost Full' : 'Open'}
                                    </span>
                                </div>

                                <div className="text-xs text-slate-500">
                                    <span className="font-medium">Instructor:</span> {c?.faculty_assigned || c?.instructor || 'TBA'}
                                </div>

                                <StatusBadge enrolled={c?.enrolled_students} limit={c?.seat_limit} />

                                <button
                                    disabled={isEnrolled(c?.id)}
                                    onClick={() => handleEnroll(c?.id)}
                                    className={isEnrolled(c?.id) ? 'btn-secondary w-full opacity-50 cursor-not-allowed' : 'btn-primary w-full'}
                                >
                                    {isEnrolled(c?.id) ? 'Already Enrolled' : 'Enroll Now'}
                                </button>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* My Enrollments Table */}
            <div className="ui-card overflow-hidden mb-8">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="text-base font-bold text-slate-900">My Learning Track</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50/50 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                            <tr>
                                <th className="px-6 py-3.5">Course</th>
                                <th className="px-6 py-3.5">Enrolled On</th>
                                <th className="px-6 py-3.5 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {myEnrollments.length === 0 ? (
                                <tr>
                                    <td colSpan="3" className="px-6 py-10 text-center text-slate-400">
                                        <Layers size={28} className="mx-auto mb-2 text-slate-300" />
                                        <p className="font-medium">No enrollments yet.</p>
                                        <p className="text-xs mt-1">Browse available courses above to get started.</p>
                                    </td>
                                </tr>
                            ) : myEnrollments.map((e, i) => (
                                <tr key={i} className="hover:bg-slate-50/80 transition-all">
                                    <td className="px-6 py-4">
                                        <div className="font-bold text-slate-900">{e.course_name}</div>
                                    </td>
                                    <td className="px-6 py-4 text-slate-500 font-medium">
                                        {e?.enrollment_date ? new Date(e.enrollment_date).toLocaleDateString() : 'N/A'}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-[10px] font-bold uppercase border border-emerald-100">
                                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                                            Active
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default StudentDashboard;
