/**
 * Global Error Boundary - React Error Handling
 * Catches JavaScript errors anywhere in the component tree and displays fallback UI
 * 
 * Phase 3: Architecture Updates
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

/**
 * Global Error Boundary Component
 * Wraps the entire application to catch and handle runtime errors gracefully
 */
export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    static getDerivedStateFromError(error: Error): Partial<State> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        this.setState({ errorInfo });

        // Log error for debugging
        console.error('[ErrorBoundary] Caught error:', error);
        console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack);

        // TODO: Send to error reporting service (e.g., Sentry)
    }

    handleReload = (): void => {
        window.location.reload();
    };

    handleReset = (): void => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null
        });
    };

    render(): ReactNode {
        if (this.state.hasError) {
            // Custom fallback UI
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
                    <div className="max-w-md w-full mx-4 p-8 bg-black/80 border border-red-500/30 rounded-lg backdrop-blur-md">
                        {/* Error Icon */}
                        <div className="flex justify-center mb-6">
                            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
                                <AlertTriangle className="w-8 h-8 text-red-500" />
                            </div>
                        </div>

                        {/* Error Title */}
                        <h1 className="text-2xl font-bold text-red-500 text-center mb-2">
                            System Malfunction
                        </h1>

                        <p className="text-gray-400 text-center mb-6">
                            AIZEN encountered an unexpected error. The system will attempt to recover.
                        </p>

                        {/* Error Details (Development Only) */}
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/20 rounded text-sm">
                                <p className="text-red-400 font-mono break-all">
                                    {this.state.error.message}
                                </p>
                                {this.state.errorInfo && (
                                    <pre className="mt-2 text-xs text-gray-500 overflow-auto max-h-32">
                                        {this.state.errorInfo.componentStack}
                                    </pre>
                                )}
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex gap-3">
                            <Button
                                variant="outline"
                                className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
                                onClick={this.handleReset}
                            >
                                Try Again
                            </Button>
                            <Button
                                className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white"
                                onClick={this.handleReload}
                            >
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Reload
                            </Button>
                        </div>

                        {/* Status Text */}
                        <p className="text-xs text-gray-600 text-center mt-4">
                            Error ID: {Date.now().toString(36).toUpperCase()}
                        </p>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
