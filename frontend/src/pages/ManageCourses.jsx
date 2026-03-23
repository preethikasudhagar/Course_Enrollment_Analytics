import React, { useState, useEffect, useCallback, useMemo, memo } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { courseService } from '../services/api';
import { Plus, Edit, Trash2, X, Check, BookOpen, Layers, Search } from 'lucide-react';

const CourseItem = memo(({ course, onEdit, onDelete }) => {
    const limit = Number(course.seat_limit || 0);
    const enrolled = Number(course.enrolled_students || 0);
    const remaining = Math.max(0, limit - enrolled);
    const status = remaining <= 5 ? 'High Demand' : 'Open';
    
    return (
        <tr className="hover:bg-gray-50 transition-colors">
            <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                        <BookOpen size={20} />
                    </div>
                    <div>
                        <p className="font-medium text-gray-900">
                            {course.course_name}
                            {course.enrolled_students > 0 && course.enrolled_students >= (course.seat_limit * 0.8) && (
                                <span className="ml-2 px-2 py-0.5 bg-amber-100 text-amber-700 text-[10px] font-bold rounded-full border border-amber-200" title="High Enrollment Volume">🔥 Trending</span>
                            )}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">ID: {course.id}</p>
                    </div>
                </div>
            </td>
            <td className="px-6 py-4">
                <span className="px-2.5 py-1 bg-gray-100 text-gray-600 rounded-md text-xs font-medium">
                    {course.department}
                </span>
            </td>
            <td className="px-6 py-4 text-gray-900 font-medium">{course.seat_limit}</td>
            <td className="px-6 py-4">
                <span className="text-sm font-semibold text-slate-700">{remaining}</span>
            </td>
            <td className="px-6 py-4">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${status === 'High Demand'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-emerald-100 text-emerald-700'
                    }`}>
                    {status}
                </span>
            </td>
            <td className="px-6 py-4 text-right space-x-2">
                <button
                    onClick={() => onEdit(course)}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-transparent"
                    title="Edit"
                >
                    <Edit size={16} />
                </button>
                <button
                    onClick={() => onDelete(course.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent"
                    title="Delete"
                >
                    <Trash2 size={16} />
                </button>
            </td>
        </tr>
    );
});

const ManageCourses = () => {
    const [courses, setCourses] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);
    const initialFormState = {
        course_name: '',
        course_code: '',
        department: '',
        faculty_assigned: '',
        seat_limit: 40,
        auto_expand_enabled: true,
        max_seat_limit: 200,
        course_description: '',
        course_duration: '',
        credits: 3
    };
    const [formData, setFormData] = useState(initialFormState);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchCourses = useCallback(async () => {
        try {
            const res = await courseService.getAll();
            setCourses(res || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCourses();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingCourse) {
                await courseService.update(editingCourse.id, formData);
            } else {
                await courseService.create(formData);
            }
            setIsModalOpen(false);
            setEditingCourse(null);
            setFormData(initialFormState);
            fetchCourses();
        } catch (err) {
            alert('Action failed');
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure? This will remove all associated enrollments.')) {
            try {
                await courseService.delete(id);
                fetchCourses();
            } catch (err) {
                alert('Delete failed');
            }
        }
    };

    const filteredCourses = useMemo(() => {
        const lowerSearch = searchTerm.toLowerCase();
        return courses.filter((c) =>
            (c?.course_name || '').toLowerCase().includes(lowerSearch) ||
            (c?.department || '').toLowerCase().includes(lowerSearch) ||
            (c?.course_code || '').toLowerCase().includes(lowerSearch)
        );
    }, [courses, searchTerm]);

    if (loading) return (
        <DashboardLayout role="admin">
            <div className="flex items-center justify-center h-64 text-gray-500">
                <p>Loading course directory...</p>
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout role="admin">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Manage Courses</h1>
                    <p className="text-gray-500 text-sm mt-1">Add, edit, and manage university courses</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search courses..."
                            className="ui-input pl-9 pr-4 py-2 w-full md:w-64 shadow-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button
                        onClick={() => { setEditingCourse(null); setFormData(initialFormState); setIsModalOpen(true); }}
                        className="btn-primary whitespace-nowrap"
                    >
                        <Plus size={16} /> Add Course
                    </button>
                </div>
            </div>

            <div className="ui-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4">Course Details</th>
                                <th className="px-6 py-4">Department</th>
                                <th className="px-6 py-4">Capacity</th>
                                <th className="px-6 py-4">Remaining</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 text-gray-700">
                            {filteredCourses.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                                        No courses found matching your search.
                                    </td>
                                </tr>
                            ) : filteredCourses.map((c) => (
                                <CourseItem 
                                    key={c.id} 
                                    course={c} 
                                    onEdit={(course) => {
                                        setEditingCourse(course);
                                        setFormData({
                                            course_name: course.course_name || '',
                                            course_code: course.course_code || '',
                                            department: course.department || '',
                                            faculty_assigned: course.faculty_assigned || '',
                                            seat_limit: course.seat_limit || 40,
                                            auto_expand_enabled: course.auto_expand_enabled ?? true,
                                            max_seat_limit: course.max_seat_limit || 200,
                                            course_description: course.course_description || '',
                                            course_duration: course.course_duration || '',
                                            credits: course.credits || 3
                                        });
                                        setIsModalOpen(true);
                                    }}
                                    onDelete={handleDelete}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {isModalOpen && (
                <div className="ui-modal">
                    <div className="ui-modal-panel max-w-2xl overflow-hidden">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-slate-900">{editingCourse ? 'Edit Course' : 'Add New Course'}</h3>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-md hover:bg-slate-100">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
                                <div>
                                    <label className="ui-label">Course Name</label>
                                    <input
                                        type="text"
                                        required
placeholder="e.g., 3D Modelling"
                                        className="ui-input"
                                        value={formData.course_name}
                                        onChange={(e) => setFormData({ ...formData, course_name: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="ui-label">Course Code</label>
                                    <input
                                        type="text"
                                        placeholder="e.g., CS101"
                                        className="ui-input"
                                        value={formData.course_code}
                                        onChange={(e) => setFormData({ ...formData, course_code: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="ui-label">Department</label>
                                    <input
                                        type="text"
                                        required
                                        placeholder="e.g., Computer Science"
                                        className="ui-input"
                                        value={formData.department}
                                        onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="ui-label">Faculty Assigned</label>
                                    <input
                                        type="text"
                                        placeholder="e.g., Dr. Smith"
                                        className="ui-input"
                                        value={formData.faculty_assigned}
                                        onChange={(e) => setFormData({ ...formData, faculty_assigned: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="ui-label">Course Duration</label>
                                    <input
                                        type="text"
                                        placeholder="e.g., 14 Weeks"
                                        className="ui-input"
                                        value={formData.course_duration}
                                        onChange={(e) => setFormData({ ...formData, course_duration: e.target.value })}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="ui-label">Seat Limit</label>
                                        <input
                                            type="number"
                                            required
                                            min="1"
                                            className="ui-input"
                                            value={formData.seat_limit}
                                            onChange={(e) => setFormData({ ...formData, seat_limit: parseInt(e.target.value) })}
                                        />
                                    </div>
                                    <div>
                                        <label className="ui-label">Credits</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="6"
                                            className="ui-input"
                                            value={formData.credits}
                                            onChange={(e) => setFormData({ ...formData, credits: parseInt(e.target.value) })}
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="ui-label">Max Seat Limit</label>
                                        <input
                                            type="number"
                                            min="1"
                                            className="ui-input"
                                            value={formData.max_seat_limit}
                                            onChange={(e) => setFormData({ ...formData, max_seat_limit: parseInt(e.target.value || '0') })}
                                        />
                                    </div>
                                    <div className="flex items-end pb-2">
                                        <label className="inline-flex items-center gap-3 text-sm font-medium text-slate-700">
                                            <input
                                                type="checkbox"
                                                checked={Boolean(formData.auto_expand_enabled)}
                                                onChange={(e) => setFormData({ ...formData, auto_expand_enabled: e.target.checked })}
                                                className="w-4 h-4 text-blue-600 border-slate-300 rounded"
                                            />
                                            Auto expand seats
                                        </label>
                                    </div>
                                </div>
                                <div className="md:col-span-2">
                                    <label className="ui-label">Course Description</label>
                                    <textarea
                                        rows="3"
                                        placeholder="Brief description of the course..."
                                        className="ui-input resize-none"
                                        value={formData.course_description}
                                        onChange={(e) => setFormData({ ...formData, course_description: e.target.value })}
                                    ></textarea>
                                </div>
                            </div>
                            <div className="pt-2 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="btn-secondary"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary"
                                >
                                    <Check size={16} />
                                    {editingCourse ? 'Save Changes' : 'Create Course'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
};

export default ManageCourses;
