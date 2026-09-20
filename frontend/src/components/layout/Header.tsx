import { Bell, UserCircle } from 'lucide-react';

export default function Header() {
  return (
    <header className="flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-8 shadow-sm text-slate-700">
      <div className="flex items-center gap-2">
        <h2 className="text-xl font-semibold text-slate-800">
          {/* We can inject dynamic page title here later using a context or route matching */}
          Portal
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <button className="flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 transition-colors">
          <Bell className="h-5 w-5 text-slate-500" />
        </button>
        <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-slate-700">Clinical User</span>
            <span className="text-xs text-slate-500">Administrator</span>
          </div>
          <button className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-brand-600 hover:bg-slate-200 transition-colors">
            <UserCircle className="h-6 w-6" />
          </button>
        </div>
      </div>
    </header>
  );
}
