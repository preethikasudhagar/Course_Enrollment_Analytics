import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { authService, getErrorMessage } from '../services/api';
import { Mail, Lock, LogIn, Activity, CheckCircle, AlertTriangle } from 'lucide-react';

const Login = () => {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [apiStatus, setApiStatus] = useState({ state: 'checking', url: '' });
    const navigate = useNavigate();

    const [diagnosticResult, setDiagnosticResult] = useState(null);
    const [isDiagnosing, setIsDiagnosing] = useState(false);

    const runDiagnostic = async () => {
        setIsDiagnosing(true);
        setDiagnosticResult(null);
        try {
            const postRes = await axios.post(`${apiStatus.url}/test-post`, {}, { timeout: 10000 });
            const dbRes = await axios.get(`${apiStatus.url}/test-db`, { timeout: 15000 });
            
            setDiagnosticResult({ 
                success: postRes.data.status === 'ok' && dbRes.data.status === 'ok', 
                message: `Connection: ${postRes.data.message} | Database: ${dbRes.data.message} ${dbRes.data.hint || ''}` 
            });
        } catch (err) {
            setDiagnosticResult({ 
                success: false, 
                message: `Diagnostic Failed: ${err.message}. Status: ${err.response?.status || 'N/A'}` 
            });
        } finally {
            setIsDiagnosing(false);
        }
    };

    useEffect(() => {
        const checkApi = async (retries = 3) => {
            console.log("--- FRONTEND VERSION 5.2 ---");
            // Hardcoded production URL for reliability
            let apiBase = import.meta.env.VITE_API_URL || 'https://course-analytics-backend-production.up.railway.app';
            
            setApiStatus(prev => ({ ...prev, url: apiBase }));
            
            for (let i = 0; i < retries; i++) {
                try {
                    // Test basic connectivity to root with 8s timeout
                    await axios.get(`${apiBase}/`, { timeout: 8000 });
                    setApiStatus({ state: 'connected', url: apiBase });
                    return; // Success
                } catch (err) {
                    console.warn(`API connection attempt ${i + 1} failed for ${apiBase}:`, err.message);
                    if (i === retries - 1) {
                        setApiStatus({ state: 'error', url: apiBase });
                        setError(`CRITICAL: Backend unreachable at ${apiBase}. If this is production, please check if the backend service is running.`);
                    } else {
                        // Wait 2 seconds before retry
                        await new Promise(r => setTimeout(r, 2000));
                    }
                }
            }
        };
        checkApi();
    }, []);

    const handleChange = (e) => {
        setCredentials({ ...credentials, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (apiStatus.state === 'error') {
            setError(`Cannot sign in. Backend is unreachable at ${apiStatus.url}. Check deployment logs.`);
            return;
        }
        setLoading(true);
        setError('');
        try {
            const res = await authService.login(credentials);
            if (res.access_token) {
                localStorage.setItem('token', res.access_token);
                const payload = JSON.parse(atob(res.access_token.split('.')[1]));
                const user = res.user || { email: payload.sub, role: payload.role };
                localStorage.setItem('user', JSON.stringify(user));

                if (user.role === 'admin') navigate('/admin-dashboard');
                else if (user.role === 'faculty') navigate('/faculty-dashboard');
                else navigate('/student-dashboard');
            }
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
                        {/* API Connection Indicator */}
                        <div className={`mb-4 flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium border ${
                            apiStatus.state === 'connected' ? 'bg-green-50 text-green-700 border-green-100' :
                            apiStatus.state === 'error' ? 'bg-red-50 text-red-700 border-red-100' :
                            'bg-blue-50 text-blue-700 border-blue-100'
                        }`}>
                            <div className="flex flex-col items-start gap-1">
                                <div className="flex items-center gap-2">
                                    {apiStatus.state === 'connected' ? <CheckCircle size={14} /> : 
                                     apiStatus.state === 'error' ? <AlertTriangle size={14} /> : 
                                     <Activity className="animate-spin" size={14} />}
                                    <span>API: {apiStatus.state === 'connected' ? 'Online' : apiStatus.state === 'error' ? 'Offline' : 'Checking connection...'}</span>
                                </div>
                                <span className="text-[10px] opacity-60 font-mono break-all">{apiStatus.url}</span>
                            </div>
                        </div>

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

                        {diagnosticResult && (
                            <div className={`mb-4 p-3 rounded-lg text-xs font-mono border ${
                                diagnosticResult.success ? 'bg-green-50 text-green-700 border-green-100' : 'bg-red-50 text-red-700 border-red-100'
                            }`}>
                                <div className="font-bold mb-1">Diagnostic Report:</div>
                                {diagnosticResult.message}
                            </div>
                        )}

                        <div className="flex flex-col gap-3">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-all shadow-md"
                            >
                                {loading ? 'Signing in...' : 'Sign in'}
                            </button>

                            <button
                                type="button"
                                onClick={runDiagnostic}
                                disabled={isDiagnosing}
                                className="w-full py-2 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-200 transition-all"
                            >
                                {isDiagnosing ? 'Running Diagnostic...' : 'Run Connection Diagnostic'}
                            </button>
                        </div>
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
