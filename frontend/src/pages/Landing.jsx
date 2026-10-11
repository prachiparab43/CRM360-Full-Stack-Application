import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoginModal from '../components/LoginModal';
import { 
  Users, 
  Building2, 
  TrendingUp, 
  BarChart3, 
  MapPin, 
  ArrowRight, 
  CheckCircle2, 
  Menu, 
  X, 
  Calendar, 
  PhoneCall, 
  Mail, 
  Check 
} from 'lucide-react';

export default function Landing() {
  const { user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('signin'); // 'signin' or 'getstarted'
  const [activeTab, setActiveTab] = useState('pipeline');
  const [isScrolled, setIsScrolled] = useState(false);

  const openAuthModal = (mode = 'signin') => {
    setModalMode(mode);
    setMobileMenuOpen(false);
    setIsLoginModalOpen(true);
  };

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900 scroll-smooth">
      
      {/* ======================================================== */}
      {/* 1. STICKY NAVIGATION BAR                                 */}
      {/* ======================================================== */}
      <header 
        className={`sticky top-0 z-50 transition-all duration-300 ${
          isScrolled 
            ? 'bg-white/95 backdrop-blur-md shadow-sm border-b border-slate-200/80 py-3.5' 
            : 'bg-white/80 backdrop-blur-sm border-b border-slate-100 py-4.5'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          
          {/* Logo & Wordmark */}
          <button 
            onClick={() => scrollToSection('hero')} 
            className="flex items-center gap-3 group text-left cursor-pointer focus:outline-none"
          >
            <div className="w-10 h-10 bg-white rounded-xl p-1 flex items-center justify-center border border-slate-200 shadow-sm group-hover:border-blue-300 transition-colors">
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
              <span className="text-[9px] uppercase tracking-wider font-semibold text-slate-500 mt-0.5 block">
                Connect &bull; Manage &bull; Grow
              </span>
            </div>
          </button>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <button 
              onClick={() => scrollToSection('hero')} 
              className="hover:text-blue-600 transition-colors cursor-pointer"
            >
              Home
            </button>
            <button 
              onClick={() => scrollToSection('features')} 
              className="hover:text-blue-600 transition-colors cursor-pointer"
            >
              Features
            </button>
            <button 
              onClick={() => scrollToSection('solutions')} 
              className="hover:text-blue-600 transition-colors cursor-pointer"
            >
              Solutions
            </button>
            <button 
              onClick={() => scrollToSection('about')} 
              className="hover:text-blue-600 transition-colors cursor-pointer"
            >
              About
            </button>
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-sm hover:shadow transition-all duration-200"
              >
                Go to Dashboard
                <ArrowRight size={16} />
              </Link>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => openAuthModal('signin')}
                  className="text-slate-700 hover:text-blue-600 font-semibold text-sm px-3.5 py-2 rounded-xl transition-colors cursor-pointer"
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => openAuthModal('getstarted')}
                  className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-4.5 py-2.5 rounded-xl shadow-sm hover:shadow transition-all duration-200 cursor-pointer"
                >
                  <span>Get Started</span>
                  <ArrowRight size={15} />
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-b border-slate-200 px-4 pt-3 pb-6 space-y-3 animate-fade-up">
            <button
              onClick={() => scrollToSection('hero')}
              className="block w-full text-left py-2 text-base font-medium text-slate-700 hover:text-blue-600"
            >
              Home
            </button>
            <button
              onClick={() => scrollToSection('features')}
              className="block w-full text-left py-2 text-base font-medium text-slate-700 hover:text-blue-600"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection('solutions')}
              className="block w-full text-left py-2 text-base font-medium text-slate-700 hover:text-blue-600"
            >
              Solutions
            </button>
            <button
              onClick={() => scrollToSection('about')}
              className="block w-full text-left py-2 text-base font-medium text-slate-700 hover:text-blue-600"
            >
              About
            </button>
            <div className="pt-2 space-y-2">
              {user ? (
                <Link
                  to="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-xl shadow-sm"
                >
                  Go to Dashboard
                  <ArrowRight size={16} />
                </Link>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => openAuthModal('getstarted')}
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-xl shadow-sm cursor-pointer"
                  >
                    <span>Get Started</span>
                    <ArrowRight size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => openAuthModal('signin')}
                    className="w-full flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold py-2.5 px-4 rounded-xl transition-colors cursor-pointer text-sm"
                  >
                    Sign In
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* ======================================================== */}
      {/* 2. PREMIUM HERO SECTION                                  */}
      {/* ======================================================== */}
      <section id="hero" className="relative pt-12 pb-20 lg:pt-20 lg:pb-28 overflow-hidden bg-gradient-to-b from-slate-50 via-blue-50/20 to-white">
        
        {/* Subtle Decorative Background Blurs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-blue-400/10 via-cyan-300/10 to-indigo-400/10 rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            
            {/* Left Content Column (7 cols on lg) */}
            <div className="lg:col-span-7 space-y-6 text-left">
              
              {/* Product Badge */}
              <div className="inline-flex items-center gap-2 bg-blue-50/80 border border-blue-200/60 rounded-full px-3.5 py-1.5 text-xs font-semibold text-blue-700 shadow-xs">
                <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
                Intelligent Enterprise CRM Platform
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-bold tracking-tight text-slate-900 leading-[1.12]">
                Build Stronger Relationships.<br />
                <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-600 bg-clip-text text-transparent">
                  Grow Smarter.
                </span>
              </h1>

              {/* Supporting Description */}
              <p className="text-lg text-slate-600 leading-relaxed max-w-xl font-normal">
                CRM360 brings your customers, leads, opportunities, and teams together in one intelligent platform—helping your business stay organized and grow with confidence.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  onClick={() => scrollToSection('features')}
                  className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-base px-6 py-3.5 rounded-xl shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer"
                >
                  Explore Features
                  <ArrowRight size={18} />
                </button>
                {user ? (
                  <Link
                    to="/dashboard"
                    className="inline-flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 font-semibold text-base px-6 py-3.5 rounded-xl border border-slate-200 shadow-xs transition-all duration-200"
                  >
                    Go to Dashboard
                  </Link>
                ) : (
                  <button
                    type="button"
                    onClick={() => openAuthModal('signin')}
                    className="inline-flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 font-semibold text-base px-6 py-3.5 rounded-xl border border-slate-200 shadow-xs transition-all duration-200 cursor-pointer"
                  >
                    Sign In
                  </button>
                )}
              </div>

              {/* Trust & Capability Highlights */}
              <div className="pt-6 border-t border-slate-200/80 flex flex-wrap items-center gap-x-8 gap-y-3 text-xs font-medium text-slate-500">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-500" />
                  <span>360° Visibility</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-500" />
                  <span>Role-Based Security</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-500" />
                  <span>Real-Time Field Tracking</span>
                </div>
              </div>
            </div>

            {/* Right Column: CRM Dashboard Preview (5 cols on lg) */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                
                {/* Preview Frame */}
                <div className="bg-white rounded-2xl shadow-xl shadow-slate-900/10 border border-slate-200/90 overflow-hidden">
                  
                  {/* Window Bar */}
                  <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                      <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                      <span className="ml-2 text-xs font-medium text-slate-300">CRM360 Enterprise Dashboard</span>
                    </div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider bg-slate-800 text-cyan-400 px-2 py-0.5 rounded">
                      Preview
                    </span>
                  </div>

                  {/* Body Content */}
                  <div className="p-5 space-y-4 bg-slate-50/50">
                    
                    {/* Top KPI Metrics */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs">
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Customers</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">1,280+</div>
                        <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">+14% MoM</div>
                      </div>
                      <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs">
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Active Leads</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">342</div>
                        <div className="text-[10px] text-blue-600 font-semibold mt-0.5">Qualified</div>
                      </div>
                      <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs">
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Pipeline</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">$4.2M</div>
                        <div className="text-[10px] text-purple-600 font-semibold mt-0.5">84 Deals</div>
                      </div>
                    </div>

                    {/* Sales Pipeline Stage Breakdown */}
                    <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold text-slate-800">Sales Pipeline Stages</span>
                        <span className="text-[11px] font-semibold text-slate-500">Won Revenue: $1.85M</span>
                      </div>
                      
                      <div className="space-y-2">
                        <div>
                          <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                            <span>Proposal Sent</span>
                            <span>$1.4M (35%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-600 rounded-full w-[35%]" />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                            <span>Negotiation</span>
                            <span>$1.1M (28%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-600 rounded-full w-[28%]" />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                            <span>Closed Won</span>
                            <span>$1.7M (42%)</span>
                          </div>
                          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full w-[42%]" />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Recent Activities Mini-Feed */}
                    <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs">
                      <div className="text-xs font-bold text-slate-800 mb-2.5">Recent Activities</div>
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between text-slate-700">
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                            <span className="font-medium truncate max-w-[170px]">Meeting with TechCorp</span>
                          </div>
                          <span className="text-[10px] text-slate-400 font-medium">Today, 2:30 PM</span>
                        </div>
                        <div className="flex items-center justify-between text-slate-700">
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <span className="font-medium truncate max-w-[170px]">Deal Closed: Horizon Healthcare</span>
                          </div>
                          <span className="text-[10px] text-emerald-600 font-semibold">+$120k Won</span>
                        </div>
                      </div>
                    </div>

                    {/* Preview Notice Caption */}
                    <div className="text-center text-[11px] text-slate-400 font-medium pt-1">
                      Illustrative product preview &bull; Connect to view your data
                    </div>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 3. CRM360 FEATURES SECTION                               */}
      {/* ======================================================== */}
      <section id="features" className="py-20 lg:py-28 bg-white border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-3.5 py-1 text-xs font-semibold text-blue-700">
              Core Capabilities
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
              Everything to Accelerate Your Customer Lifecycle
            </h2>
            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
              Purpose-built CRM modules engineered to streamline daily operations, keep teams aligned, and drive scalable enterprise growth.
            </p>
          </div>

          {/* 6 Feature Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            {/* 1. Lead Management */}
            <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs hover:shadow-xl hover:border-blue-200 transition-all duration-300 group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-blue-600 group-hover:text-white transition-all duration-200">
                  <Users size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                  Lead Management
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                  Capture, organize, and track leads through your sales process.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Check size={14} className="text-blue-600" />
                <span>Source tracking &amp; status progression</span>
              </div>
            </div>

            {/* 2. Customer Management */}
            <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs hover:shadow-xl hover:border-emerald-200 transition-all duration-300 group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-200">
                  <Building2 size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                  Customer Management
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                  Keep customer records and relationship information organized.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Check size={14} className="text-emerald-600" />
                <span>Accounts, contacts, and unified history</span>
              </div>
            </div>

            {/* 3. Sales Pipeline */}
            <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs hover:shadow-xl hover:border-purple-200 transition-all duration-300 group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 border border-purple-100 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-purple-600 group-hover:text-white transition-all duration-200">
                  <TrendingUp size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                  Sales Pipeline
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                  Track opportunities and monitor progress across deal stages.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Check size={14} className="text-purple-600" />
                <span>Deal staging &amp; won revenue metrics</span>
              </div>
            </div>

            {/* 4. Team Collaboration */}
            <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs hover:shadow-xl hover:border-amber-200 transition-all duration-300 group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 border border-amber-100 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-amber-600 group-hover:text-white transition-all duration-200">
                  <Calendar size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                  Team Collaboration
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                  Coordinate employee activities, meetings, and tasks.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Check size={14} className="text-amber-600" />
                <span>Task delegation &amp; meeting schedules</span>
              </div>
            </div>

            {/* 5. Reports & Analytics */}
            <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs hover:shadow-xl hover:border-cyan-200 transition-all duration-300 group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-cyan-50 text-cyan-600 border border-cyan-100 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-cyan-600 group-hover:text-white transition-all duration-200">
                  <BarChart3 size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                  Reports &amp; Analytics
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                  Understand CRM performance through charts and reports.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Check size={14} className="text-cyan-600" />
                <span>Live KPI summaries &amp; visual charts</span>
              </div>
            </div>

            {/* 6. Geotracking & Visits */}
            <div className="bg-white rounded-2xl p-7 border border-slate-200/80 shadow-xs hover:shadow-xl hover:border-rose-200 transition-all duration-300 group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 border border-rose-100 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-rose-600 group-hover:text-white transition-all duration-200">
                  <MapPin size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                  Geotracking &amp; Visits
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                  Manage field activities and customer visits.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Check size={14} className="text-rose-600" />
                <span>GPS coordinates &amp; client visit verification</span>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 4. HOW CRM360 WORKS SECTION                              */}
      {/* ======================================================== */}
      <section id="solutions" className="py-20 lg:py-28 bg-slate-50/80 border-t border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-full px-3.5 py-1 text-xs font-semibold text-indigo-700">
              Proven Architecture
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
              How CRM360 Works
            </h2>
            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
              A structured, dependable framework designed to turn disjointed customer data into measurable business results.
            </p>
          </div>

          {/* 3-Step Process (Horizontal on Desktop, Vertical on Mobile) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            
            {/* Step 1 */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200/80 shadow-xs relative">
              <div className="flex items-center justify-between mb-6">
                <span className="text-3xl font-extrabold text-blue-600 font-mono">01</span>
                <span className="text-xs font-semibold bg-blue-50 text-blue-700 px-3 py-1 rounded-full">
                  Foundation
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Organize Your Data
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed mb-4">
                Manage customers, contacts, and leads.
              </p>
              <p className="text-xs text-slate-500 leading-normal border-t border-slate-100 pt-3">
                Centralize company profiles, designated points of contact, and raw inbound inquiries into a clean, searchable database.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200/80 shadow-xs relative">
              <div className="flex items-center justify-between mb-6">
                <span className="text-3xl font-extrabold text-indigo-600 font-mono">02</span>
                <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full">
                  Execution
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Manage Your Workflow
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed mb-4">
                Track opportunities, tasks, and team activities.
              </p>
              <p className="text-xs text-slate-500 leading-normal border-t border-slate-100 pt-3">
                Seamlessly guide deals through pipeline stages, schedule customer meetings, assign overdue tasks, and track field visits.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200/80 shadow-xs relative">
              <div className="flex items-center justify-between mb-6">
                <span className="text-3xl font-extrabold text-cyan-600 font-mono">03</span>
                <span className="text-xs font-semibold bg-cyan-50 text-cyan-700 px-3 py-1 rounded-full">
                  Growth
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Monitor Your Progress
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed mb-4">
                Use reports and dashboard insights to make informed decisions.
              </p>
              <p className="text-xs text-slate-500 leading-normal border-t border-slate-100 pt-3">
                Evaluate conversion ratios, review total won revenue, identify overdue bottlenecks, and forecast sales accurately.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 5. PRODUCT SHOWCASE SECTION                              */}
      {/* ======================================================== */}
      <section id="about" className="py-20 lg:py-28 bg-white border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-14 space-y-4">
            <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-3.5 py-1 text-xs font-semibold text-blue-700">
              Interactive Product Showcase
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
              Everything You Need. One Powerful CRM.
            </h2>
            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
              Designed for speed, clarity, and precision. Explore how CRM360 brings together deal management, customer records, and field tracking.
            </p>
          </div>

          {/* Interactive Navigation Tabs */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex p-1.5 bg-slate-100/90 rounded-2xl border border-slate-200/80">
              <button
                onClick={() => setActiveTab('pipeline')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                  activeTab === 'pipeline'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Sales Pipeline
              </button>
              <button
                onClick={() => setActiveTab('customer')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                  activeTab === 'customer'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Customer Hub
              </button>
              <button
                onClick={() => setActiveTab('field')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                  activeTab === 'field'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Field Operations
              </button>
            </div>
          </div>

          {/* Product Showcase Window */}
          <div className="bg-slate-900 rounded-3xl p-4 sm:p-8 shadow-2xl border border-slate-800 text-white max-w-5xl mx-auto">
            
            {/* Window Header */}
            <div className="flex items-center justify-between pb-6 border-b border-slate-800 text-xs">
              <div className="flex items-center gap-3">
                <div className="flex gap-2">
                  <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-amber-400 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
                </div>
                <span className="text-slate-400 font-mono ml-2 hidden sm:inline">
                  crm360.app / {activeTab}
                </span>
              </div>
              <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Simulated Enterprise View</span>
              </div>
            </div>

            {/* Tab 1: Sales Pipeline Showcase */}
            {activeTab === 'pipeline' && (
              <div className="pt-6 animate-fade-up">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  
                  {/* Column 1: Discovery */}
                  <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-300 pb-2 mb-3 border-b border-slate-700/40">
                      <span>Discovery</span>
                      <span className="bg-slate-700 px-2 py-0.5 rounded text-[10px]">3 Deals</span>
                    </div>
                    <div className="space-y-3">
                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-700 text-xs">
                        <div className="font-semibold text-white">Apex Logistics</div>
                        <div className="text-slate-400 mt-1">$45,000 &bull; Enterprise</div>
                        <div className="mt-2 text-[10px] text-blue-400 font-medium">Assigned: Alex Taylor</div>
                      </div>
                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-700 text-xs">
                        <div className="font-semibold text-white">Delta Media</div>
                        <div className="text-slate-400 mt-1">$28,000 &bull; Mid-Market</div>
                        <div className="mt-2 text-[10px] text-blue-400 font-medium">Assigned: Sarah Jenkins</div>
                      </div>
                    </div>
                  </div>

                  {/* Column 2: Proposal */}
                  <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60">
                    <div className="flex items-center justify-between text-xs font-semibold text-blue-300 pb-2 mb-3 border-b border-slate-700/40">
                      <span>Proposal Sent</span>
                      <span className="bg-blue-900/60 text-blue-300 px-2 py-0.5 rounded text-[10px]">4 Deals</span>
                    </div>
                    <div className="space-y-3">
                      <div className="bg-slate-900 p-3 rounded-lg border border-blue-900/40 text-xs">
                        <div className="font-semibold text-white">Global Cloud Systems</div>
                        <div className="text-slate-400 mt-1">$120,000 &bull; Custom Suite</div>
                        <div className="mt-2 text-[10px] text-blue-400 font-medium">Reviewing SOW</div>
                      </div>
                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-700 text-xs">
                        <div className="font-semibold text-white">Pinnacle Bio</div>
                        <div className="text-slate-400 mt-1">$65,000 &bull; Standard</div>
                        <div className="mt-2 text-[10px] text-blue-400 font-medium">Follow-up scheduled</div>
                      </div>
                    </div>
                  </div>

                  {/* Column 3: Negotiation */}
                  <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60">
                    <div className="flex items-center justify-between text-xs font-semibold text-amber-300 pb-2 mb-3 border-b border-slate-700/40">
                      <span>Negotiation</span>
                      <span className="bg-amber-900/60 text-amber-300 px-2 py-0.5 rounded text-[10px]">2 Deals</span>
                    </div>
                    <div className="space-y-3">
                      <div className="bg-slate-900 p-3 rounded-lg border border-amber-900/40 text-xs">
                        <div className="font-semibold text-white">Nexus Aerospace</div>
                        <div className="text-slate-400 mt-1">$210,000 &bull; Enterprise</div>
                        <div className="mt-2 text-[10px] text-amber-400 font-medium">Security Audit Passed</div>
                      </div>
                    </div>
                  </div>

                  {/* Column 4: Closed Won */}
                  <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60">
                    <div className="flex items-center justify-between text-xs font-semibold text-emerald-300 pb-2 mb-3 border-b border-slate-700/40">
                      <span>Closed Won</span>
                      <span className="bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded text-[10px]">$1.85M</span>
                    </div>
                    <div className="space-y-3">
                      <div className="bg-slate-900 p-3 rounded-lg border border-emerald-900/40 text-xs">
                        <div className="font-semibold text-white">Horizon Healthcare</div>
                        <div className="text-slate-400 mt-1">$120,000 &bull; 3-Year Plan</div>
                        <div className="mt-2 text-[10px] text-emerald-400 font-medium">Onboarding in progress</div>
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            )}

            {/* Tab 2: Customer Hub Showcase */}
            {activeTab === 'customer' && (
              <div className="pt-6 animate-fade-up">
                <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700/70">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-700">
                    <div>
                      <div className="flex items-center gap-3">
                        <h4 className="text-xl font-bold text-white">Horizon Healthcare Technologies</h4>
                        <span className="bg-emerald-500/20 text-emerald-300 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                          Active Customer
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">Enterprise Tier &bull; Account #HH-8921 &bull; Industry: Medical Systems</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-400">Total Lifetime Value</span>
                      <div className="text-2xl font-bold text-white">$120,000</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
                    <div className="space-y-3">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Primary Contacts</span>
                      <div className="bg-slate-900 p-3 rounded-xl border border-slate-700 text-xs">
                        <div className="font-semibold text-white">Dr. Elena Ramos</div>
                        <div className="text-slate-400">Chief Medical Officer</div>
                        <div className="text-slate-500 mt-1">elena.ramos@horizonhealth.org</div>
                      </div>
                    </div>
                    <div className="md:col-span-2 space-y-3">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Recent Engagement Timeline</span>
                      <div className="space-y-2 text-xs">
                        <div className="bg-slate-900 p-3 rounded-xl border border-slate-700 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <PhoneCall size={16} className="text-blue-400" />
                            <span>Quarterly Business Review call completed</span>
                          </div>
                          <span className="text-slate-400">Yesterday</span>
                        </div>
                        <div className="bg-slate-900 p-3 rounded-xl border border-slate-700 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Mail size={16} className="text-emerald-400" />
                            <span>Implementation sign-off document confirmed</span>
                          </div>
                          <span className="text-slate-400">3 days ago</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Field Operations Showcase */}
            {activeTab === 'field' && (
              <div className="pt-6 animate-fade-up">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-800/60 p-5 rounded-2xl border border-slate-700/60 space-y-4">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Live Visit Schedule</span>
                    <div className="space-y-3 text-xs">
                      <div className="bg-slate-900 p-3 rounded-xl border border-emerald-900/40">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white">Downtown Tech Campus</span>
                          <span className="text-emerald-400 font-semibold text-[10px]">Completed</span>
                        </div>
                        <div className="text-slate-400 mt-1">Rep: Marcus Vance &bull; 10:15 AM</div>
                      </div>
                      <div className="bg-slate-900 p-3 rounded-xl border border-blue-900/40">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white">Northwest Medical Center</span>
                          <span className="text-blue-400 font-semibold text-[10px]">In Progress</span>
                        </div>
                        <div className="text-slate-400 mt-1">Rep: Lisa Chen &bull; 1:30 PM</div>
                      </div>
                    </div>
                  </div>

                  <div className="md:col-span-2 bg-slate-800/60 p-5 rounded-2xl border border-slate-700/60 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Geographic Dispatch Map (Leaflet Integration)</span>
                        <span className="text-xs text-cyan-400 font-medium">GPS Sync Active</span>
                      </div>
                      <div className="h-44 bg-slate-950 rounded-xl border border-slate-700 flex items-center justify-center relative overflow-hidden">
                        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px]" />
                        <div className="relative z-10 flex flex-col items-center text-center p-4">
                          <MapPin size={32} className="text-cyan-400 mb-2 animate-bounce" />
                          <span className="text-sm font-semibold text-white">Interactive Geo-Coordinates Recorded</span>
                          <span className="text-xs text-slate-400 mt-1">Latitude: 37.7749 &bull; Longitude: -122.4194 &bull; Accurate within 5m</span>
                        </div>
                      </div>
                    </div>
                    <div className="pt-3 text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Field rep verification powered by integrated GPS geocoding</span>
                      <span className="text-emerald-400 font-semibold">100% Audit Verified</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 6. FINAL CALL TO ACTION                                  */}
      {/* ======================================================== */}
      <section className="py-20 lg:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 text-white p-10 sm:p-16 lg:p-20 shadow-2xl border border-slate-800 text-center">
            
            {/* Subtle Glow Accents */}
            <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10 max-w-2xl mx-auto space-y-6">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-tight">
                Ready to Connect, Manage, and Grow?
              </h2>
              <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-normal">
                Bring your customer relationships and business workflows together with CRM360.
              </p>
              <div className="pt-4">
                {user ? (
                  <Link
                    to="/dashboard"
                    className="inline-flex items-center gap-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base px-8 py-4 rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all duration-200"
                  >
                    Go to Dashboard
                    <ArrowRight size={18} />
                  </Link>
                ) : (
                  <button
                    type="button"
                    onClick={() => openAuthModal('signin')}
                    className="inline-flex items-center gap-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base px-8 py-4 rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all duration-200 cursor-pointer"
                  >
                    Sign In to CRM360
                    <ArrowRight size={18} />
                  </button>
                )}
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 7. PROFESSIONAL FOOTER                                   */}
      {/* ======================================================== */}
      <footer className="bg-slate-950 text-white border-t border-slate-800/80 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 pb-8 border-b border-slate-800">
            
            {/* Logo, Wordmark & Tagline */}
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 bg-white rounded-xl p-1 flex items-center justify-center border border-white/20 shadow-sm flex-shrink-0">
                <img 
                  src="/crm360-mark.png" 
                  alt="CRM360" 
                  className="w-full h-full object-contain"
                />
              </div>
              <div>
                <span className="text-xl font-bold tracking-tight text-white block leading-none">
                  CRM<span className="text-blue-500">360</span>
                </span>
                <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mt-1 block">
                  Connect &bull; Manage &bull; Grow
                </span>
              </div>
            </div>

            {/* Working Footer Links */}
            <nav className="flex items-center gap-8 text-sm font-medium text-slate-400">
              <button 
                onClick={() => scrollToSection('hero')} 
                className="hover:text-white transition-colors cursor-pointer"
              >
                Home
              </button>
              <button 
                onClick={() => scrollToSection('features')} 
                className="hover:text-white transition-colors cursor-pointer"
              >
                Features
              </button>
              <button 
                onClick={() => scrollToSection('about')} 
                className="hover:text-white transition-colors cursor-pointer"
              >
                About
              </button>
              {user ? (
                <Link 
                  to="/dashboard" 
                  className="hover:text-white transition-colors text-blue-400"
                >
                  Dashboard
                </Link>
              ) : (
                <button 
                  type="button"
                  onClick={() => openAuthModal('signin')} 
                  className="hover:text-white transition-colors text-blue-400 cursor-pointer"
                >
                  Sign In
                </button>
              )}
            </nav>

          </div>

          {/* Copyright Row */}
          <div className="pt-8 text-center text-xs text-slate-500 font-normal">
            &copy; 2026 CRM360. All rights reserved.
          </div>
        </div>
      </footer>

      {/* ======================================================== */}
      {/* 8. INTEGRATED LOGIN MODAL                                */}
      {/* ======================================================== */}
      <LoginModal 
        isOpen={isLoginModalOpen} 
        onClose={() => setIsLoginModalOpen(false)} 
        initialMode={modalMode}
      />

    </div>
  );
}
