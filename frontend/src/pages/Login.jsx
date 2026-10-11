import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, AlertCircle, Users, Briefcase, TrendingUp, Check } from 'lucide-react';

export default function Login() {
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

  const { login } = useAuth();
  const navigate = useNavigate();

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
  const handleKeyDown = (e) => {
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
        navigate('/');
      }, 400);
    } catch (err) {
      setAuthError(err.response?.data?.detail || 'Incorrect email or password. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex w-full font-sans bg-white selection:bg-blue-100 selection:text-blue-900">
      
      {/* ======================================================== */}
      {/* 1. LEFT BRAND PANEL (Desktop >=1024px, 45% width)        */}
      {/* ======================================================== */}
      <div className="hidden lg:flex lg:w-[45%] min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 animate-gradient-slow relative overflow-hidden flex-col justify-between p-10 lg:p-14 xl:p-16 text-white border-r border-slate-800/40">
        
        {/* Soft Radial Glows */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/15 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        
        {/* Faint Dot / Grid Pattern */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.06] pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="dot-grid" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="#ffffff" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#dot-grid)" />
        </svg>

        {/* Top spacer for balanced vertical alignment */}
        <div className="hidden xl:block"></div>

        {/* Centered Brand Content Block (Max-width ~480px) */}
        <div className="relative z-10 my-auto w-full max-w-[480px] mx-auto animate-fade-up">
          
          {/* Logo & Wordmark Header (Compact Badge & Centered Alignment) */}
          <div className="flex items-center gap-3.5 mb-8">
            <div className="w-12 h-12 bg-white rounded-xl p-1.5 flex items-center justify-center border border-white/20 shadow-sm shadow-navy-950/20 flex-shrink-0">
              <img 
                src="/crm360-mark.png" 
                alt="CRM360" 
                className="w-full h-full object-contain"
              />
            </div>
            <div className="flex flex-col justify-center">
              <span className="text-2xl font-bold tracking-tight text-white leading-none">
                CRM<span className="text-cyan-400">360</span>
              </span>
              <span className="text-[10px] tracking-wider uppercase font-semibold text-slate-300/80 mt-1.5 leading-none">
                Connect &bull; Manage &bull; Grow
              </span>
            </div>
          </div>

          {/* Refined 3-Line Headline */}
          <h1 className="text-4xl lg:text-[2.75rem] font-bold tracking-tight leading-[1.1] text-white mb-4">
            Connect.<br />
            Manage.<br />
            <span className="bg-gradient-to-r from-blue-300 via-cyan-200 to-sky-100 bg-clip-text text-transparent">
              Grow.
            </span>
          </h1>

          {/* Softer White Description (Max 2 lines, ~18px) */}
          <p className="text-lg text-slate-200/80 leading-relaxed max-w-md mb-8 font-normal">
            Bring your customers, teams, and opportunities together in one powerful CRM platform.
          </p>

          {/* Feature List (3 items with 40px icon chips, 24px vertical gap, verified features) */}
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 text-cyan-300 flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
                <Users size={20} />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white tracking-wide">Unified Customer View</h2>
                <p className="text-xs text-slate-300/75 leading-normal mt-0.5">Accounts, contacts, and interaction history in one place.</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 text-cyan-300 flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
                <Briefcase size={20} />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white tracking-wide">Team Collaboration</h2>
                <p className="text-xs text-slate-300/75 leading-normal mt-0.5">Shared records, tasks, and notes to keep your team aligned.</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 text-cyan-300 flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
                <TrendingUp size={20} />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white tracking-wide">Pipeline &amp; Revenue Insights</h2>
                <p className="text-xs text-slate-300/75 leading-normal mt-0.5">Track your deals through every stage of the pipeline.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Pinned Copyright Footer */}
        <div className="relative z-10 w-full max-w-[480px] mx-auto pt-8 text-xs text-slate-400/80 font-normal">
          &copy; 2026 CRM360. All rights reserved.
        </div>
      </div>

      {/* ======================================================== */}
      {/* 2. RIGHT FORM PANEL (55% width, clean white, NO CARD)   */}
      {/* ======================================================== */}
      <div className="w-full lg:w-[55%] min-h-screen bg-white flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16 xl:p-20 overflow-y-auto">
        
        {/* Form Container (Constrained to Max-width ~420px, NO Card wrapper) */}
        <div className="w-full max-w-[420px] mx-auto animate-fade-up">
          
          {/* Mobile-Only Header (<1024px) */}
          <div className="lg:hidden flex flex-col items-center justify-center mb-8">
            <div className="w-12 h-12 bg-white border border-slate-200/90 rounded-xl p-1.5 flex items-center justify-center shadow-sm mb-3 flex-shrink-0">
              <img 
                src="/crm360-mark.png" 
                alt="CRM360" 
                className="w-full h-full object-contain"
              />
            </div>
            <span className="text-2xl font-bold tracking-tight text-slate-900 leading-none">
              CRM<span className="text-blue-600">360</span>
            </span>
            <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mt-1.5 leading-none">
              Connect &bull; Manage &bull; Grow
            </p>
          </div>

          {/* Form Header */}
          <div className="mb-7 text-left">
            <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">
              Welcome back
            </h1>
            <p className="text-slate-600 text-sm mt-1.5 font-normal">
              Sign in to your account to continue
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

          {/* Main Login Form */}
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <input 
                  id="email"
                  name="email"
                  type="email" 
                  autoComplete="email"
                  value={username} 
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (emailError) validateEmail(e.target.value);
                  }}
                  onBlur={() => validateEmail(username)}
                  className={`w-full h-12 pl-11 pr-4 bg-white border ${
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
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              
              <div className="relative">
                <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <input 
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"} 
                  autoComplete="current-password"
                  value={password} 
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (passwordError) validatePassword(e.target.value);
                  }}
                  onBlur={() => validatePassword(password)}
                  onKeyDown={handleKeyDown}
                  onKeyUp={handleKeyDown}
                  className={`w-full h-12 pl-11 pr-11 bg-white border ${
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

            {/* Full-Width Sign In Button (48px, with spinner & success state) */}
            <button 
              type="submit" 
              disabled={loading || isSuccess}
              className={`w-full h-12 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium rounded-xl shadow-sm transition-all duration-150 flex items-center justify-center text-sm focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/25 ${
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
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  <span>Signing In...</span>
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

        </div>
      </div>

    </div>
  );
}
