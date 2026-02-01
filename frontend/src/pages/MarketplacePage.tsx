import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import * as api from '@/lib/api';
import { TrendingUp, Star, Clock, MessageCircle, Sparkles } from 'lucide-react';

interface Character {
  id: string;
  name: string;
  description: string | null;
  avatar_url: string | null;
  pack_id: string | null;
  pack_name: string | null;
  is_custom: boolean;
}

type SortOption = 'trend' | 'recommend' | 'new';
type CategoryOption = 'all' | 'anime' | 'gal' | 'imouto' | 'oneesan';

const sortOptions: { id: SortOption; label: string; icon: React.ReactNode }[] = [
  { id: 'trend', label: 'トレンド', icon: <TrendingUp className="h-4 w-4" /> },
  { id: 'recommend', label: 'オススメ', icon: <Star className="h-4 w-4" /> },
  { id: 'new', label: '新着', icon: <Clock className="h-4 w-4" /> },
];

const categoryOptions: { id: CategoryOption; label: string }[] = [
  { id: 'all', label: 'すべて' },
  { id: 'anime', label: 'アニメ' },
  { id: 'gal', label: 'ギャル' },
  { id: 'imouto', label: '妹系' },
  { id: 'oneesan', label: 'お姉さん' },
];

export function MarketplacePage() {
  const navigate = useNavigate();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('trend');
  const [category, setCategory] = useState<CategoryOption>('all');

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        const data = await api.getCharacters();
        let sortedCharacters = [...data.data];
        
        // Apply sort (MVP: simple sorting)
        if (sortBy === 'recommend') {
          sortedCharacters.sort(() => Math.random() - 0.5);
        }
        // 'trend' and 'new' use default order from API
        
        setCharacters(sortedCharacters);
      } catch (error) {
        console.error('Failed to fetch characters:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCharacters();
  }, [sortBy, category]);

  const handleStartConversation = async (character: Character) => {
    setIsStarting(character.id);
    try {
      const result = await api.createThread(character.pack_id, character.id);
      navigate(`/conversation/${result.thread.id}`);
    } catch (error) {
      console.error('Failed to create thread:', error);
      alert('会話の開始に失敗しました');
    } finally {
      setIsStarting(null);
    }
  };

  const getImageUrl = (avatarUrl: string | null): string => {
    if (avatarUrl) {
      if (avatarUrl.startsWith('/static/')) {
        return `http://localhost:8000${avatarUrl}`;
      }
      return avatarUrl;
    }
    return '/placeholder.png';
  };

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="text-center py-8">
        <h1 className="text-3xl font-bold mb-2">
          <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            AI will
          </span>
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          あなただけのAIキャラクターと会話を楽しもう
        </p>
      </div>

      {/* Sort Options */}
      <div className="flex justify-center gap-2 flex-wrap">
        {sortOptions.map((option) => (
          <Button
            key={option.id}
            variant={sortBy === option.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy(option.id)}
            className="gap-1"
          >
            {option.icon}
            {option.label}
          </Button>
        ))}
      </div>

      {/* Category Filter */}
      <ScrollArea className="w-full whitespace-nowrap">
        <div className="flex justify-center gap-2 pb-2">
          {categoryOptions.map((option) => (
            <Button
              key={option.id}
              variant={category === option.id ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setCategory(option.id)}
              className={`rounded-full ${
                category === option.id 
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' 
                  : ''
              }`}
            >
              {option.label}
            </Button>
          ))}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>

      {/* Character Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      ) : characters.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          キャラクターが見つかりませんでした
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {characters.map((character) => (
            <Card 
              key={character.id} 
              className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer h-full"
              onClick={() => handleStartConversation(character)}
            >
              <div className="aspect-square bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 flex items-center justify-center relative overflow-hidden">
                <img
                  src={getImageUrl(character.avatar_url)}
                  alt={character.name}
                  className="w-full h-full object-cover"
                />
                {character.is_custom && (
                  <div className="absolute top-2 right-2 bg-pink-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <Sparkles className="h-3 w-3" />
                    マイパートナー
                  </div>
                )}
                {isStarting === character.id && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                  </div>
                )}
              </div>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <MessageCircle className="h-4 w-4 text-purple-500" />
                  <h3 className="font-semibold text-lg line-clamp-1">{character.name}</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {character.description || 'タップして会話を始めましょう'}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
