import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkles, Wand2, RefreshCw, MessageCircle, Volume2, Loader2 } from 'lucide-react';
import * as api from '@/lib/api';
import type { VoiceId } from '@/lib/api';

type ImageStyle = 'anime' | 'realistic' | 'illustration';

const styleOptions: { id: ImageStyle; name: string; description: string }[] = [
  { id: 'anime', name: 'アニメ風', description: '日本のアニメスタイル' },
  { id: 'realistic', name: 'リアル', description: '写実的なスタイル' },
  { id: 'illustration', name: 'イラスト', description: 'デジタルイラスト風' },
];

const voiceOptions: { id: VoiceId; name: string; description: string }[] = [
  { id: 'nova', name: 'Nova', description: '明るい女性' },
  { id: 'shimmer', name: 'Shimmer', description: '柔らかい女性' },
  { id: 'alloy', name: 'Alloy', description: '中性的' },
  { id: 'echo', name: 'Echo', description: '男性的' },
  { id: 'fable', name: 'Fable', description: '英国風' },
  { id: 'onyx', name: 'Onyx', description: '深い男性' },
];

export function PartnerCreatePage() {
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [partnerName, setPartnerName] = useState('');
  const [partnerDescription, setPartnerDescription] = useState('');
  const [selectedStyle, setSelectedStyle] = useState<ImageStyle>('anime');
  const [selectedVoice, setSelectedVoice] = useState<VoiceId>('nova');
  const [faceImageUrl, setFaceImageUrl] = useState<string | null>(null);
  const [fullBodyImageUrl, setFullBodyImageUrl] = useState<string | null>(null);
  const [serverFaceImageUrl, setServerFaceImageUrl] = useState<string | null>(null);
  const [serverFullBodyImageUrl, setServerFullBodyImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playingVoice, setPlayingVoice] = useState<VoiceId | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleGenerateImage = async () => {
    if (!partnerName.trim()) {
      setError('パートナーの名前を入力してください');
      return;
    }

    setIsGenerating(true);
    setError(null);
    
    try {
      const result = await api.generateImage({
        name: partnerName.trim(),
        description: partnerDescription.trim() || undefined,
        style: selectedStyle,
      });
      
      // バックエンドのURLを使用
      setFaceImageUrl(`http://localhost:8002${result.face_image_url}`);
      setFullBodyImageUrl(`http://localhost:8002${result.full_body_image_url}`);
      setServerFaceImageUrl(result.face_image_url);
      setServerFullBodyImageUrl(result.full_body_image_url);
    } catch (err) {
      console.error('Image generation error:', err);
      setError(err instanceof Error ? err.message : '画像生成に失敗しました');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = () => {
    setFaceImageUrl(null);
    setFullBodyImageUrl(null);
    setServerFaceImageUrl(null);
    setServerFullBodyImageUrl(null);
    handleGenerateImage();
  };

  const handleRegisterPartner = async () => {
    if (!partnerName.trim() || !serverFaceImageUrl) {
      setError('名前と画像が必要です');
      return;
    }

    setIsRegistering(true);
    setError(null);

    try {
      const result = await api.createPartner({
        name: partnerName.trim(),
        description: partnerDescription.trim() || undefined,
        image_url: serverFaceImageUrl,
        full_body_image_url: serverFullBodyImageUrl || undefined,
        voice_id: selectedVoice,
      });

      // 会話ページに遷移
      navigate(`/conversation/${result.thread_id}`);
    } catch (err) {
      console.error('Partner registration error:', err);
      setError(err instanceof Error ? err.message : 'パートナー登録に失敗しました');
    } finally {
      setIsRegistering(false);
    }
  };

  const handleVoiceClick = async (voiceId: VoiceId) => {
    // 選択状態を更新
    setSelectedVoice(voiceId);

    // 既に再生中の音声を停止
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    // サンプル音声を再生
    setPlayingVoice(voiceId);
    try {
      const audioBlob = await api.getVoiceSample(voiceId);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setPlayingVoice(null);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = () => {
        setPlayingVoice(null);
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
    } catch (err) {
      console.error('Voice sample error:', err);
      setPlayingVoice(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 mb-4">
          <Sparkles className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold mb-2">パートナー生成</h1>
        <p className="text-gray-600 dark:text-gray-400">
          あなただけのAIパートナーを作成しましょう
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">パートナー情報</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">
              名前 <span className="text-red-500">*</span>
            </label>
            <Input
              placeholder="例: ゆうき、さくら、etc."
              value={partnerName}
              onChange={(e) => setPartnerName(e.target.value)}
              maxLength={20}
              disabled={isGenerating || isRegistering}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              性格・特徴（任意）
            </label>
            <Textarea
              placeholder="例: 明るくて元気、優しくて癒し系、クールで知的、黒髪ロング、青い瞳..."
              value={partnerDescription}
              onChange={(e) => setPartnerDescription(e.target.value)}
              rows={4}
              maxLength={200}
              disabled={isGenerating || isRegistering}
            />
            <p className="text-xs text-gray-500 mt-1">
              {partnerDescription.length}/200文字
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              アートスタイル
            </label>
            <div className="grid grid-cols-3 gap-2">
              {styleOptions.map((style) => (
                <button
                  key={style.id}
                  type="button"
                  onClick={() => setSelectedStyle(style.id)}
                  disabled={isGenerating || isRegistering}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    selectedStyle === style.id
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-purple-300'
                  } ${isGenerating || isRegistering ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="font-medium text-sm">{style.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{style.description}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              <Volume2 className="inline h-4 w-4 mr-1" />
              声の種類（クリックで試聴）
            </label>
            <div className="grid grid-cols-3 gap-2">
              {voiceOptions.map((voice) => (
                <button
                  key={voice.id}
                  type="button"
                  onClick={() => handleVoiceClick(voice.id)}
                  disabled={isGenerating || isRegistering}
                  className={`p-3 rounded-lg border-2 text-center transition-all relative ${
                    selectedVoice === voice.id
                      ? 'border-pink-500 bg-pink-50 dark:bg-pink-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-pink-300'
                  } ${isGenerating || isRegistering ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {playingVoice === voice.id && (
                    <div className="absolute top-1 right-1">
                      <Loader2 className="h-3 w-3 animate-spin text-pink-500" />
                    </div>
                  )}
                  <div className="font-medium text-sm">{voice.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{voice.description}</div>
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">
              ※ カードをクリックすると声のサンプルが再生されます
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {(faceImageUrl || fullBodyImageUrl) && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium">生成された画像</label>
                <button
                  onClick={handleRegenerate}
                  disabled={isGenerating}
                  className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  title="再生成"
                >
                  <RefreshCw className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
                  再生成
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {/* 顔アップ画像 */}
                <div className="space-y-2">
                  <p className="text-xs text-center text-gray-500 font-medium">
                    アイコン・背景用
                  </p>
                  <div className="relative">
                    {faceImageUrl ? (
                      <img
                        src={faceImageUrl}
                        alt={`${partnerName} - 顔アップ`}
                        className="w-full aspect-square object-cover rounded-xl shadow-lg"
                      />
                    ) : (
                      <div className="w-full aspect-square bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
                        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                      </div>
                    )}
                  </div>
                </div>
                {/* 立ち絵画像 */}
                <div className="space-y-2">
                  <p className="text-xs text-center text-gray-500 font-medium">
                    立ち絵
                  </p>
                  <div className="relative">
                    {fullBodyImageUrl ? (
                      <img
                        src={fullBodyImageUrl}
                        alt={`${partnerName} - 立ち絵`}
                        className="w-full aspect-square object-cover rounded-xl shadow-lg"
                      />
                    ) : (
                      <div className="w-full aspect-square bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
                        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="pt-4 space-y-3">
            {!faceImageUrl ? (
              <Button
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                size="lg"
                onClick={handleGenerateImage}
                disabled={isGenerating || !partnerName.trim()}
              >
                {isGenerating ? (
                  <>
                    <Wand2 className="h-5 w-5 mr-2 animate-spin" />
                    生成中...（1分ほどかかります）
                  </>
                ) : (
                  <>
                    <Wand2 className="h-5 w-5 mr-2" />
                    パートナー画像を生成
                  </>
                )}
              </Button>
            ) : (
              <>
                <Button
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
                  size="lg"
                  onClick={handleRegisterPartner}
                  disabled={isRegistering || isGenerating}
                >
                  {isRegistering ? (
                    <>
                      <MessageCircle className="h-5 w-5 mr-2 animate-pulse" />
                      登録中...
                    </>
                  ) : (
                    <>
                      <MessageCircle className="h-5 w-5 mr-2" />
                      このパートナーで会話を始める
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleRegenerate}
                  disabled={isGenerating || isRegistering}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isGenerating ? 'animate-spin' : ''}`} />
                  別の画像を生成
                </Button>
              </>
            )}
          </div>

          <p className="text-xs text-center text-gray-500">
            ※ 顔アップと立ち絵の2種類を生成するため、1分ほどかかる場合があります
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
