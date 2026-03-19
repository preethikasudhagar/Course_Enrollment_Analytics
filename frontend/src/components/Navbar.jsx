import React, { useState, useEffect, useRef } from 'react';
import { Bell, Menu, LogOut, Settings, User as UserIcon, CheckCheck } from 'lucide-react';
import NotificationPanel from './NotificationPanel';
import { authService, notificationService } from '../services/api';
import { useNavigate } from 'react-router-dom';

const Navbar = ({ onMenuClick }) => {
    const getUser = () => {
        try {
            const stored = localStorage.getItem('user');
            return stored ? JSON.parse(stored) : null;
        } catch {
            return null;
        }
    };
    const user = getUser() || { email: 'user@example.com', role: 'visitor' };
    const [notifOpen, setNotifOpen] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const [profileOpen, setProfileOpen] = useState(false);
    const profileRef = useRef(null);
    const navigate = useNavigate();

    // Close profile dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (profileRef.current && !profileRef.current.contains(event.target)) setProfileOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Fetch + poll unread count every 30 seconds
    useEffect(() => {
        const fetchUnread = async () => {
            try {
                const res = await notificationService.getUnreadCount();
                setUnreadCount(Number(res?.unread_count || 0));
            } catch {
                setUnreadCount(0);
            }
        };
        fetchUnread();
        const interval = setInterval(fetchUnread, 30000);
        window.addEventListener('refreshNotifications', fetchUnread);
        return () => {
            clearInterval(interval);
            window.removeEventListener('refreshNotifications', fetchUnread);
        };
    }, []);

    const handleLogout = () => {
        authService.logout();
        navigate('/login');
    };

    const displayName = user.name || (user.email ? user.email.split('@')[0] : 'User');

    return (
        <>
            <nav className="h-16 bg-white/95 backdrop-blur-sm border-b border-slate-200 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
                <div className="flex items-center gap-4">
                    <button
                        type="button"
                        className="md:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
                        onClick={onMenuClick}
                    >
                        <Menu size={20} />
                    </button>
                    <span className="hidden md:block text-lg font-bold text-slate-900 tracking-tight">
                        Institutional Analytics
                    </span>
                </div>

                <div className="flex items-center gap-4">
                    {/* Notification Bell */}
                    <div className="relative">
                        <button
                            type="button"
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); setNotifOpen(!notifOpen); }}
                            className="p-2.5 text-slate-500 hover:bg-slate-100 hover:text-blue-600 rounded-xl transition-colors relative"
                        >
                            <Bell size={20} />
                            {unreadCount > 0 && (
                                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-blue-600 text-white text-[10px] font-bold rounded-full border-2 border-white flex items-center justify-center">
                                    {unreadCount > 99 ? '99+' : unreadCount}
                                </span>
                            )}
                        </button>
                    </div>

                    {/* Divider */}
                    <div className="w-px h-7 bg-slate-200 hidden md:block"></div>

                    {/* User Profile */}
                    <div className="relative" ref={profileRef}>
                        <div
                            onClick={() => setProfileOpen(!profileOpen)}
                            className="flex items-center gap-3 cursor-pointer hover:bg-slate-50 p-1.5 rounded-xl transition-colors"
                        >
                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 text-white flex items-center justify-center font-semibold text-sm shadow-sm">
                                {(displayName || 'U').charAt(0).toUpperCase()}
                            </div>
                            <div className="flex flex-col hidden sm:flex">
                                <span className="text-sm font-semibold text-slate-900 leading-none">{displayName}</span>
                                <span className="text-[11px] text-slate-500 capitalize mt-0.5 leading-none">{user.role}</span>
                            </div>
                        </div>

                        {profileOpen && (
                            <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50">
                                <div className="px-4 py-3 border-b border-slate-100">
                                    <p className="text-sm text-slate-900 font-semibold">{displayName}</p>
                                    <p className="text-xs text-slate-500 truncate">{user.email}</p>
                                </div>
                                <div className="py-1">
                                    <button
                                        type="button"
                                        onClick={() => { navigate('/profile'); setProfileOpen(false); }}
                                        className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 hover:text-blue-600 flex items-center gap-3 transition-colors"
                                    >
                                        <UserIcon size={16} /> My Profile
                                    </button>
                                    {user.role === 'admin' && (
                                        <button
                                            type="button"
                                            onClick={() => { navigate('/settings'); setProfileOpen(false); }}
                                            className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 hover:text-blue-600 flex items-center gap-3 transition-colors"
                                        >
                                            <Settings size={16} /> System Settings
                                        </button>
                                    )}
                                </div>
                                <div className="border-t border-slate-100 pt-1 pb-1">
                                    <button
                                        type="button"
                                        onClick={handleLogout}
                                        className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors font-medium"
                                    >
                                        <LogOut size={16} /> Sign out
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </nav>
            <NotificationPanel isOpen={notifOpen} onClose={() => setNotifOpen(false)} onUnreadChange={setUnreadCount} />
        </>
    );
};

export default Navbar;
