import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { userService } from '../services/api';
import { User, Shield, Trash2, Mail, BadgeCheck, Users, Search, Filter } from 'lucide-react';

const ManageUsers = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchUsers = async () => {
        try {
            const res = await userService.getAll();
            setUsers(res || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleUpdateRole = async (id, newRole) => {
        try {
            await userService.updateRole(id, newRole);
            setMessage({ type: 'success', text: `Role updated to ${newRole}` });
            fetchUsers();
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to update role' });
        }
        setTimeout(() => setMessage(null), 3000);
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to remove this user from the system?')) {
            try {
                await userService.delete(id);
                setMessage({ type: 'success', text: 'User successfully removed' });
                fetchUsers();
            } catch (err) {
                setMessage({ type: 'error', text: 'Failed to remove user' });
            }
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const filteredUsers = (users || []).filter(u =>
        (u.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (u.email || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return (
        <DashboardLayout role="admin">
            <div className="flex items-center justify-center h-64 text-gray-500">
                <p>Loading user directory...</p>
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout role="admin">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Manage Users</h1>
                    <p className="text-gray-500 text-sm mt-1">Manage personnel, roles, and system access</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search users..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 w-full md:w-64 shadow-sm"
                        />
                    </div>
                </div>
            </div>

            {message && (
                <div className={`mb-8 p-4 rounded-xl border flex items-center justify-between shadow-sm ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-red-50 border-red-200 text-red-700'
                    }`}>
                    <div className="flex items-center gap-3 text-sm font-medium">
                        <BadgeCheck size={18} />
                        {message.text}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredUsers.length === 0 ? (
                    <div className="col-span-full py-12 text-center text-gray-500 bg-white border border-gray-200 rounded-xl shadow-sm">
                        No users found matching your search.
                    </div>
                ) : filteredUsers.map((u) => (
                    <div key={u.id} className="bg-white border border-gray-200 p-6 rounded-xl hover:shadow-md transition-shadow relative group shadow-sm flex flex-col">
                        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                                onClick={() => handleDelete(u.id)}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent"
                                title="Remove User"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>

                        <div className="flex flex-col items-center text-center mb-6">
                            <div className="w-16 h-16 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4">
                                <User size={28} />
                            </div>
                            <h4 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{u.name}</h4>
                            <div className="flex items-center gap-1.5 text-gray-500 text-sm mt-1">
                                <Mail size={14} />
                                <span className="truncate max-w-[180px]" title={u.email}>{u.email}</span>
                            </div>
                        </div>

                        <div className="mt-auto space-y-4 pt-5 border-t border-gray-100">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1.5">
                                    <Shield size={14} className="text-gray-400" />
                                    <span className="text-xs font-medium text-gray-500">Role</span>
                                </div>
                                <span className={`text-xs font-medium px-2.5 py-1 rounded-md ${u.role === 'admin' ? 'bg-gray-900 text-white' :
                                    u.role === 'faculty' ? 'bg-blue-100 text-blue-700' :
                                        'bg-gray-100 text-gray-600'
                                    }`}>
                                    {((u.role || 'student').charAt(0).toUpperCase() + (u.role || 'student').slice(1))}
                                </span>
                            </div>

                            <div className="relative">
                                <select
                                    value={u.role || 'student'}
                                    onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                                    className="w-full bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-700 py-2.5 pl-3 pr-8 outline-none appearance-none cursor-pointer focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all font-medium"
                                >
                                    <option value="student">Student</option>
                                    <option value="faculty">Faculty</option>
                                    <option value="admin">System Admin</option>
                                </select>
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                                    <Filter size={14} />
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </DashboardLayout>
    );
};

export default ManageUsers;
