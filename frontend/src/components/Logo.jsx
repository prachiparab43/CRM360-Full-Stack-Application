export default function Logo({ 
  variant = 'dark', 
  className = '', 
  size = 'default',
  showText = true,
  full = false 
}) {
  if (full) {
    return (
      <div className={`flex items-center ${className}`}>
        <img
          src="/crm360-logo.png"
          alt="CRM360 Logo"
          className="w-28 h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 object-contain"
        />
      </div>
    );
  }

  const sizeClasses = {
    sm: 'w-7 h-7',
    default: 'w-9 h-9',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const imgSize = sizeClasses[size] || sizeClasses.default;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <img
        src="/crm360-logo.png"
        alt="CRM360 Logo"
        className={`${imgSize} object-contain flex-shrink-0 bg-white rounded-lg p-0.5 shadow-sm`}
      />
      {showText && (
        <span className={`text-2xl font-extrabold tracking-tight ${variant === 'light' ? 'text-white' : 'text-slate-900'}`}>
          CRM<span className={variant === 'light' ? 'text-blue-400' : 'text-blue-600'}>360</span>
        </span>
      )}
    </div>
  );
}
