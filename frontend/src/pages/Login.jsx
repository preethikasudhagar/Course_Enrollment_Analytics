import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService, getErrorMessage } from '../services/api';
import { Mail, Lock, LogIn } from 'lucide-react';

const Login = () => {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleChange = (e) => {
        setCredentials({ ...credentials, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await authService.login(credentials);
            localStorage.setItem('token', res.access_token);
            const payload = JSON.parse(atob(res.access_token.split('.')[1]));
            const user = res.user || { email: payload.sub, role: payload.role };
            localStorage.setItem('user', JSON.stringify(user));

            if (user.role === 'admin') navigate('/admin-dashboard');
            else if (user.role === 'faculty') navigate('/faculty-dashboard');
            else navigate('/student-dashboard');
        } catch (err) {
            setError(getErrorMessage(err, 'Invalid email or password'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
                <div className="mx-auto h-12 w-12 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-sm mb-4">
                    <LogIn size={24} />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Welcome to CourseInsight Analytics</h2>
                <p className="mt-2 text-sm text-gray-500">Analyze course demand and manage enrollments intelligently.</p>
            </div>

            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-8 shadow-sm border border-gray-200 rounded-2xl relative overflow-hidden">
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm font-medium text-center">
                                {error}
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    name="username"
                                    type="email"
                                    required
                                    className="block w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-colors placeholder:text-gray-400 shadow-sm"
                                    placeholder="name@university.edu"
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-1.5">
                                <label className="block text-sm font-medium text-gray-700">Password</label>
                                <Link to="/forgot-password" className="text-sm font-medium text-blue-600 hover:text-blue-500 transition-colors">Forgot password?</Link>
                            </div>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                <input
                                    name="password"
                                    type="password"
                                    required
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
                            {loading ? 'Signing in...' : 'Sign in'}
                        </button>
                    </form>

                    <div className="mt-8 text-center text-sm">
                        <span className="text-gray-500">Don't have an account?</span>{' '}
                        <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium transition-colors">Sign up</Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
