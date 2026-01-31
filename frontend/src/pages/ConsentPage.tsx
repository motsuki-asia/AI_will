import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

export function ConsentPage() {
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { consent } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await consent();
      navigate('/onboarding/age');
    } catch (err) {
      setError(err instanceof Error ? err.message : '同意の記録に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const canSubmit = termsAccepted && privacyAccepted;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 relative">
      {/* Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-50 via-pink-50 to-white dark:from-gray-900 dark:via-purple-950/30 dark:to-gray-900 -z-10" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-100/40 via-transparent to-transparent dark:from-purple-900/20 -z-10" />
      
      <Card className="w-full max-w-lg bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">利用規約への同意</CardTitle>
          <CardDescription>
            サービスをご利用いただくには、以下の規約に同意していただく必要があります
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-md">
                {error}
              </div>
            )}

            {/* Terms of Service */}
            <div className="space-y-3">
              <h3 className="font-semibold">利用規約</h3>
              <ScrollArea className="h-32 rounded-md border p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                  <p>1. 本サービスは、AIキャラクターとの会話体験を提供します。</p>
                  <p>2. ユーザーは、本サービスを適切な方法で利用するものとします。</p>
                  <p>3. 不適切なコンテンツの生成を目的とした利用は禁止されています。</p>
                  <p>4. サービスの内容は予告なく変更される場合があります。</p>
                  <p>5. 本規約は日本法に準拠します。</p>
                </div>
              </ScrollArea>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="terms"
                  checked={termsAccepted}
                  onCheckedChange={(checked) => setTermsAccepted(checked === true)}
                />
                <label htmlFor="terms" className="text-sm cursor-pointer">
                  利用規約に同意します
                </label>
              </div>
            </div>

            {/* Privacy Policy */}
            <div className="space-y-3">
              <h3 className="font-semibold">プライバシーポリシー</h3>
              <ScrollArea className="h-32 rounded-md border p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                  <p>1. 当社は、お客様のプライバシーを尊重します。</p>
                  <p>2. 収集した個人情報は、サービス提供の目的でのみ使用します。</p>
                  <p>3. 会話データは、サービス改善のために匿名化して分析される場合があります。</p>
                  <p>4. お客様は、いつでもデータの削除を要求することができます。</p>
                  <p>5. 第三者への個人情報の提供は、法令に基づく場合を除き行いません。</p>
                </div>
              </ScrollArea>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="privacy"
                  checked={privacyAccepted}
                  onCheckedChange={(checked) => setPrivacyAccepted(checked === true)}
                />
                <label htmlFor="privacy" className="text-sm cursor-pointer">
                  プライバシーポリシーに同意します
                </label>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={!canSubmit || isLoading}>
              {isLoading ? '処理中...' : '同意して次へ'}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
