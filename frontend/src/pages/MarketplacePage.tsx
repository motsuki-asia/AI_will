import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import * as api from '@/lib/api';
import { Sparkles, Users, TrendingUp, Star, Clock } from 'lucide-react';

interface Pack {
  id: string;
  pack_type: 'persona' | 'scenario';
  name: string;
  description: string;
  thumbnail_url: string;
  price: number;
  is_free: boolean;
  creator: {
    id: string;
    display_name: string;
  };
  created_at?: string;
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
  const [packs, setPacks] = useState<Pack[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortOption>('trend');
  const [category, setCategory] = useState<CategoryOption>('all');

  useEffect(() => {
    const fetchPacks = async () => {
      try {
        const data = await api.getPacks();
        let sortedPacks = [...data.data];
        
        // Apply sort
        if (sortBy === 'new') {
          sortedPacks.sort((a, b) => 
            new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
          );
        } else if (sortBy === 'recommend') {
          // For MVP, shuffle for "recommend"
          sortedPacks.sort(() => Math.random() - 0.5);
        }
        // 'trend' uses default order from API
        
        setPacks(sortedPacks);
      } catch (error) {
        console.error('Failed to fetch packs:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPacks();
  }, [sortBy, category]);

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

      {/* Pack Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      ) : packs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          パックが見つかりませんでした
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {packs.map((pack) => (
            <Link key={pack.id} to={`/marketplace/${pack.id}`}>
              <Card className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer h-full">
                <div className="aspect-video bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 flex items-center justify-center relative overflow-hidden">
                  <img
                    src={pack.thumbnail_url.startsWith('/static/') 
                      ? `http://localhost:8000${pack.thumbnail_url}` 
                      : pack.thumbnail_url}
                    alt={pack.name}
                    className="w-32 h-32 object-cover rounded-lg"
                  />
                  <div className="absolute top-2 right-2">
                    {pack.pack_type === 'persona' ? (
                      <Users className="h-5 w-5 text-purple-500 bg-white/80 rounded-full p-1" />
                    ) : (
                      <Sparkles className="h-5 w-5 text-pink-500 bg-white/80 rounded-full p-1" />
                    )}
                  </div>
                </div>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        pack.pack_type === 'persona'
                          ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                          : 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300'
                      }`}
                    >
                      {pack.pack_type === 'persona' ? 'ペルソナ' : 'シナリオ'}
                    </span>
                    <span className="text-sm font-semibold text-green-600">
                      {pack.is_free ? '無料' : `¥${pack.price}`}
                    </span>
                  </div>
                  <h3 className="font-semibold text-lg mb-1 line-clamp-1">{pack.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {pack.description}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                    by {pack.creator.display_name}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
