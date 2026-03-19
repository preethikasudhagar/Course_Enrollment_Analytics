import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService, getErrorMessage } from '../services/api';
import { UserPlus, Mail, Lock, User, Shield, Building2 } from 'lucide-react';

const DEPARTMENTS = [
    'Computer Science and Engineering',
    'Information Technology',
    'Information Science and Engineering',
    'Artificial Intelligence and Data Science',
    'Electronics and Communication Engineering'
];

const Register = () => {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        role: 'student',
        department: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await authService.register(formData);
            navigate('/login');
        } catch (err) {
            setError(getErrorMessage(err, 'Registration failed'));
            setFormData(prev => ({ ...prev, password: '' }));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
                <div className="mx-auto h-12 w-12 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-sm mb-4">
                    <UserPlus size={24} />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Create an account</h2>
                <p className="mt-2 text-sm text-gray-500">Join the university analytics platform</p>
            </div>

            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-8 shadow-sm border border-gray-200 rounded-2xl relative overflow-hidden">
                    <form className="space-y-5" onSubmit={handleSubmit}>
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm font-medium text-center">
                                {error}
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Full Name</label>
                            <div className="relative">
                                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    name="name"
                                    type="text"
                                    required
                                    value={formData.name}
                                    className="block w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-colors placeholder:text-gray-400 shadow-sm"
                                    placeholder="John Doe"
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    name="email"
                                    type="email"
                                    required
                                    value={formData.email}
                                    className="block w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-colors placeholder:text-gray-400 shadow-sm"
                                    placeholder="name@university.edu"
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Role</label>
                            <div className="relative">
                                <Shield className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <select
                                    name="role"
                                    value={formData.role}
                                    className="block w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-colors cursor-pointer appearance-none shadow-sm"
                                    onChange={handleChange}
                                    style={{ WebkitAppearance: 'none', MozAppearance: 'none' }}
                                >
                                    <option value="student">Student</option>
                                    <option value="faculty">Faculty</option>
                                    <option value="admin">System Admin</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Department</label>
                            <div className="relative">
                                <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <select
                                    name="department"
                                    value={formData.department}
                                    required={formData.role === 'student'}
                                    className="block w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-colors cursor-pointer appearance-none shadow-sm"
                                    onChange={handleChange}
                                    style={{ WebkitAppearance: 'none', MozAppearance: 'none' }}
                                >
                                    <option value="">Select Department</option>
                                    {DEPARTMENTS.map((dept) => (
                                        <option key={dept} value={dept}>{dept}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    name="password"
                                    type="password"
                                    required
                                    value={formData.password}
                                    className="block w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-colors placeholder:text-gray-400 shadow-sm"
                                    placeholder="••••••••"
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors text-sm shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                        >
                            {loading ? 'Creating account...' : 'Create account'}
                        </button>
                    </form>

                    <div className="mt-8 text-center text-sm">
                        <span className="text-gray-500">Already have an account?</span>{' '}
                        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium transition-colors">Sign in</Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;
