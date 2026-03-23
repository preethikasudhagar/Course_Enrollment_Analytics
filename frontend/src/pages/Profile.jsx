import React, { useState, useEffect } from 'react';
import { userService, getErrorMessage } from '../services/api';
import { Camera, User as UserIcon, Loader2, Phone, Mail, Building, Shield, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Profile = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [phone, setPhone] = useState('');
    const [photoFile, setPhotoFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [msg, setMsg] = useState({ text: '', type: '' });

    const handleClose = () => {
        try {
            const localUser = JSON.parse(localStorage.getItem('user') || '{}');
            const role = localUser?.role;
            const homeMap = {
                admin: '/admin-dashboard',
                faculty: '/faculty-dashboard',
                student: '/student-dashboard'
            };
            navigate(homeMap[role] || -1);
        } catch {
            navigate(-1);
        }
    };

    useEffect(() => {
        const loadProfile = async () => {
            try {
                setLoading(true);
                const data = await userService.getProfile();
                setUser(data);
                setPhone(data.phone || '');
                if (data?.name) {
                    const localUser = JSON.parse(localStorage.getItem('user') || '{}');
                    localStorage.setItem('user', JSON.stringify({ ...localUser, name: data.name }));
                }
                if (data && data.profile_photo) {
                    const baseUrl = 'http://localhost:8000';
                    const photoPath = data.profile_photo.startsWith('/') ? data.profile_photo : `/${data.profile_photo}`;
                    setPreview(`${baseUrl}${photoPath}`);
                }
            } catch (err) {
                const denied = err?.response?.status === 401 || err?.response?.status === 403;
                setMsg({ text: denied ? 'Access denied. Please log in again.' : getErrorMessage(err, 'Failed to load profile'), type: 'error' });
            } finally {
                setLoading(false);
            }
        };
        loadProfile();
    }, []);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const maxSizeMb = 2;
            const allowed = ['image/jpeg', 'image/png', 'image/webp'];
            if (!allowed.includes(file.type)) {
                setMsg({ text: 'Only JPG, PNG, or WEBP files are allowed.', type: 'error' });
                return;
            }
            if (file.size > maxSizeMb * 1024 * 1024) {
                setMsg({ text: 'Profile photo must be 2MB or less.', type: 'error' });
                return;
            }
            setPhotoFile(file);
            setPreview(URL.createObjectURL(file));
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('phone', phone);
            if (photoFile) {
                formData.append('profile_photo', photoFile);
            }

            const updated = await userService.updateProfile(formData);
            setUser(updated);
            if (updated?.name) {
                const localUser = JSON.parse(localStorage.getItem('user') || '{}');
                localStorage.setItem('user', JSON.stringify({ ...localUser, name: updated.name }));
            }
            if (updated?.profile_photo) {
                const baseUrl = 'http://localhost:8000';
                const photoPath = updated.profile_photo.startsWith('/') ? updated.profile_photo : `/${updated.profile_photo}`;
                setPreview(`${baseUrl}${photoPath}`);
            }
            setMsg({ text: 'Profile updated successfully!', type: 'success' });

            // Auto-clear message after 3 seconds
            setTimeout(() => setMsg({ text: '', type: '' }), 3000);
        } catch (err) {
            setMsg({ text: 'Update failed. Please try again.', type: 'error' });
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[60vh] text-[#ffd700]">
            <Loader2 className="animate-spin mr-2" /> Loading Profile...
        </div>
    );

    return (
        <div className="max-w-3xl mx-auto p-4 sm:p-8">
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm relative">
                <button
                    onClick={handleClose}
                    className="btn-secondary absolute top-4 right-4 z-10"
                    aria-label="Close profile"
                >
                    <X size={16} /> Close
                </button>
                <div className="h-32 bg-gradient-to-r from-blue-50 to-slate-50 border-b border-slate-100" />

                <div className="px-8 pb-8 -mt-12">
                    <div className="flex flex-col sm:flex-row items-end gap-6 mb-8">
                        <div className="relative group">
                            <div className="w-32 h-32 rounded-2xl overflow-hidden border-4 border-white bg-slate-100 shadow-xl flex items-center justify-center">
                                {preview ? (
                                    <img src={preview} alt="Profile" className="w-full h-full object-cover" loading="lazy" />
                                ) : (
                                    <UserIcon size={64} className="text-gray-600" />
                                )}
                            </div>
                            <label className="absolute bottom-2 right-2 p-2 bg-blue-600 text-white rounded-lg cursor-pointer transform hover:scale-110 transition-transform shadow-lg">
                                <Camera size={20} />
                                <input type="file" hidden onChange={handleFileChange} accept="image/*" />
                            </label>
                        </div>

                        <div className="flex-1 pb-2">
                            <h2 className="text-3xl font-bold text-slate-900 mb-1">{user?.name || 'Academic Professional'}</h2>
                            <div className="flex flex-wrap gap-3">
                                <span className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-semibold uppercase tracking-wider">
                                    <Shield size={12} /> {user?.role}
                                </span>
                                <span className="flex items-center gap-1.5 px-3 py-1 bg-slate-50 text-slate-500 rounded-full text-xs font-semibold uppercase tracking-wider border border-slate-200">
                                    <Building size={12} /> {user?.department || 'University'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-100 pb-2 mb-4">Contact Information</h3>

                            <div>
                                <label className="block text-sm text-gray-500 mb-1.5 ml-1">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                                    <input
                                        type="email"
                                        value={user?.email || ''}
                                        disabled
                                        className="w-full pl-10 pr-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-slate-500 cursor-not-allowed opacity-70"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-slate-500 mb-1.5 ml-1">Phone Number</label>
                                <div className="relative">
                                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-600" size={18} />
                                    <input
                                        type="text"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        placeholder="+1 (555) 000-0000"
                                        className="ui-input pl-10 pr-4 py-3"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-100 pb-2 mb-4">Account Status</h3>
                            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-500">Member Since</span>
                                    <span className="text-slate-700">Default Group</span>
                                </div>
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-500">Security Level</span>
                                    <span className="text-green-400 font-medium">Standard</span>
                                </div>
                                <div className="pt-2">
                                    <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-600 w-[85%]" />
                                    </div>
                                    <p className="text-[10px] text-slate-500 mt-1.5 uppercase tracking-tighter">Profile Completion: 85%</p>
                                </div>
                            </div>

                            {msg.text && (
                                <div className={`p-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300 ${msg.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
                                    }`}>
                                    <div className={`w-2 h-2 rounded-full ${msg.type === 'success' ? 'bg-green-400' : 'bg-red-400'}`} />
                                    <span className="text-sm font-medium">{msg.text}</span>
                                </div>
                            )}

                            <button
                                type="submit"
                                className="btn-primary w-full py-3.5"
                            >
                                Update Profile
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Profile;
