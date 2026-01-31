import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

type AgeGroup = 'u13' | 'u18' | 'adult';

interface AgeOption {
  value: AgeGroup;
  label: string;
  description: string;
}

const ageOptions: AgeOption[] = [
  { value: 'u13', label: '13歳未満', description: '一部のコンテンツが制限されます' },
  { value: 'u18', label: '13〜17歳', description: '年齢に応じたコンテンツをお楽しみいただけます' },
  { value: 'adult', label: '18歳以上', description: 'すべてのコンテンツをお楽しみいただけます' },
];

export function AgeVerifyPage() {
  const [selectedAge, setSelectedAge] = useState<AgeGroup | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { ageVerify } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAge) return;

    setError('');
    setIsLoading(true);

    try {
      await ageVerify(selectedAge);
      navigate('/marketplace');
    } catch (err) {
      setError(err instanceof Error ? err.message : '年齢確認に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 relative">
      {/* Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-50 via-pink-50 to-white dark:from-gray-900 dark:via-purple-950/30 dark:to-gray-900 -z-10" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-100/40 via-transparent to-transparent dark:from-purple-900/20 -z-10" />
      
      <Card className="w-full max-w-lg bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">年齢確認</CardTitle>
          <CardDescription>
            適切なコンテンツを表示するため、年齢をお知らせください
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-3">
              {ageOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSelectedAge(option.value)}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                    selectedAge === option.value
                      ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="font-semibold">{option.label}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {option.description}
                  </div>
                </button>
              ))}
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              ※ 年齢情報は一度設定すると変更できません
            </p>
          </CardContent>
          <CardFooter>
            <Button
              type="submit"
              className="w-full"
              disabled={!selectedAge || isLoading}
            >
              {isLoading ? '処理中...' : '確認して始める'}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
