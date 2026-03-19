import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
                    <div className="max-w-md w-full bg-white border border-slate-200 rounded-2xl shadow-xl p-8 text-center animate-in zoom-in-95 duration-300">
                        <div className="w-16 h-16 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertTriangle size={32} />
                        </div>
                        <h2 className="text-2xl font-black text-slate-900 mb-2">Something went wrong</h2>
                        <p className="text-slate-500 mb-8 leading-relaxed">
                            The application encountered an unexpected error. Don't worry, your data is safe.
                            Please try refreshing the page or returning home.
                        </p>

                        {import.meta.env.DEV && (
                            <div className="mb-8 p-4 bg-slate-50 rounded-xl border border-slate-100 text-left overflow-auto max-h-40">
                                <code className="text-xs text-rose-600 font-mono italic">
                                    {this.state.error?.toString()}
                                </code>
                            </div>
                        )}

                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={() => window.location.reload()}
                                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all shadow-md active:scale-[0.98]"
                            >
                                <RefreshCw size={18} /> Refresh Page
                            </button>
                            <button
                                onClick={this.handleReset}
                                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-50 transition-all shadow-sm active:scale-[0.98]"
                            >
                                <Home size={18} /> Return Home
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
