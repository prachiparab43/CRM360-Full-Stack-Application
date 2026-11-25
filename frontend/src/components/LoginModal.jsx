import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  AlertCircle, 
  X, 
  Check, 
  ShieldCheck, 
  UserPlus, 
  LogIn, 
  ArrowRight,
  User,
  Phone,
  Clock
} from 'lucide-react';

export default function LoginModal({ isOpen, onClose, initialMode = 'signin' }) {
  // 'signin' or 'getstarted'
  const [mode, setMode] = useState(initialMode === 'getstarted' ? 'register' : 'signin');

  // Sign In state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Register state
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [showRegConfirmPassword, setShowRegConfirmPassword] = useState(false);

  // Validation & status states
  const [capsLockOn, setCapsLockOn] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [regErrors, setRegErrors] = useState({});
  const [authError, setAuthError] = useState('');
  const [isPendingError, setIsPendingError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const { login, register, setPending } = useAuth();
  const navigate = useNavigate();
  const emailInputRef = useRef(null);
  const modalRef = useRef(null);

  // Sync mode with prop
  useEffect(() => {
    setMode(initialMode === 'getstarted' ? 'register' : 'signin');
  }, [initialMode]);

  // Reset form state when modal opens
  useEffect(() => {
    if (isOpen) {
      setUsername('');
      setPassword('');
      setRegName('');
      setRegEmail('');
      setRegPhone('');
      setRegPassword('');
      setRegConfirmPassword('');
      setEmailError('');
      setPasswordError('');
      setRegErrors({});
      setAuthError('');
      setIsPendingError(false);
      setLoading(false);
      setIsSuccess(false);
      setShowPassword(false);
      setShowRegPassword(false);
      setShowRegConfirmPassword(false);
      setCapsLockOn(false);

      const timer = setTimeout(() => {
        emailInputRef.current?.focus();
      }, 100);

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
    if (!val || !val.trim()) {
      return 'Email address is required.';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(val.trim())) {
      return 'Please enter a valid work email address.';
    }
    return '';
  };

  // Caps lock detection
  const handleKeyModifier = (e) => {
    if (e.getModifierState) {
      setCapsLockOn(e.getModifierState('CapsLock'));
    }
  };

  // Switch tab
  const switchTab = (newMode) => {
    setMode(newMode);
    setAuthError('');
    setIsPendingError(false);
    setEmailError('');
    setPasswordError('');
    setRegErrors({});
  };

  // Sign In handler
  const handleSignIn = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsPendingError(false);

    const emailErr = validateEmail(username);
    const passErr = !password ? 'Password is required.' : '';

    setEmailError(emailErr);
    setPasswordError(passErr);

    if (emailErr || passErr) return;

    setLoading(true);
    try {
      const loggedUser = await login(username, password);
      setIsSuccess(true);
      setTimeout(() => {
        onClose();
        if (loggedUser && (loggedUser.status === 'Pending_Approval' || loggedUser.status === 'Pending')) {
          navigate('/pending-approval');
        } else {
          navigate('/dashboard');
        }
      }, 300);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Incorrect email or password. Please try again.';
      setAuthError(detail);
      if (err.response?.status === 403 && (detail.toLowerCase().includes('pending') || detail.toLowerCase().includes('approval'))) {
        setIsPendingError(true);
        setPending({ email: username.trim(), name: 'Member' });
      }
      setLoading(false);
    }
  };

  // Register handler
  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsPendingError(false);
    const errors = {};

    if (!regName.trim()) {
      errors.name = 'Full name is required.';
    }

    const emailErr = validateEmail(regEmail);
    if (emailErr) {
      errors.email = emailErr;
    }

    if (!regPassword) {
      errors.password = 'Password is required.';
    } else if (regPassword.length < 8) {
      errors.password = 'Password must be at least 8 characters long.';
    } else if (!/[a-zA-Z]/.test(regPassword) || !/[0-9]/.test(regPassword)) {
      errors.password = 'Password must contain both letters and numbers.';
    }

    if (!regConfirmPassword) {
      errors.confirmPassword = 'Please confirm your password.';
    } else if (regPassword !== regConfirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    setRegErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setLoading(true);
    try {
      await register({
        name: regName,
        email: regEmail,
        password: regPassword,
        confirm_password: regConfirmPassword,
        phone: regPhone
      });
      setIsSuccess(true);
      setTimeout(() => {
        onClose();
        navigate('/pending-approval');
      }, 400);
    } catch (err) {
      setAuthError(err.response?.data?.detail || 'Registration failed. Please try again.');
      setLoading(false);
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
        className="w-full max-w-[460px] bg-white rounded-2xl shadow-2xl border border-slate-200/90 overflow-hidden relative animate-fade-up max-h-[92vh] flex flex-col"
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
          <div className="flex rounded-xl bg-slate-100 p-1 mb-5 border border-slate-200/80">
            <button
              type="button"
              onClick={() => switchTab('signin')}
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
              onClick={() => switchTab('register')}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                mode === 'register'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserPlus size={14} />
              <span>Get Started</span>
            </button>
          </div>

          {/* Title & Prompt */}
          <div className="mb-4">
            <h2 id="login-modal-title" className="text-2xl font-bold text-slate-900 tracking-tight">
              {mode === 'signin' ? 'Welcome back' : 'Create an Account'}
            </h2>
            <p className="text-slate-500 text-xs sm:text-sm mt-0.5">
              {mode === 'signin' 
                ? 'Sign in to access your enterprise dashboard'
                : 'Register for company workspace onboarding'}
            </p>
          </div>

          {/* Error Banner with Alert Role & Shake Animation */}
          {authError && (
            <div 
              role="alert" 
              className="bg-red-50 text-red-700 p-3.5 rounded-xl mb-4 text-sm border border-red-200 flex flex-col gap-1.5 font-medium animate-shake"
            >
              <div className="flex items-start gap-2.5">
                <AlertCircle size={18} className="text-red-500 flex-shrink-0 mt-0.5" />
                <span>{authError}</span>
              </div>
              {isPendingError && (
                <div className="mt-1 pl-7">
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      navigate('/pending-approval');
                    }}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900 underline cursor-pointer"
                  >
                    <Clock size={13} />
                    <span>View Pending Status Details</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 1: SIGN IN FORM                                      */}
          {/* ======================================================== */}
          {mode === 'signin' ? (
            <form onSubmit={handleSignIn} noValidate className="space-y-4">
              
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
                      if (emailError) setEmailError(validateEmail(e.target.value));
                    }}
                    onBlur={() => setEmailError(validateEmail(username))}
                    className={`w-full h-11 sm:h-12 pl-11 pr-4 bg-white border ${
                      emailError ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'border-slate-300 hover:border-slate-400 focus:border-blue-600 focus:ring-blue-600/15'
                    } rounded-xl text-slate-900 placeholder-slate-400 focus:ring-[3px] focus:outline-none transition-all duration-150 text-sm`}
                    placeholder="name@company.com"
                    required 
                  />
                </div>
                {emailError && (
                  <p className="mt-1 text-xs text-red-600 font-medium">
                    {emailError}
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
                      if (passwordError) setPasswordError(e.target.value ? '' : 'Password is required.');
                    }}
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
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-colors cursor-pointer"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>

                {capsLockOn && (
                  <p className="mt-1 text-xs text-amber-600 font-medium">
                    Caps Lock is ON
                  </p>
                )}

                {passwordError && (
                  <p className="mt-1 text-xs text-red-600 font-medium">
                    {passwordError}
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
                      <span>Sign In to Workspace</span>
                      <ArrowRight size={16} />
                    </span>
                  )}
                </button>
              </div>

              <p className="text-center text-xs text-slate-500 pt-2">
                Need an account?{' '}
                <button
                  type="button"
                  onClick={() => switchTab('register')}
                  className="font-semibold text-blue-600 hover:text-blue-700 underline cursor-pointer"
                >
                  Create one now
                </button>
              </p>

            </form>
          ) : (
            /* ======================================================== */
            /* TAB 2: REGISTRATION FORM                                 */
            /* ======================================================== */
            <form onSubmit={handleRegister} noValidate className="space-y-3">
              
              {/* Enterprise Access Guidance */}
              <div className="p-3 rounded-xl bg-blue-50/80 border border-blue-200/70 text-xs text-blue-900 space-y-1">
                <div className="font-semibold flex items-center gap-1.5 text-blue-800">
                  <ShieldCheck size={14} />
                  <span>Enterprise Workspace Onboarding</span>
                </div>
                <p className="leading-relaxed text-blue-800/90 text-[11px]">
                  Accounts enter pending approval until an administrator assigns company and role permissions.
                </p>
              </div>

              {/* Full Name */}
              <div>
                <label htmlFor="modal-reg-name" className="block text-xs font-medium text-slate-700 mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <input
                    id="modal-reg-name"
                    type="text"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    className={`w-full h-10 pl-9 pr-3 bg-white border ${
                      regErrors.name ? 'border-red-500' : 'border-slate-300 focus:border-blue-600'
                    } rounded-xl text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-none`}
                    placeholder="Jane Doe"
                    required
                  />
                </div>
                {regErrors.name && (
                  <p className="mt-1 text-[11px] text-red-600 font-medium">{regErrors.name}</p>
                )}
              </div>

              {/* Work Email */}
              <div>
                <label htmlFor="modal-reg-email" className="block text-xs font-medium text-slate-700 mb-1">
                  Work Email Address
                </label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <input
                    id="modal-reg-email"
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className={`w-full h-10 pl-9 pr-3 bg-white border ${
                      regErrors.email ? 'border-red-500' : 'border-slate-300 focus:border-blue-600'
                    } rounded-xl text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-none`}
                    placeholder="name@company.com"
                    required
                  />
                </div>
                {regErrors.email && (
                  <p className="mt-1 text-[11px] text-red-600 font-medium">{regErrors.email}</p>
                )}
              </div>

              {/* Phone (Optional) */}
              <div>
                <label htmlFor="modal-reg-phone" className="block text-xs font-medium text-slate-700 mb-1">
                  Phone Number <span className="text-slate-400 font-normal">(optional)</span>
                </label>
                <div className="relative">
                  <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <input
                    id="modal-reg-phone"
                    type="tel"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    className="w-full h-10 pl-9 pr-3 bg-white border border-slate-300 focus:border-blue-600 rounded-xl text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-none"
                    placeholder="+1 (555) 000-0000"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="modal-reg-password" className="block text-xs font-medium text-slate-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <input
                    id="modal-reg-password"
                    type={showRegPassword ? "text" : "password"}
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    onKeyDown={handleKeyModifier}
                    onKeyUp={handleKeyModifier}
                    className={`w-full h-10 pl-9 pr-9 bg-white border ${
                      regErrors.password ? 'border-red-500' : 'border-slate-300 focus:border-blue-600'
                    } rounded-xl text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-none`}
                    placeholder="Min. 8 characters (letters & numbers)"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegPassword(!showRegPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 cursor-pointer"
                  >
                    {showRegPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                {regErrors.password && (
                  <p className="mt-1 text-[11px] text-red-600 font-medium">{regErrors.password}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="modal-reg-confirm" className="block text-xs font-medium text-slate-700 mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <input
                    id="modal-reg-confirm"
                    type={showRegConfirmPassword ? "text" : "password"}
                    value={regConfirmPassword}
                    onChange={(e) => setRegConfirmPassword(e.target.value)}
                    onKeyDown={handleKeyModifier}
                    onKeyUp={handleKeyModifier}
                    className={`w-full h-10 pl-9 pr-9 bg-white border ${
                      regErrors.confirmPassword ? 'border-red-500' : 'border-slate-300 focus:border-blue-600'
                    } rounded-xl text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-none`}
                    placeholder="Re-enter password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegConfirmPassword(!showRegConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 cursor-pointer"
                  >
                    {showRegConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                {regErrors.confirmPassword && (
                  <p className="mt-1 text-[11px] text-red-600 font-medium">{regErrors.confirmPassword}</p>
                )}
              </div>

              {capsLockOn && (
                <p className="text-[11px] text-amber-600 font-medium">Caps Lock is ON</p>
              )}

              {/* Submit Button */}
              <div className="pt-1.5">
                <button
                  type="submit"
                  disabled={loading || isSuccess}
                  className={`w-full h-11 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium rounded-xl shadow-sm transition-all duration-150 flex items-center justify-center text-sm cursor-pointer ${
                    loading ? 'opacity-80 cursor-wait' : ''
                  } ${isSuccess ? 'bg-emerald-600 hover:bg-emerald-600' : ''}`}
                >
                  {isSuccess ? (
                    <span className="flex items-center gap-2">
                      <Check size={18} />
                      <span>Account Created! Redirecting...</span>
                    </span>
                  ) : loading ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Creating Account...</span>
                    </span>
                  ) : (
                    'Create Account'
                  )}
                </button>
              </div>

              <p className="text-center text-xs text-slate-500 pt-1">
                Already registered?{' '}
                <button
                  type="button"
                  onClick={() => switchTab('signin')}
                  className="font-semibold text-blue-600 hover:text-blue-700 underline cursor-pointer"
                >
                  Sign in
                </button>
              </p>

            </form>
          )}

        </div>
      </div>
    </div>
  );
}
