export default function Logo({ variant = 'dark', className = '' }) {
  const primary = variant === 'light' ? '#ffffff' : '#0f172a'; // slate-900
  const secondary = variant === 'light' ? '#60a5fa' : '#2563eb'; // blue-400 / blue-600
  const node = variant === 'light' ? '#93c5fd' : '#3b82f6'; // blue-300 / blue-500

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="flex-shrink-0">
        {/* Outer 360 Ring */}
        <path d="M 50 15 A 35 35 0 1 1 15 50" stroke={secondary} strokeWidth="8" strokeLinecap="round" />
        <path d="M 18 32 A 35 35 0 0 1 32 18" stroke={secondary} strokeWidth="8" strokeLinecap="round" opacity="0.4" />
        
        {/* Inner network lines */}
        <path d="M 50 15 L 85 50 L 50 85 L 15 50 Z" stroke={primary} strokeWidth="4" strokeLinejoin="round" opacity="0.2" />
        <path d="M 50 15 L 50 85 M 15 50 L 85 50" stroke={primary} strokeWidth="4" opacity="0.2" />
        
        {/* Nodes */}
        <circle cx="50" cy="15" r="8" fill={primary} />
        <circle cx="85" cy="50" r="8" fill={node} />
        <circle cx="50" cy="85" r="8" fill={primary} />
        <circle cx="15" cy="50" r="8" fill={node} />
        <circle cx="50" cy="50" r="10" fill={secondary} />
      </svg>
      <span className={`text-2xl font-extrabold tracking-tight ${variant === 'light' ? 'text-white' : 'text-slate-900'}`}>
        CRM<span className={variant === 'light' ? 'text-blue-400' : 'text-blue-600'}>360</span>
      </span>
    </div>
  );
}
