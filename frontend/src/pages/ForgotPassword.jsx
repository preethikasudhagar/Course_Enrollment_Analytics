import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService, getErrorMessage } from '../services/api';
import { BookOpen, Shield, Mail, KeyRound, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';

const ForgotPassword = () => {
    const [step, setStep] = useState(1);
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [message, setMessage] = useState({ text: '', type: '' });
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const showMessage = (text, type = 'success') => setMessage({ text, type });

    const handleSendOTP = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await authService.forgotPassword({ email });
            setStep(2);
            showMessage("If your email is registered, an OTP has been sent.");
        } catch (err) {
            showMessage("Failed to request OTP. Please try again.", "error");
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyAndReset = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await authService.resetPassword({ email, otp, new_password: newPassword });
            setStep(3);
        } catch (err) {
            showMessage(getErrorMessage(err, "Invalid OTP or failure. Please try again."), "error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center flex-col items-center">
                    <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg mb-4">
                        <BookOpen size={30} strokeWidth={2.5} />
                    </div>
                    <h2 className="text-center text-3xl font-bold tracking-tight text-gray-900">
                        {step === 1 && "Reset your password"}
                        {step === 2 && "Enter verification code"}
                        {step === 3 && "Password updated"}
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600 max-w-sm">
                        {step === 1 && "Enter your email address and we'll send you a One-Time Password to reset your account."}
                        {step === 2 && `We sent a 6-digit code to ${email}.`}
                        {step === 3 && "Your password has been successfully reset. You can now return to the login screen."}
                    </p>
                </div>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[420px]">
                <div className="bg-white py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10 border border-gray-100">

                    {message.text && step !== 3 && (
                        <div className={`mb-6 p-4 rounded-xl text-sm font-medium border ${message.type === 'error' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-green-50 text-green-700 border-green-200'}`}>
                            {message.text}
                        </div>
                    )}

                    {step === 1 && (
                        <form className="space-y-6" onSubmit={handleSendOTP}>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Email address</label>
                                <div className="mt-2 relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                        <Mail size={18} />
                                    </div>
                                    <input
                                        type="email" required
                                        className="block w-full pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-100 focus:border-blue-400 text-sm transition-all outline-none"
                                        placeholder="Enter your university email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>
                            <button
                                type="submit" disabled={loading}
                                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {loading ? "Sending..." : "Send Verification Code"}
                            </button>
                        </form>
                    )}

                    {step === 2 && (
                        <form className="space-y-6" onSubmit={handleVerifyAndReset}>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">6-Digit OTP</label>
                                <div className="mt-2 relative">
                                    <input
                                        type="text" required maxLength={6}
                                        className="block w-full px-4 py-2.5 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white tracking-[0.5em] text-center font-mono text-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all outline-none"
                                        placeholder="------"
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">New Password</label>
                                <div className="mt-2 relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                        <Shield size={18} />
                                    </div>
                                    <input
                                        type="password" required minLength={6}
                                        className="block w-full pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-100 focus:border-blue-400 text-sm transition-all outline-none"
                                        placeholder="Enter new strong password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button" onClick={() => setStep(1)}
                                    className="px-4 py-2.5 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors flex items-center justify-center gap-2 w-1/3"
                                >
                                    <ArrowLeft size={16} /> Back
                                </button>
                                <button
                                    type="submit" disabled={loading}
                                    className="flex-1 flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
                                >
                                    {loading ? "Verifying..." : "Reset Password"} <KeyRound size={16} className="ml-2" />
                                </button>
                            </div>
                        </form>
                    )}

                    {step === 3 && (
                        <div className="text-center space-y-6 py-4">
                            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex justify-center items-center text-green-500 mb-4 animate-in zoom-in">
                                <CheckCircle size={32} />
                            </div>
                            <Link to="/login" className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors">
                                Return to Login <ArrowRight size={16} className="ml-2 aspect-square" />
                            </Link>
                        </div>
                    )}
                </div>

                {step === 1 && (
                    <div className="mt-6 text-center">
                        <Link to="/login" className="text-sm font-medium text-blue-600 hover:text-blue-500 transition-colors flex items-center justify-center gap-2">
                            <ArrowLeft size={14} /> Back to Sign In
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ForgotPassword;
