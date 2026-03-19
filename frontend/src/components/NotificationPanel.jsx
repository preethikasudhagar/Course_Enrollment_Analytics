import React, { useState, useEffect } from 'react';
import { Bell, X, CheckCircle, AlertTriangle, Plus, Info, ExternalLink, Trash2, CheckCheck } from 'lucide-react';
import { notificationService } from '../services/api';

const CATEGORY_CONFIG = {
    'Seat Alert': {
        icon: AlertTriangle,
        iconBg: 'bg-amber-100',
        iconColor: 'text-amber-600',
        dotColor: 'bg-amber-500',
    },
    'Enrollment': {
        icon: CheckCircle,
        iconBg: 'bg-emerald-100',
        iconColor: 'text-emerald-600',
        dotColor: 'bg-emerald-500',
    },
    'New Course': {
        icon: Plus,
        iconBg: 'bg-blue-100',
        iconColor: 'text-blue-600',
        dotColor: 'bg-blue-500',
    },
    'System Notice': {
        icon: Info,
        iconBg: 'bg-slate-100',
        iconColor: 'text-slate-600',
        dotColor: 'bg-slate-400',
    },
};

function categorize(message) {
    const msg = (message || '').toLowerCase();
    if (msg.includes('seat') || msg.includes('capacity') || msg.includes('limit')) return 'Seat Alert';
    if (msg.includes('enrolled') || msg.includes('enrollment') || msg.includes('enroll')) return 'Enrollment';
    if (msg.includes('new course') || msg.includes('created') || msg.includes('course added')) return 'New Course';
    return 'System Notice';
}

function timeAgo(timestamp) {
    if (!timestamp) return '';
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
}

const NotificationPanel = ({ isOpen, onClose, onUnreadChange }) => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen) {
            fetchNotifications();
        }
    }, [isOpen]);

    const fetchNotifications = async () => {
        try {
            setLoading(true);
            const res = await notificationService.getAll();
            const list = Array.isArray(res) ? res : [];
            setNotifications(list);
            const unread = list.filter((n) => n?.status === 'unread').length;
            onUnreadChange?.(unread);
        } catch (err) {
            console.error('Failed to fetch notifications');
            setNotifications([]);
            onUnreadChange?.(0);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (notification) => {
        if (!notification?.id || notification?.status !== 'unread') return;
        try {
            await notificationService.markRead(notification.id);
            setNotifications((prev) => {
                const updated = prev.map((n) => n.id === notification.id ? { ...n, status: 'read' } : n);
                const unread = updated.filter((n) => n?.status === 'unread').length;
                onUnreadChange?.(unread);
                return updated;
            });
        } catch (err) {
            console.error('Failed to mark notification as read');
        }
    };

    const markAllRead = async () => {
        try {
            await notificationService.markAllRead();
            setNotifications((prev) => {
                const updated = prev.map((n) => ({ ...n, status: 'read' }));
                onUnreadChange?.(0);
                return updated;
            });
        } catch (err) {
            console.error('Failed to mark all as read');
        }
    };

    if (!isOpen) return null;

    const unreadCount = notifications.filter((n) => n?.status === 'unread').length;

    return (
        <div className="fixed inset-0 z-[100] overflow-hidden">
            <div className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm transition-opacity" onClick={onClose}></div>
            <div className="absolute right-0 top-0 h-full w-full max-w-sm bg-white shadow-2xl flex flex-col transform transition-transform duration-300">
                {/* Header */}
                <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                            <Bell size={18} className="text-blue-600" />
                            Notifications
                            {unreadCount > 0 && (
                                <span className="ml-1 px-2 py-0.5 bg-blue-600 text-white text-[10px] font-bold rounded-full">
                                    {unreadCount}
                                </span>
                            )}
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">Stay updated with system alerts</p>
                    </div>
                    <div className="flex items-center gap-2">
                        {unreadCount > 0 && (
                            <button
                                onClick={markAllRead}
                                className="p-2 hover:bg-blue-50 rounded-lg transition-colors text-blue-600 text-xs font-semibold flex items-center gap-1"
                                title="Mark all as read"
                            >
                                <CheckCheck size={16} />
                            </button>
                        )}
                        <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-900">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Notification List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {loading ? (
                        <div className="py-20 text-center">
                            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-sm text-slate-500">Loading notifications...</p>
                        </div>
                    ) : notifications.length === 0 ? (
                        <div className="py-20 text-center">
                            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Bell className="text-slate-300" size={28} />
                            </div>
                            <p className="text-slate-900 font-semibold">No new notifications</p>
                            <p className="text-sm text-slate-500 mt-1">You're all caught up!</p>
                        </div>
                    ) : (
                        notifications.map((n, i) => {
                            const category = n.category || categorize(n.message);
                            const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG['System Notice'];
                            const IconComp = config.icon;

                            return (
                                <button
                                    key={n.id || i}
                                    onClick={() => markAsRead(n)}
                                    className={`w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer group ${n.status === 'unread'
                                            ? 'bg-blue-50/40 border-blue-100 hover:bg-blue-50/70'
                                            : 'bg-white border-slate-100 hover:border-slate-200 hover:bg-slate-50/50'
                                        }`}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={`p-2 rounded-lg shrink-0 ${config.iconBg}`}>
                                            <IconComp size={16} className={config.iconColor} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-0.5">
                                                <span className={`text-xs font-bold uppercase tracking-wide ${config.iconColor}`}>
                                                    {category}
                                                </span>
                                                <span className="text-[11px] text-slate-400 whitespace-nowrap ml-2">
                                                    {timeAgo(n.timestamp)}
                                                </span>
                                            </div>
                                            <p className={`text-sm leading-snug mt-1 ${n.status === 'unread' ? 'text-slate-900 font-medium' : 'text-slate-600'
                                                }`}>
                                                {n?.message || 'Notification'}
                                            </p>
                                        </div>
                                        {n.status === 'unread' && (
                                            <div className={`w-2 h-2 rounded-full shrink-0 mt-2 ${config.dotColor}`}></div>
                                        )}
                                    </div>
                                </button>
                            );
                        })
                    )}
                </div>

                {/* Footer */}
                {notifications.length > 0 && (
                    <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                        <button
                            onClick={() => { setNotifications([]); onUnreadChange?.(0); }}
                            className="w-full bg-white border border-slate-200 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors shadow-sm flex items-center justify-center gap-2"
                        >
                            <Trash2 size={14} /> Clear all
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotificationPanel;
