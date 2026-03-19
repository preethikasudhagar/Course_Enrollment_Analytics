import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { courseService, enrollmentService, getErrorMessage } from '../services/api';
import { ArrowRight, X, Zap, Loader2 } from 'lucide-react';

const AvailableCourses = () => {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [msg, setMsg] = useState({ text: '', type: '' });
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await courseService.getAll();
                setCourses(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error("Fetch courses error:", err);
                setError('Failed to load courses.');
            } finally {
                setLoading(false);
            }
        };
        fetchCourses();
    }, []);

    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape') setSelectedCourse(null);
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, []);

    const handleEnroll = async (id) => {
        try {
            if (!id) {
                setMsg({ text: 'Invalid course selection', type: 'error' });
                return;
            }
            const res = await enrollmentService.enroll(id);
            setMsg({ text: res.message || "Enrolled successfully!", type: 'success' });
            const updated = await courseService.getAll();
            setCourses(Array.isArray(updated) ? updated : []);
            window.dispatchEvent(new Event('refreshNotifications'));
        } catch (err) {
            setMsg({ text: getErrorMessage(err, "Enrollment failed"), type: 'error' });
        }
    };

    const closeModal = () => setSelectedCourse(null);

    if (loading) return (
        <DashboardLayout role="student">
            <div className="flex items-center justify-center min-h-[60vh] text-[#ffd700]">
                <Loader2 className="animate-spin mr-2" /> Exploring Courses...
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout role="student">
            <div className="p-4 md:p-8 min-h-screen text-slate-900">
                <div className="flex justify-between items-center mb-10">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 mb-2">Available Courses</h1>
                        <p className="text-slate-500">Expand your knowledge with the institutional catalog.</p>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-3 rounded-lg text-sm bg-red-50 border border-red-200 text-red-600">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {courses.length === 0 ? (
                        <div className="col-span-full text-center py-10 text-slate-400 border border-slate-200 rounded-2xl bg-white">
                            No data available
                        </div>
                    ) : courses.map(course => (
                        <div
                            key={course.id}
                            className="ui-card overflow-hidden group flex flex-col"
                        >
                            <div className="p-6 flex-1">
                                <div className="flex justify-between items-start mb-4">
                                    <span className="px-2 py-1 bg-blue-50 text-blue-600 text-[10px] font-bold uppercase tracking-wider rounded border border-blue-200">
                                        {course.department}
                                    </span>
                                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${course.demand_status === 'High Demand' ? 'bg-red-500/20 text-red-400' :
                                        course.demand_status === 'Medium Demand' ? 'bg-blue-100 text-blue-600' : 'bg-emerald-100 text-emerald-600'
                                        }`}>
                                        {course.demand_status}
                                    </span>
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 mb-1 group-hover:text-blue-600 transition-colors">{course.course_name}</h3>
                                <p className="text-slate-500 text-xs font-semibold mb-3">Instructor: {course.instructor || 'Staff'}</p>
                                <p className="text-slate-500 text-sm mb-4 line-clamp-2">{course.description || "Comprehensive course covering advanced concepts and industry best practices."}</p>

                                <div className="space-y-3 pt-4 border-t border-slate-100 mb-4">
                                    <div className="flex justify-between items-center text-xs text-slate-500">
                                        <span>Remaining: {(course.seat_limit || 0) - (course.enrolled_students || 0)}</span>
                                        <span className="text-blue-600 font-bold">{course.utilization_pct || 0}% Utilized</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full transition-all duration-1000 ${course.utilization_pct > 80 ? 'bg-red-500' :
                                                course.utilization_pct > 40 ? 'bg-blue-500' : 'bg-green-500'
                                                }`}
                                            style={{ width: `${course.utilization_pct}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => setSelectedCourse(course)}
                                className="w-full py-4 bg-slate-50 hover:bg-blue-600 hover:text-white transition-all font-bold flex items-center justify-center gap-2 border-t border-slate-100"
                            >
                                View Details <ArrowRight size={16} />
                            </button>
                        </div>
                    ))}
                </div>

                {/* Course Details Modal */}
                {selectedCourse && (
                    <div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-300"
                        onClick={(e) => {
                            if (e.target === e.currentTarget) closeModal();
                        }}
                    >
                        <div
                            className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 overflow-hidden shadow-2xl animate-in zoom-in-95 duration-300"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="relative h-48 bg-gradient-to-br from-blue-50 to-slate-50 p-8 flex items-end">
                                <button
                                    onClick={closeModal}
                                    className="absolute top-4 right-4 p-2 bg-white text-slate-500 rounded-full border border-slate-200 hover:bg-red-50 hover:text-red-600 transition-colors"
                                    aria-label="Close"
                                >
                                    <X size={20} />
                                </button>
                                <div>
                                    <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full mb-2 inline-block capitalize">
                                        {selectedCourse.department}
                                    </span>
                                    <h2 className="text-3xl font-bold text-slate-900">{selectedCourse.course_name}</h2>
                                    <p className="text-slate-500">{selectedCourse.course_code || 'CRN-001'}</p>
                                </div>
                            </div>

                            <div className="p-8 space-y-6">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                        <div className="text-slate-500 text-xs mb-1 uppercase tracking-wider">Faculty</div>
                                        <div className="text-slate-900 font-semibold">{selectedCourse.faculty_assigned || 'Not Assigned'}</div>
                                    </div>
                                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                        <div className="text-slate-500 text-xs mb-1 uppercase tracking-wider">Seats Available</div>
                                        <div className="text-blue-600 font-bold text-lg">
                                            {Number(selectedCourse.seat_limit || 0) - Number(selectedCourse.enrolled_students || 0)} / {selectedCourse.seat_limit || 0}
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">Description</h4>
                                    <p className="text-slate-600 leading-relaxed text-lg">
                                        {selectedCourse.description || "Explore advanced concepts and practical applications in this comprehensive institutional course designed for modern industry requirements."}
                                    </p>
                                </div>

                                <button
                                    className="btn-primary w-full py-4 text-lg"
                                    onClick={() => {
                                        handleEnroll(selectedCourse.id);
                                        closeModal();
                                    }}
                                >
                                    <Zap size={20} /> Confirm Enrollment
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {msg.text && (
                    <div className={`fixed bottom-8 right-8 p-4 rounded-xl z-50 animate-in slide-in-from-bottom-5 shadow-lg ${msg.type === 'success' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-red-50 text-red-600 border border-red-200'
                        }`}>
                        {msg.text}
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default AvailableCourses;
