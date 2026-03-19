import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { systemService, authService, getErrorMessage } from '../services/api';
import { Settings as SettingsIcon, Shield, Bell, Key, Save, CheckCircle } from 'lucide-react';

const Settings = () => {
    const [activeTab, setActiveTab] = useState('system');
    const [settings, setSettings] = useState({
        default_seat_increase: 10,
        auto_seat_expansion: true,
        enable_notifications: true,
        enable_email_alerts: false,
        max_seat_limit: 100,
        seat_expansion_threshold: 10
    });
    const [passwordData, setPasswordData] = useState({
        current_password: '',
        new_password: '',
        confirm_password: ''
    });
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState({ text: '', type: '' });

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await systemService.getSettings();
                setSettings(res || settings);
            } catch (err) {
                console.error("Failed to load settings");
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const showMessage = (text, type = 'success') => {
        setMessage({ text, type });
        setTimeout(() => setMessage({ text: '', type: '' }), 3000);
    };

    const handleSystemSave = async (e) => {
        e.preventDefault();
        try {
            await systemService.updateSettings(settings);
            showMessage("System settings updated successfully.");
        } catch (err) {
            showMessage("Failed to update settings.", "error");
        }
    };

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        if (passwordData.new_password !== passwordData.confirm_password) {
            showMessage("New passwords do not match.", "error");
            return;
        }
        try {
            await authService.changePassword({
                current_password: passwordData.current_password,
                new_password: passwordData.new_password
            });
            showMessage("Password changed successfully.");
            setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
        } catch (err) {
            showMessage(getErrorMessage(err, "Failed to change password."), "error");
        }
    };

    if (loading) return (
        <DashboardLayout role="admin">
            <div className="flex items-center justify-center h-64 text-gray-500">
                <SettingsIcon className="animate-spin mr-2" size={20} /> Loading settings...
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout role="admin">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-gray-900">Platform Settings</h1>
                    <p className="text-sm text-gray-500 mt-1">Manage global system configurations and account security.</p>
                </div>

                {message.text && (
                    <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${message.type === 'error' ? 'bg-red-50 text-red-700 border-l-4 border-red-500' : 'bg-green-50 text-green-700 border-l-4 border-green-500'}`}>
                        <CheckCircle size={20} className={message.type === 'error' ? 'text-red-500' : 'text-green-500'} />
                        <p className="font-medium text-sm">{message.text}</p>
                    </div>
                )}

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col md:flex-row">
                    {/* Sidebar Tabs */}
                    <div className="w-full md:w-64 bg-gray-50 border-b md:border-b-0 md:border-r border-gray-200 p-4 space-y-1 shrink-0">
                        <button
                            onClick={() => setActiveTab('system')}
                            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'system' ? 'bg-white text-blue-600 shadow-sm border border-gray-200' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
                        >
                            <SettingsIcon size={18} /> System Defaults
                        </button>
                        <button
                            onClick={() => setActiveTab('security')}
                            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'security' ? 'bg-white text-blue-600 shadow-sm border border-gray-200' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
                        >
                            <Shield size={18} /> Global Policies
                        </button>
                        <button
                            onClick={() => setActiveTab('account')}
                            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'account' ? 'bg-white text-blue-600 shadow-sm border border-gray-200' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
                        >
                            <Key size={18} /> Security & Auth
                        </button>
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 p-6 md:p-8 min-h-[400px]">
                        {activeTab === 'system' && (
                            <div className="animate-in fade-in duration-300">
                                <h2 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-3 mb-6">Automation Settings</h2>
                                <form onSubmit={handleSystemSave} className="space-y-6">
                                    <div className="flex items-center justify-between pb-4 border-b border-gray-100">
                                        <div>
                                            <p className="font-medium text-gray-900 text-sm">Auto Seat Expansion</p>
                                            <p className="text-xs text-gray-500 mt-1 w-3/4">Automatically increase limits when course capacity is full to prevent registration blocks.</p>
                                        </div>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" className="sr-only peer" checked={settings.auto_seat_expansion} onChange={(e) => setSettings({ ...settings, auto_seat_expansion: e.target.checked })} />
                                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                        </label>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Default Seat Increase Volume</label>
                                        <input
                                            type="number"
                                            className="w-full max-w-xs bg-white border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 text-sm"
                                            value={settings.default_seat_increase}
                                            onChange={(e) => setSettings({ ...settings, default_seat_increase: parseInt(e.target.value) })}
                                        />
                                        <p className="text-xs text-gray-500 mt-2">The number of seats added each time expansion is triggered.</p>
                                    </div>

                                    <div className="pt-4 border-t border-gray-100">
                                        <button type="submit" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-colors shadow-sm">
                                            <Save size={16} /> Save System Defaults
                                        </button>
                                    </div>
                                </form>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <div className="animate-in fade-in duration-300">
                                <h2 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-3 mb-6">Global Limits & Policies</h2>
                                <form onSubmit={handleSystemSave} className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-6 border-b border-gray-100">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Global Seat Limit</label>
                                            <input
                                                type="number"
                                                className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:border-blue-400 text-sm"
                                                value={settings.max_seat_limit}
                                                onChange={(e) => setSettings({ ...settings, max_seat_limit: parseInt(e.target.value) })}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">Expansion Threshold (%)</label>
                                            <input
                                                type="number"
                                                className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:border-blue-400 text-sm"
                                                value={settings.seat_expansion_threshold}
                                                onChange={(e) => setSettings({ ...settings, seat_expansion_threshold: parseInt(e.target.value) })}
                                            />
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium text-gray-900 text-sm flex items-center gap-2"><Bell size={16} className="text-gray-400" /> Enable Global Notifications</p>
                                            <p className="text-xs text-gray-500 mt-1">Broadcast notifications to users on major changes.</p>
                                        </div>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" className="sr-only peer" checked={settings.enable_notifications} onChange={(e) => setSettings({ ...settings, enable_notifications: e.target.checked })} />
                                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                        </label>
                                    </div>

                                    <div className="pt-4 border-t border-gray-100">
                                        <button type="submit" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-colors shadow-sm">
                                            <Save size={16} /> Save Policies
                                        </button>
                                    </div>
                                </form>
                            </div>
                        )}

                        {activeTab === 'account' && (
                            <div className="animate-in fade-in duration-300 max-w-md">
                                <h2 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-3 mb-6">Change Password</h2>
                                <form onSubmit={handlePasswordChange} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                                        <input
                                            type="password" required
                                            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:border-blue-400 text-sm"
                                            value={passwordData.current_password}
                                            onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                                        <input
                                            type="password" required minLength={6}
                                            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:border-blue-400 text-sm"
                                            value={passwordData.new_password}
                                            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                                        <input
                                            type="password" required minLength={6}
                                            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:border-blue-400 text-sm"
                                            value={passwordData.confirm_password}
                                            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                                        />
                                    </div>
                                    <div className="pt-4 border-t border-gray-100 mt-6">
                                        <button type="submit" className="w-full flex justify-center items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-colors shadow-sm">
                                            <Key size={16} /> Update Password
                                        </button>
                                    </div>
                                </form>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default Settings;
