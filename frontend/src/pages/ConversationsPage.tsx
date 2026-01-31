import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import * as api from '@/lib/api';
import { MessageCircle } from 'lucide-react';

interface Thread {
  id: string;
  character: {
    id: string;
    name: string;
    avatar_url: string | null;
  };
  created_at: string;
  updated_at: string;
}

export function ConversationsPage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const data = await api.getThreads();
        setThreads(data.data);
      } catch (error) {
        console.error('Failed to fetch threads:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchThreads();
  }, []);

  const formatDate = (dateString: string) => {
    // バックエンドはUTC時間を返すが、Zが付いていないので明示的に追加
    const utcDateString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
    const date = new Date(utcDateString);
    const now = new Date();
    
    // 日本時間での日付を取得して比較
    const jpFormatter = new Intl.DateTimeFormat('ja-JP', { 
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
    const dateJP = jpFormatter.format(date);
    const nowJP = jpFormatter.format(now);
    
    // 昨日の日付を計算
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayJP = jpFormatter.format(yesterday);
    
    if (dateJP === nowJP) {
      // 今日
      return date.toLocaleTimeString('ja-JP', { 
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'Asia/Tokyo'
      });
    } else if (dateJP === yesterdayJP) {
      return '昨日';
    } else {
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      if (days < 7) {
        return `${days}日前`;
      } else {
        return date.toLocaleDateString('ja-JP', { 
          month: 'short', 
          day: 'numeric',
          timeZone: 'Asia/Tokyo'
        });
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">会話履歴</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      ) : threads.length === 0 ? (
        <div className="text-center py-12">
          <MessageCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500 mb-2">まだ会話がありません</p>
          <p className="text-sm text-gray-400">
            マーケットからキャラクターを選んで会話を始めましょう
          </p>
          <Link
            to="/marketplace"
            className="inline-block mt-4 text-purple-600 hover:underline"
          >
            マーケットへ
          </Link>
        </div>
      ) : (
        <div className="space-y-2">
          {threads.map((thread) => (
            <Link key={thread.id} to={`/conversation/${thread.id}`}>
              <Card className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <img
                      src={`https://api.dicebear.com/7.x/lorelei/svg?seed=${encodeURIComponent(thread.character.name)}&backgroundColor=b6e3f4,c0aede,d1d4f9`}
                      alt={thread.character.name}
                      className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-100 to-pink-100"
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold truncate">
                        {thread.character.name}
                      </h3>
                      <p className="text-sm text-gray-500 truncate">
                        タップして会話を続ける
                      </p>
                    </div>
                    <span className="text-xs text-gray-400">
                      {formatDate(thread.updated_at)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
