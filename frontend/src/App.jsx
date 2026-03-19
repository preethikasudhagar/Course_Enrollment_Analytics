import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminDashboard from './dashboards/AdminDashboard';
import FacultyDashboard from './dashboards/FacultyDashboard';
import StudentDashboard from './dashboards/StudentDashboard';

import ManageUsers from './pages/ManageUsers';
import ManageCourses from './pages/ManageCourses';
import AvailableCourses from './pages/AvailableCourses';
import MyEnrollments from './pages/MyEnrollments';
import Settings from './pages/Settings';
import ForgotPassword from './pages/ForgotPassword';
import Profile from './pages/Profile';
import ErrorBoundary from './components/ErrorBoundary';

const ProtectedRoute = ({ children, allowedRoles }) => {
    const getUser = () => {
        try {
            const stored = localStorage.getItem('user');
            return stored ? JSON.parse(stored) : null;
        } catch {
            return null;
        }
    };
    const user = getUser();
    const token = localStorage.getItem('token');

    if (!token || !user) {
        return <Navigate to="/login" replace />;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
        const homeMap = {
            admin: '/admin-dashboard',
            faculty: '/faculty-dashboard',
            student: '/student-dashboard'
        };
        return <Navigate to={homeMap[user.role] || '/login'} replace />;
    }

    return children;
};

function App() {
    const withBoundary = (component) => (
        <ErrorBoundary>
            {component}
        </ErrorBoundary>
    );

    return (
        <div className="min-h-screen bg-[#F8FAFC] text-slate-900 font-sans antialiased">
            <Routes>
                <Route path="/login" element={withBoundary(<Login />)} />
                <Route path="/register" element={withBoundary(<Register />)} />
                <Route path="/forgot-password" element={withBoundary(<ForgotPassword />)} />
                <Route path="/profile" element={
                    <ProtectedRoute>
                        {withBoundary(<Profile />)}
                    </ProtectedRoute>
                } />

                {/* Secure Dashboards */}
                <Route path="/admin-dashboard" element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        {withBoundary(<AdminDashboard />)}
                    </ProtectedRoute>
                } />
                <Route path="/faculty-dashboard" element={
                    <ProtectedRoute allowedRoles={['faculty']}>
                        {withBoundary(<FacultyDashboard />)}
                    </ProtectedRoute>
                } />
                <Route path="/student-dashboard" element={
                    <ProtectedRoute allowedRoles={['student']}>
                        {withBoundary(<StudentDashboard />)}
                    </ProtectedRoute>
                } />

                {/* Identity & Asset Management */}
                <Route path="/admin/courses" element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        {withBoundary(<ManageCourses />)}
                    </ProtectedRoute>
                } />
                <Route path="/admin/users" element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        {withBoundary(<ManageUsers />)}
                    </ProtectedRoute>
                } />
                <Route path="/settings" element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        {withBoundary(<Settings />)}
                    </ProtectedRoute>
                } />

                {/* CurricularDiscovery */}
                <Route path="/student/courses" element={
                    <ProtectedRoute allowedRoles={['student']}>
                        {withBoundary(<AvailableCourses />)}
                    </ProtectedRoute>
                } />
                <Route path="/student/my-enrollments" element={
                    <ProtectedRoute allowedRoles={['student']}>
                        {withBoundary(<MyEnrollments />)}
                    </ProtectedRoute>
                } />

                <Route path="/" element={<Navigate to="/login" replace />} />
                <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
        </div>
    );
}

export default App;
