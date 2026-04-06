import axios from 'axios';

let API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
if (API_URL && !API_URL.startsWith('http')) {
    API_URL = `https://${API_URL}`;
}
// Strip trailing slashes to prevent //auth/login redirects
if (API_URL) {
    API_URL = API_URL.replace(/\/+$/, "");
}

const api = axios.create({
    baseURL: API_URL,
});

// Add auth header if token exists
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Robust response interceptor for standard API pattern
api.interceptors.response.use(
    (response) => {
        // If it's a blob, Return the whole response object so components can handle it
        if (response.config.responseType === 'blob') {
            return response;
        }

        // Unwrap standard status/data envelope if it exists
        if (response.data && response.data.status === 'success' && response.data.data !== undefined) {
            return response.data.data;
        }

        // Return raw data as fallback
        return response.data;
    },
    (error) => {
        return Promise.reject(error);
    }
);

const safeRequest = async (requestFn, fallback = null) => {
    try {
        const data = await requestFn();
        return data ?? fallback;
    } catch (error) {
        console.error('API request failed:', error);
        return fallback;
    }
};

export const getErrorMessage = (error, fallback = 'Request failed') => {
    const detail = error?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        const first = detail[0];
        if (typeof first === 'string') return first;
        if (first?.msg) return first.msg;
    }
    if (detail?.msg) return detail.msg;
    if (typeof error?.message === 'string') return error.message;
    return fallback;
};

export const userService = {
    login: async (credentials) => {
        const form = new URLSearchParams();
        form.append('username', credentials?.username || '');
        form.append('password', credentials?.password || '');
        return await api.post('/auth/login', form, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    },
    register: async (userData) => await api.post('/auth/register', userData),
    getProfile: async () => await api.get('/users/profile'),
    updateProfile: async (formData) => await api.put('/users/profile', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    }),
    getAll: async () => await api.get('/users/'),
    updateRole: async (userId, role) => await api.put(`/users/${userId}/role`, null, { params: { role } }),
    delete: async (userId) => await api.delete(`/users/${userId}`),
    safeGetProfile: async () => await safeRequest(() => userService.getProfile(), null)
};

export const authService = {
    ...userService,
    changePassword: async (payload) => await api.post('/change-password', payload),
    forgotPassword: async (payload) => await api.post('/forgot-password', payload),
    verifyOtp: async (payload) => await api.post('/verify-otp', payload),
    resetPassword: async (payload) => await api.post('/reset-password', payload),
    logout: () => {
        localStorage.clear();
        window.location.href = '/login';
    }
};

export const courseService = {
    getAll: async (department = null) => await api.get('/courses/', { params: { department } }),
    create: async (courseData) => await api.post('/courses/create-course', courseData),
    add: async (courseData) => await api.post('/courses/create-course', courseData),
    update: async (id, courseData) => await api.put(`/courses/update/${id}`, courseData),
    delete: async (id) => await api.delete(`/courses/delete/${id}`),
    safeGetAll: async (department = null) => await safeRequest(() => courseService.getAll(department), []),
    getStudents: async (id) => await api.get(`/courses/${id}/students`)
};

export const analyticsService = {
    getDashboardStats: async () => await api.get('/analytics/dashboard-stats'),
    getEnrollmentTrends: async () => await api.get('/analytics/enrollment-trends'),
    getPopularity: async () => await api.get('/analytics/course-popularity'),
    getDemandPrediction: async () => await api.get('/analytics/demand-prediction'),
    getFacultyStats: async () => await api.get('/analytics/faculty-stats'),
    getDeptUtilization: async () => await api.get('/analytics/department-utilization'),
    getDeptStats: async () => await api.get('/analytics/department-stats'),
    getHeatmap: async () => await api.get('/analytics/enrollment-heatmap'),
    getInsights: async () => await api.get('/analytics/smart-insights'),
    getSummary: async () => await api.get('/analytics/dashboard-summary'),
    getEnrollmentsChart: async () => {
        try {
            return await api.get('/analytics/course-enrollments-chart');
        } catch {
            return await api.get('/analytics/course_enrollments');
        }
    },
    getMonthlyTrends: async () => {
        try {
            return await api.get('/analytics/monthly-trends');
        } catch {
            return await api.get('/analytics/monthly_trends');
        }
    },
    getRecommendations: async () => await api.get('/analytics/recommendations'),
    exportData: async (format, reportType = 'general') => await api.get('/analytics/export', {
        params: { format, report_type: reportType },
        responseType: 'blob'
    }),
    getSeatExpansionLogs: async () => await api.get('/seat-expansion-logs'),
    getAdminVitals: async () => await api.get('/analytics/admin-vitals'),
    getFacultyVitals: async () => await api.get('/analytics/faculty-vitals'),
    getStudentVitals: async () => await api.get('/analytics/student-vitals')
};

export const enrollmentService = {
    enroll: async (courseId, studentId = null) => await api.post('/enroll', { course_id: courseId, student_id: studentId }),
    getMyEnc: async () => await api.get('/enrollments/my'),
    safeGetMyEnc: async () => await safeRequest(() => enrollmentService.getMyEnc(), [])
};

export const suggestionService = {
    getAll: async () => await api.get('/suggestions/'),
    approveAction: async (id, action) => await api.post(`/suggestions/${id}/${action}`)
};

export const systemService = {
    getActivity: async () => await api.get('/activity/'),
    getSettings: async () => await api.get('/settings/'),
    updateSettings: async (payload) => await api.put('/settings/', payload)
};

export const notificationService = {
    getAll: async () => await api.get('/notifications/'),
    getUnreadCount: async () => await api.get('/notifications/unread-count'),
    markRead: async (id) => await api.post(`/notifications/${id}/read`),
    markAllRead: async () => await api.post('/notifications/mark-all-read')
};

export const settingsService = {
    get: async () => await api.get('/settings/'),
    update: async (payload) => await api.put('/settings/', payload)
};

export default api;
