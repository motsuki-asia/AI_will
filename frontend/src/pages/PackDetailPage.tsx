import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import * as api from '@/lib/api';
import { ArrowLeft, MessageCircle, Sparkles } from 'lucide-react';

interface Pack {
  id: string;
  pack_type: 'persona' | 'scenario';
  name: string;
  description: string;
  price: number;
  is_free: boolean;
  creator: {
    id: string;
    display_name: string;
  };
}

interface PackItem {
  id: string;
  item_type: string;
  item_id: string;
  name: string;
  description: string | null;
  avatar_url: string | null;
}

export function PackDetailPage() {
  const { packId } = useParams<{ packId: string }>();
  const navigate = useNavigate();
  const [pack, setPack] = useState<Pack | null>(null);
  const [items, setItems] = useState<PackItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!packId) return;
      try {
        const [packData, itemsData] = await Promise.all([
          api.getPack(packId),
          api.getPackItems(packId),
        ]);
        setPack(packData.pack);
        setItems(itemsData.data);
      } catch (error) {
        console.error('Failed to fetch pack:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [packId]);

  const handleStartConversation = async (characterId: string) => {
    if (!packId) return;
    setIsStarting(true);
    try {
      const result = await api.createThread(packId, characterId);
      navigate(`/conversation/${result.thread.id}`);
    } catch (error) {
      console.error('Failed to create thread:', error);
      alert('会話の開始に失敗しました');
    } finally {
      setIsStarting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!pack) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">パックが見つかりませんでした</p>
        <Button variant="link" onClick={() => navigate('/marketplace')}>
          マーケットに戻る
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back Button */}
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
        <ArrowLeft className="h-4 w-4 mr-1" />
        戻る
      </Button>

      {/* Pack Header */}
      <div className="text-center">
        <div className="aspect-video max-w-sm mx-auto mb-4 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-xl flex items-center justify-center overflow-hidden">
          {items.filter((item) => item.item_type === 'character')[0]?.avatar_url ? (
            <img
              src={items.filter((item) => item.item_type === 'character')[0].avatar_url!.startsWith('/static/') ? `http://localhost:8080${items.filter((item) => item.item_type === 'character')[0].avatar_url}` : items.filter((item) => item.item_type === 'character')[0].avatar_url!}
              alt={pack.name}
              className="w-40 h-40 object-cover"
            />
          ) : (
            <div className="w-40 h-40 flex items-center justify-center text-gray-400">
              <Sparkles className="h-16 w-16" />
            </div>
          )}
        </div>
        <span
          className={`inline-block text-xs px-3 py-1 rounded-full mb-2 ${
            pack.pack_type === 'persona'
              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
              : 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300'
          }`}
        >
          {pack.pack_type === 'persona' ? 'ペルソナ' : 'シナリオ'}
        </span>
        <h1 className="text-2xl font-bold mb-2">{pack.name}</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-2">{pack.description}</p>
        <p className="text-sm text-gray-500">by {pack.creator.display_name}</p>
        <p className="text-lg font-semibold text-green-600 mt-2">
          {pack.is_free ? '無料' : `¥${pack.price}`}
        </p>
      </div>

      {/* Characters */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">キャラクター</h2>
        {items.filter((item) => item.item_type === 'character').map((character) => (
          <Card key={character.id}>
            <CardContent className="p-4">
              <div className="flex items-start gap-4">
                <img
                  src={character.avatar_url ? (character.avatar_url.startsWith('/static/') ? `http://localhost:8080${character.avatar_url}` : character.avatar_url) : '/placeholder.png'}
                  alt={character.name}
                  className="h-16 w-16 rounded-full object-cover bg-gradient-to-br from-purple-100 to-pink-100"
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{character.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {character.description || 'このキャラクターと会話を楽しみましょう'}
                  </p>
                </div>
              </div>
              <Button
                className="w-full mt-4"
                onClick={() => handleStartConversation(character.item_id)}
                disabled={isStarting}
              >
                <MessageCircle className="h-4 w-4 mr-2" />
                {isStarting ? '開始中...' : '会話を始める'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
