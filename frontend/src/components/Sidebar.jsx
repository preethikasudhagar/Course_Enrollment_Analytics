import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    BookOpen,
    Users,
    LogOut,
    ChevronLeft,
    ChevronRight,
    GraduationCap,
    X,
    Settings as SettingsIcon
} from 'lucide-react';

const Sidebar = ({ role, isOpen, onClose }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.clear();
        navigate('/login');
    };

    const adminMenu = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/admin-dashboard' },
        { icon: BookOpen, label: 'Courses', path: '/admin/courses' },
        { icon: Users, label: 'Users', path: '/admin/users' },
        { icon: SettingsIcon, label: 'Settings', path: '/settings' },
    ];

    const facultyMenu = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/faculty-dashboard' },
    ];

    const studentMenu = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/student-dashboard' },
        { icon: BookOpen, label: 'Available Courses', path: '/student/courses' },
        { icon: GraduationCap, label: 'My Enrollments', path: '/student/my-enrollments' },
    ];

    const menuItems = { admin: adminMenu, faculty: facultyMenu, student: studentMenu };
    const currentMenu = menuItems[role] || studentMenu;

    return (
        <>
            {/* Mobile backdrop */}
            {isOpen && (
                <div className="fixed inset-0 bg-slate-900/30 z-40 md:hidden" onClick={onClose} />
            )}

            <aside className={`
                ${isCollapsed ? 'w-[72px]' : 'w-[240px]'} 
                ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
                bg-white border-r border-slate-200 h-screen transition-all duration-300 flex flex-col z-50 fixed md:sticky top-0 left-0
            `}>
                {/* Brand */}
                <div className="h-16 flex items-center justify-between px-5 border-b border-slate-100 shrink-0">
                    {!isCollapsed && (
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-blue-100 border border-blue-500">
                                <span className="text-xl">📊</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-sm font-black text-slate-900 leading-none tracking-tight">CourseInsight</span>
                                <span className="text-[9px] font-bold text-blue-500 uppercase tracking-widest mt-1">Analytics Intelligence</span>
                            </div>
                        </div>
                    )}
                    {isCollapsed && (
                        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-lg mx-auto shadow-md border border-blue-500">
                            📊
                        </div>
                    )}
                    <button onClick={onClose} className="md:hidden p-1 text-slate-400 hover:text-slate-900">
                        <X size={18} />
                    </button>
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="hidden md:flex absolute -right-3 top-6 w-6 h-6 bg-white border border-slate-200 rounded-full items-center justify-center text-slate-400 hover:text-blue-600 hover:border-blue-400 transition-all shadow-sm z-50"
                    >
                        {isCollapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                    {currentMenu.map((item, idx) => (
                        <NavLink
                            key={idx}
                            to={item.path}
                            className={({ isActive }) => `
                                flex items-center gap-3 px-3.5 py-3 rounded-xl transition-all duration-300 group relative
                                ${isActive
                                    ? 'bg-blue-50 text-blue-600 font-bold'
                                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                                }
                            `}
                            onClick={() => {
                                if (window.innerWidth < 768) onClose();
                            }}
                        >
                            <item.icon
                                size={18}
                                className={`${isCollapsed ? 'mx-auto' : ''} shrink-0`}
                            />
                            {!isCollapsed && <span className="text-sm truncate">{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>

                {/* Logout */}
                <div className="p-3 border-t border-slate-100 shrink-0">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors w-full group"
                    >
                        <LogOut size={18} className={`${isCollapsed ? 'mx-auto' : ''} shrink-0 text-slate-400 group-hover:text-red-500`} />
                        {!isCollapsed && <span className="text-sm font-medium">Logout</span>}
                    </button>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;
