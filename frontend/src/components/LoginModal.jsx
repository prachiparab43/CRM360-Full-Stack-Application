import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, AlertCircle, X, Check, ShieldCheck, UserPlus, LogIn, ArrowRight } from 'lucide-react';

export default function LoginModal({ isOpen, onClose, initialMode = 'signin' }) {
  const [mode, setMode] = useState(initialMode); // 'signin' or 'getstarted'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [capsLockOn, setCapsLockOn] = useState(false);

  // Validation & status states
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [authError, setAuthError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const { login, googleAuth } = useAuth();
  const navigate = useNavigate();
  const emailInputRef = useRef(null);
  const modalRef = useRef(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  // Sync mode with prop
  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  // Reset form state when modal opens
  useEffect(() => {
    if (isOpen) {
      setUsername('');
      setPassword('');
      setEmailError('');
      setPasswordError('');
      setAuthError('');
      setLoading(false);
      setIsSuccess(false);
      setShowPassword(false);
      setCapsLockOn(false);

      // Focus email input after opening
      const timer = setTimeout(() => {
        emailInputRef.current?.focus();
      }, 100);

      // Prevent background scrolling while modal is open
      document.body.style.overflow = 'hidden';

      return () => {
        clearTimeout(timer);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  // Handle Escape key to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !loading) {
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, loading, onClose]);

  if (!isOpen) return null;

  // Validate email format
  const validateEmail = (val) => {
    if (!val.trim()) {
      setEmailError('Email address is required.');
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(val.trim())) {
      setEmailError('Please enter a valid email address.');
      return false;
    }
    setEmailError('');
    return true;
  };

  // Validate password
  const validatePassword = (val) => {
    if (!val) {
      setPasswordError('Password is required.');
      return false;
    }
    setPasswordError('');
    return true;
  };

  // Caps lock detection
  const handleKeyModifier = (e) => {
    if (e.getModifierState) {
      setCapsLockOn(e.getModifierState('CapsLock'));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');

    const isEmailValid = validateEmail(username);
    const isPasswordValid = validatePassword(password);

    if (!isEmailValid || !isPasswordValid) {
      return;
    }

    setLoading(true);
    try {
      await login(username, password);
      setIsSuccess(true);
      setTimeout(() => {
        onClose();
        navigate('/dashboard');
      }, 400);
    } catch (err) {
      setAuthError(err.response?.data?.detail || 'Incorrect email or password. Please try again.');
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    setAuthError('');
    if (!googleClientId) {
      setAuthError('Google Client ID is not configured in frontend/.env (VITE_GOOGLE_CLIENT_ID).');
      return;
    }

    if (!window.google?.accounts?.id) {
      setAuthError('Google Identity Services SDK is not loaded. Check your internet connection.');
      return;
    }

    try {
      setGoogleLoading(true);
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          if (!response?.credential) {
            setGoogleLoading(false);
            return;
          }
          try {
            const res = await googleAuth(response.credential);
            setGoogleLoading(false);
            if (res.status === 'Active') {
              setIsSuccess(true);
              setTimeout(() => {
                onClose();
                navigate('/dashboard');
              }, 400);
            } else if (res.status === 'Pending_Approval') {
              onClose();
              navigate('/pending-approval');
            }
          } catch (err) {
            setGoogleLoading(false);
            setAuthError(err.response?.data?.detail || 'Google authentication failed. Please try again.');
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true
      });

      // Prompt the user to select their account
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          setGoogleLoading(false);
        }
      });
    } catch (err) {
      setGoogleLoading(false);
      setAuthError('Failed to initialize Google authentication prompt.');
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/65 backdrop-blur-xs transition-opacity duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-modal-title"
    >
      {/* Modal Dialog Card */}
      <div 
        ref={modalRef}
        className="w-full max-w-[440px] bg-white rounded-2xl shadow-2xl border border-slate-200/90 overflow-hidden relative animate-fade-up max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Gradient Accent Bar */}
        <div className="h-1.5 w-full bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-400" />

        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={loading}
          aria-label="Close modal"
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
        >
          <X size={20} />
        </button>

        <div className="p-6 sm:p-8 overflow-y-auto">
          
          {/* Header Branding */}
          <div className="flex items-center gap-3 mb-5">
            <div className="w-11 h-11 bg-white border border-slate-200/90 rounded-xl p-1.5 flex items-center justify-center shadow-xs flex-shrink-0">
              <img 
                src="/crm360-mark.png" 
                alt="CRM360" 
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900 leading-none block">
                CRM<span className="text-blue-600">360</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mt-1 block">
                Connect &bull; Manage &bull; Grow
              </span>
            </div>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex rounded-xl bg-slate-100 p-1 mb-6 border border-slate-200/80">
            <button
              type="button"
              onClick={() => {
                setMode('signin');
                setAuthError('');
              }}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                mode === 'signin'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LogIn size={14} />
              <span>Sign In</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('getstarted');
                setAuthError('');
              }}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                mode === 'getstarted'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserPlus size={14} />
              <span>Get Started</span>
            </button>
          </div>

          {/* Title & Prompt */}
          <div className="mb-5">
            <h2 id="login-modal-title" className="text-2xl font-bold text-slate-900 tracking-tight">
              {mode === 'signin' ? 'Welcome back' : 'Get Started with CRM360'}
            </h2>
            <p className="text-slate-500 text-xs sm:text-sm mt-1">
              {mode === 'signin' 
                ? 'Sign in to access your enterprise dashboard'
                : 'Join your organization or start new enterprise onboarding'}
            </p>
          </div>

          {/* Error Banner with Alert Role & Shake Animation */}
          {authError && (
            <div 
              role="alert" 
              className="bg-red-50 text-red-700 p-3.5 rounded-xl mb-5 text-sm border border-red-200 flex items-start gap-2.5 font-medium animate-shake"
            >
              <AlertCircle size={18} className="text-red-500 flex-shrink-0 mt-0.5" />
              <span>{authError}</span>
            </div>
          )}

          {/* Google Button */}
          <div className="mb-5">
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={loading || googleLoading}
              title={googleClientId ? (mode === 'signin' ? 'Sign in with Google' : 'Sign up with Google') : 'Set VITE_GOOGLE_CLIENT_ID in frontend/.env to activate'}
              className="w-full h-11 sm:h-12 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-xl font-medium text-sm flex items-center justify-center gap-3 shadow-2xs transition-colors hover:border-slate-400 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed relative"
            >
              {/* Official Google SVG emblem */}
              <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>
                {googleLoading 
                  ? 'Connecting to Google...' 
                  : (mode === 'signin' ? 'Sign in with Google' : 'Sign up with Google')}
              </span>
              {!googleClientId && (
                <span className="text-[10px] bg-amber-50 text-amber-700 font-semibold px-2 py-0.5 rounded border border-amber-200">
                  Missing Client ID
                </span>
              )}
            </button>
            {!googleClientId && (
              <p className="text-[11px] text-amber-600/90 text-center mt-1.5 font-medium">
                Set VITE_GOOGLE_CLIENT_ID in frontend/.env to activate Google OAuth.
              </p>
            )}
          </div>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-3 text-slate-400 font-medium tracking-wider">
                or continue with credentials
              </span>
            </div>
          </div>

          {/* Mode Guidance for Get Started */}
          {mode === 'getstarted' && (
            <div className="mb-4 p-3.5 rounded-xl bg-blue-50/80 border border-blue-200/70 text-xs text-blue-900 space-y-1.5">
              <div className="font-semibold flex items-center gap-1.5 text-blue-800">
                <ShieldCheck size={16} />
                <span>Enterprise Access Policy</span>
              </div>
              <p className="leading-relaxed text-blue-800/90">
                CRM360 is an enterprise platform. Existing members can sign in with their assigned company credentials. New Google users will enter pending review until assigned to an authorized company workspace.
              </p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            
            {/* Email Field */}
            <div>
              <label htmlFor="modal-email" className="block text-xs sm:text-sm font-medium text-slate-700 mb-1.5">
                Work Email Address
              </label>
              <div className="relative">
                <Mail size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <input 
                  ref={emailInputRef}
                  id="modal-email"
                  name="email"
                  type="email" 
                  autoComplete="email"
                  value={username} 
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (emailError) validateEmail(e.target.value);
                  }}
                  onBlur={() => validateEmail(username)}
                  className={`w-full h-11 sm:h-12 pl-11 pr-4 bg-white border ${
                    emailError ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'border-slate-300 hover:border-slate-400 focus:border-blue-600 focus:ring-blue-600/15'
                  } rounded-xl text-slate-900 placeholder-slate-400 focus:ring-[3px] focus:outline-none transition-all duration-150 text-sm`}
                  placeholder="name@company.com"
                  required 
                />
              </div>
              {emailError && (
                <p className="mt-1 text-xs text-red-600 font-medium flex items-center gap-1">
                  <span>{emailError}</span>
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="modal-password" className="block text-xs sm:text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              
              <div className="relative">
                <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <input 
                  id="modal-password"
                  name="password"
                  type={showPassword ? "text" : "password"} 
                  autoComplete="current-password"
                  value={password} 
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (passwordError) validatePassword(e.target.value);
                  }}
                  onBlur={() => validatePassword(password)}
                  onKeyDown={handleKeyModifier}
                  onKeyUp={handleKeyModifier}
                  className={`w-full h-11 sm:h-12 pl-11 pr-11 bg-white border ${
                    passwordError ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'border-slate-300 hover:border-slate-400 focus:border-blue-600 focus:ring-blue-600/15'
                  } rounded-xl text-slate-900 placeholder-slate-400 focus:ring-[3px] focus:outline-none transition-all duration-150 text-sm`}
                  placeholder="••••••••"
                  required 
                />
                <button 
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              {capsLockOn && (
                <p className="mt-1 text-xs text-amber-600 font-medium flex items-center gap-1">
                  <span>Caps Lock is ON</span>
                </p>
              )}

              {passwordError && (
                <p className="mt-1 text-xs text-red-600 font-medium">
                  <span>{passwordError}</span>
                </p>
              )}
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button 
                type="submit" 
                disabled={loading || isSuccess}
                className={`w-full h-11 sm:h-12 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium rounded-xl shadow-sm transition-all duration-150 flex items-center justify-center text-sm focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/25 cursor-pointer ${
                  loading ? 'opacity-80 cursor-wait' : ''
                } ${isSuccess ? 'bg-emerald-600 hover:bg-emerald-600' : ''}`}
              >
                {isSuccess ? (
                  <span className="flex items-center gap-2">
                    <Check size={18} />
                    <span>Authenticated! Redirecting...</span>
                  </span>
                ) : loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <span>{mode === 'signin' ? 'Sign In to Workspace' : 'Sign In with Existing Account'}</span>
                    <ArrowRight size={16} />
                  </span>
                )}
              </button>
            </div>

            {/* Security note */}
            <p className="text-center text-[11px] text-slate-400 pt-1">
              Secured with JWT authentication and Role-Based Access Control (RBAC).
            </p>
          </form>

        </div>
      </div>
    </div>
  );
}
