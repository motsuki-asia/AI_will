import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Home, MessageCircle, Settings, LogOut, Sparkles } from 'lucide-react';

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen relative">
      {/* Background gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-50 via-pink-50 to-white dark:from-gray-900 dark:via-purple-950/30 dark:to-gray-900 -z-10" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-100/40 via-transparent to-transparent dark:from-purple-900/20 -z-10" />
      
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-md">
        <div className="container flex h-14 items-center justify-between px-4">
          <Link to="/marketplace" className="flex items-center space-x-2">
            <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              AI will
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {user?.display_name || user?.email}
            </span>
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-6 pb-20">
        <Outlet />
      </main>

      {/* Bottom navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-white/80 dark:bg-gray-900/80 backdrop-blur-md">
        <div className="container mx-auto flex justify-around py-2">
          <Link
            to="/marketplace"
            className="flex flex-col items-center p-2 text-gray-600 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400"
          >
            <Home className="h-5 w-5" />
            <span className="text-xs mt-1">ホーム</span>
          </Link>
          <Link
            to="/conversations"
            className="flex flex-col items-center p-2 text-gray-600 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400"
          >
            <MessageCircle className="h-5 w-5" />
            <span className="text-xs mt-1">会話</span>
          </Link>
          <Link
            to="/partner-create"
            className="flex flex-col items-center p-2 text-gray-600 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400"
          >
            <Sparkles className="h-5 w-5" />
            <span className="text-xs mt-1">パートナー生成</span>
          </Link>
          <Link
            to="/settings"
            className="flex flex-col items-center p-2 text-gray-600 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400"
          >
            <Settings className="h-5 w-5" />
            <span className="text-xs mt-1">設定</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}
