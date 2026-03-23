import React, { useState, useEffect, useCallback, useMemo, memo } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import DashboardCard from '../components/DashboardCard';
import StatusBadge from '../components/StatusBadge';
import { analyticsService, courseService, enrollmentService, getErrorMessage, userService } from '../services/api';
import Skeleton, { SkeletonCard, SkeletonTable } from '../components/Skeleton';
import {
    Activity,
    Layers,
    Book,
    BookOpen,
    Star,
    Search,
    Zap,
    CheckCircle2,
    AlertCircle,
    XCircle,
} from 'lucide-react';

const CourseCard = memo(({ course, isEnrolled, onEnroll, isEnrolling }) => {
    const remaining = Math.max(0, Number(course?.seat_limit || 0) - Number(course?.enrolled_students || 0));
    return (
        <div className="ui-card p-5 flex flex-col gap-4">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <h4 className="text-base font-bold text-slate-900">{course?.course_name || 'Untitled Course'}</h4>
                    <p className="text-sm text-slate-500 mt-0.5">{course?.department || 'General'}</p>
                </div>
            </div>

            <div className="text-xs text-slate-500">
                <span className="font-medium">Instructor:</span> {course?.faculty_assigned || course?.instructor || 'TBA'}
            </div>

            <StatusBadge enrolled={course?.enrolled_students} limit={course?.seat_limit} />

            <button
                disabled={isEnrolled || isEnrolling}
                onClick={() => onEnroll(course?.id)}
                className={isEnrolled ? 'btn-secondary w-full opacity-50 cursor-not-allowed' : 'btn-primary w-full flex items-center justify-center gap-2'}
            >
                {isEnrolling ? (
                    <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Enrolling...
                    </>
                ) : (
                    isEnrolled ? 'Already Enrolled' : 'Enroll Now'
                )}
            </button>
        </div>
    );
});

const EnrollmentRow = memo(({ enrollment }) => (
    <tr className="hover:bg-slate-50/80 transition-all">
        <td className="px-6 py-4">
            <div className="font-bold text-slate-900">{enrollment.course_name}</div>
        </td>
        <td className="px-6 py-4 text-slate-500 font-medium">
            {enrollment?.enrollment_date ? new Date(enrollment.enrollment_date).toLocaleDateString() : 'N/A'}
        </td>
        <td className="px-6 py-4 text-right">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-[10px] font-bold uppercase border border-emerald-100">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                Active
            </div>
        </td>
    </tr>
));

const StudentDashboard = () => {
    // Single-cycle state for absolute rendering speed
    const [dashboardData, setDashboardData] = useState(() => {
        try {
            const cached = sessionStorage.getItem('student_vitals_full');
            return cached ? JSON.parse(cached) : null;
        } catch { return null; }
    });
    const [myEnrollments, setMyEnrollments] = useState(() => {
        const cached = sessionStorage.getItem('student_vitals_enrollments');
        return cached ? JSON.parse(cached) : [];
    });
    const [loading, setLoading] = useState(!dashboardData);
    const [enrollingId, setEnrollingId] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [retryCount, setRetryCount] = useState(0);
    const MAX_RETRIES = 2;

    const [user, setUser] = useState(() => {
        try {
            const stored = localStorage.getItem('user');
            return stored ? JSON.parse(stored) : {};
        } catch { return {}; }
    });
    const userDept = user?.department || 'General';

    const fetchData = React.useCallback(async (isManualRetry = false) => {
        try {
            if (!dashboardData || isManualRetry) setLoading(true);
            setError(null);
            
            const [vitals, enrollments, profile] = await Promise.all([
                analyticsService.getStudentVitals(),
                enrollmentService.getMyEnc(),
                userService.getProfile()
            ]);

            if (vitals) {
                setDashboardData(vitals);
                sessionStorage.setItem('student_vitals_full', JSON.stringify(vitals));
            }
            if (enrollments) {
                setMyEnrollments(enrollments);
                sessionStorage.setItem('student_vitals_enrollments', JSON.stringify(enrollments));
            }
            if (profile) {
                setUser(profile);
                localStorage.setItem('user', JSON.stringify(profile));
            }
            setRetryCount(0); // Reset on success
        } catch (err) {
            console.error('Student sync failed:', err);
            if (retryCount < MAX_RETRIES && !isManualRetry) {
                setRetryCount(prev => prev + 1);
                setTimeout(() => fetchData(), 2000);
            } else {
                setError('Failed to refresh your dashboard. Please check your connection.');
            }
        } finally {
            if (retryCount >= MAX_RETRIES || dashboardData) setLoading(false);
        }
    }, [dashboardData, retryCount]);

    useEffect(() => {
        fetchData();
    }, []);

    const handleEnroll = async (id) => {
        if (!id || enrollingId) return;
        setEnrollingId(id);
        try {
            const data = await enrollmentService.enroll(id);
            const courseName = data?.course_name || 'the course';

            if (data) {
                const updatedCourse = data;
                setDashboardData(prev => ({
                    ...prev,
                    courses: (prev?.courses || []).map(c => 
                        c.id === id ? { 
                            ...c, 
                            enrolled_students: updatedCourse.enrolled_count,
                            seat_limit: updatedCourse.seat_limit,
                            available_seats: updatedCourse.available_seats
                        } : c
                    )
                }));
                
                // Optimistically update enrollments so the button instantly locks
                setMyEnrollments(prev => [...prev, { course_id: id }]);
            }

            if (data?.seat_expanded) {
                setMessage({
                    type: 'success',
                    text: `Successfully enrolled. Seats increased automatically.`
                });
            } else {
                setMessage({ type: 'success', text: `Enrolled in ${courseName} successfully.` });
            }
            
            // Re-fetch everything else in the background
            fetchData();
            window.dispatchEvent(new Event('refreshNotifications'));
        } catch (err) {
            setMessage({ type: 'error', text: getErrorMessage(err, 'Enrollment failed.') });
        } finally {
            setEnrollingId(null);
        }
        setTimeout(() => setMessage(null), 6000);
    };

    const { 
        courses = [], 
        recommendations = [] 
    } = dashboardData || {};

    const prioritizedCourses = useMemo(() => {
        const lowerSearch = searchTerm.toLowerCase();
        const filtered = (courses || []).filter((c) =>
            (c?.course_name || '').toLowerCase().includes(lowerSearch) ||
            (c?.department || '').toLowerCase().includes(lowerSearch)
        );
        return [...filtered].sort((a, b) => {
            const aMatch = userDept !== 'General' && a?.department === userDept;
            const bMatch = userDept !== 'General' && b?.department === userDept;
            if (aMatch === bMatch) return 0;
            return aMatch ? -1 : 1;
        });
    }, [courses, searchTerm, userDept]);

    const isEnrolled = (cid) => myEnrollments.some(e => e.course_id === cid);

    if (loading) return (
        <DashboardLayout role="student">
            <div className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[...Array(3)].map((_, i) => <SkeletonCard key={i} />)}
                </div>
                <div className="ui-card p-6">
                    <SkeletonTable rows={10} />
                </div>
            </div>
        </DashboardLayout>
    );

    if (error) {
        return (
            <DashboardLayout role="student">
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="text-center">
                        <p className="text-rose-600 mb-3 font-medium">{error}</p>
                        <button onClick={() => fetchData(true)} className="btn-primary">Retry Now</button>
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
                                    disabled={isEnrolled(rec.id) || enrollingId === rec.id}
                                    onClick={() => handleEnroll(rec.id)}
                                    className={isEnrolled(rec.id) ? 'w-full btn-secondary py-2 mt-auto opacity-50 cursor-not-allowed' : 'w-full btn-primary py-2 mt-auto flex justify-center items-center gap-2'}
                                >
                                    {enrollingId === rec.id ? (
                                        <>
                                            ...
                                        </>
                                    ) : (isEnrolled(rec.id) ? 'Enrolled' : 'Enroll')}
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
                    ) : prioritizedCourses.map((c, i) => (
                        <CourseCard 
                            key={c.id || i} 
                            course={c} 
                            isEnrolled={isEnrolled(c?.id)}
                            onEnroll={handleEnroll}
                            isEnrolling={enrollingId === c?.id}
                        />
                    ))}
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
                                <EnrollmentRow key={e.id || i} enrollment={e} />
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default StudentDashboard;
