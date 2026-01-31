import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { User, Shield, Trash2, LogOut } from 'lucide-react';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isLogoutDialogOpen, setIsLogoutDialogOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">設定</h1>

      {/* Profile Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            プロフィール
          </CardTitle>
          <CardDescription>アカウント情報</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-gray-500">メールアドレス</label>
            <p className="font-medium">{user?.email}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">表示名</label>
            <p className="font-medium">{user?.display_name || '未設定'}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">年齢区分</label>
            <p className="font-medium">
              {user?.age_group === 'adult'
                ? '18歳以上'
                : user?.age_group === 'u18'
                ? '13〜17歳'
                : '13歳未満'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Privacy Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            プライバシー
          </CardTitle>
          <CardDescription>データの管理</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">会話履歴の削除</p>
              <p className="text-sm text-gray-500">すべての会話履歴を削除します</p>
            </div>
            <Button variant="outline" size="sm">
              削除
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200 dark:border-red-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <Trash2 className="h-5 w-5" />
            危険な操作
          </CardTitle>
          <CardDescription>この操作は取り消せません</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">アカウント削除</p>
              <p className="text-sm text-gray-500">アカウントとすべてのデータを削除します</p>
            </div>
            <Button variant="destructive" size="sm" disabled>
              削除（準備中）
            </Button>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Logout */}
      <Dialog open={isLogoutDialogOpen} onOpenChange={setIsLogoutDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="w-full">
            <LogOut className="h-4 w-4 mr-2" />
            ログアウト
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>ログアウト</DialogTitle>
            <DialogDescription>
              本当にログアウトしますか？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsLogoutDialogOpen(false)}>
              キャンセル
            </Button>
            <Button onClick={handleLogout}>ログアウト</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* App Info */}
      <div className="text-center text-sm text-gray-500 py-4">
        <p>AI will v1.0.0</p>
        <p className="mt-1">
          <a href="/terms" className="hover:underline">
            利用規約
          </a>
          {' • '}
          <a href="/privacy" className="hover:underline">
            プライバシーポリシー
          </a>
        </p>
      </div>
    </div>
  );
}
