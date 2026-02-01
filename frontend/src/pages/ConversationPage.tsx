import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import * as api from '@/lib/api';
import { ArrowLeft, Send, MoreVertical, Volume2, VolumeX, Loader2, ImageIcon, Video, X, Check, Download, Clock } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'character' | 'system';
  content: string;
  content_type: 'text' | 'image';
  image_url?: string;
  expires_at?: string;
  created_at: string;
}

interface Thread {
  id: string;
  character: {
    id: string;
    name: string;
    avatar_url: string | null;
  };
}

// キャラクター画像URLを取得する関数
const getCharacterImageUrl = (avatarUrl: string | null): string => {
  if (avatarUrl) {
    // サーバーの静的ファイルURLの場合はフルURLに変換
    if (avatarUrl.startsWith('/static/')) {
      return `http://localhost:8080${avatarUrl}`;
    }
    return avatarUrl;
  }
  // フォールバック: プレースホルダー画像
  return '/placeholder.png';
};

export function ConversationPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [thread, setThread] = useState<Thread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const [loadingAudioId, setLoadingAudioId] = useState<string | null>(null);
  const [isGeneratingScene, setIsGeneratingScene] = useState(false);
  // メッセージ選択モード
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedMessageIds, setSelectedMessageIds] = useState<Set<string>>(new Set());
  // 無限スクロール用の状態
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // スクロール位置維持用
  const isLoadingMoreRef = useRef(false);
  const prevScrollHeightRef = useRef<number>(0);
  // 初回ロード完了フラグ
  const isInitialLoadRef = useRef(true);

  // Play audio for a message
  const playMessageAudio = async (messageId: string) => {
    if (!threadId) return;
    
    // Stop current audio if playing
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    
    if (playingMessageId === messageId) {
      setPlayingMessageId(null);
      return;
    }
    
    setLoadingAudioId(messageId);
    
    try {
      const audioBlob = await api.getMessageAudio(threadId, messageId);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onplay = () => {
        setPlayingMessageId(messageId);
        setLoadingAudioId(null);
      };
      
      audio.onended = () => {
        setPlayingMessageId(null);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = () => {
        setPlayingMessageId(null);
        setLoadingAudioId(null);
        console.error('Audio playback error');
      };
      
      await audio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
      setLoadingAudioId(null);
      // 音声が利用できない場合は静かに失敗
    }
  };

  // 古いメッセージを読み込む関数
  const loadOlderMessages = useCallback(async () => {
    if (!threadId || !hasMore || isLoadingMore || !nextCursor) return;
    
    setIsLoadingMore(true);
    isLoadingMoreRef.current = true;
    
    // スクロール位置を保存
    if (scrollRef.current) {
      prevScrollHeightRef.current = scrollRef.current.scrollHeight;
    }
    
    try {
      // order=descで次のページを取得（より古いメッセージ）
      const messagesData = await api.getMessages(threadId, 'desc', nextCursor);
      // 取得したメッセージを逆順にして先頭に追加
      const olderMessages = [...messagesData.data].reverse();
      setMessages(prev => [...olderMessages, ...prev]);
      setNextCursor(messagesData.pagination.next_cursor);
      setHasMore(messagesData.pagination.has_more);
    } catch (error) {
      console.error('Failed to load older messages:', error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [threadId, hasMore, isLoadingMore, nextCursor]);

  // 初期データ取得
  useEffect(() => {
    const fetchData = async () => {
      if (!threadId) return;
      try {
        const [threadData, messagesData] = await Promise.all([
          api.getThread(threadId),
          // order=descで最新メッセージから取得
          api.getMessages(threadId, 'desc'),
        ]);
        setThread(threadData.thread);
        // 取得したメッセージを逆順にして表示（古い→新しい順）
        setMessages([...messagesData.data].reverse());
        setNextCursor(messagesData.pagination.next_cursor);
        setHasMore(messagesData.pagination.has_more);
      } catch (error) {
        console.error('Failed to fetch conversation:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [threadId]);

  // スクロールイベントの監視
  useEffect(() => {
    const scrollElement = scrollRef.current;
    if (!scrollElement) return;

    const handleScroll = () => {
      // 上端付近に到達したら読み込み
      if (scrollElement.scrollTop < 100 && hasMore && !isLoadingMore) {
        loadOlderMessages();
      }
    };

    scrollElement.addEventListener('scroll', handleScroll);
    return () => scrollElement.removeEventListener('scroll', handleScroll);
  }, [hasMore, isLoadingMore, loadOlderMessages]);

  // スクロール位置の維持（古いメッセージ読み込み後）
  useEffect(() => {
    if (isLoadingMoreRef.current && scrollRef.current && prevScrollHeightRef.current > 0) {
      const newScrollHeight = scrollRef.current.scrollHeight;
      const scrollDiff = newScrollHeight - prevScrollHeightRef.current;
      scrollRef.current.scrollTop = scrollDiff;
      prevScrollHeightRef.current = 0;
      isLoadingMoreRef.current = false;
    }
  }, [messages]);

  // 最下部へスクロール（初期表示・新規メッセージ送信時）
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  // 初期表示時に最下部へスクロール（メッセージがDOMに反映された後）
  useEffect(() => {
    // 初回ロード完了時のみスクロール
    if (isInitialLoadRef.current && !isLoading && messages.length > 0) {
      // DOM更新後にスクロールするためにrequestAnimationFrameを使用
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          scrollToBottom();
          isInitialLoadRef.current = false;
        });
      });
    }
  }, [isLoading, messages.length, scrollToBottom]);

  const handleSend = async () => {
    if (!threadId || !inputValue.trim() || isSending) return;

    const content = inputValue.trim();
    setInputValue('');
    setIsSending(true);

    // Optimistic update for user message
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      content_type: 'text',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const result = await api.sendMessage(threadId, content);
      // Replace temp message and add AI response
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMessage.id),
        result.user_message,
        result.assistant_message,
      ]);
      // 新規メッセージ送信後は最下部へスクロール
      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove temp message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
      alert('メッセージの送信に失敗しました');
      setInputValue(content);
    } finally {
      setIsSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // メッセージ選択の切り替え
  const toggleMessageSelection = (messageId: string) => {
    setSelectedMessageIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  // 選択モードの開始
  const startSelectMode = () => {
    setIsSelectMode(true);
    setSelectedMessageIds(new Set());
  };

  // 選択モードのキャンセル
  const cancelSelectMode = () => {
    setIsSelectMode(false);
    setSelectedMessageIds(new Set());
  };

  const handleGenerateSceneImage = async () => {
    if (!threadId || isGeneratingScene || selectedMessageIds.size === 0) return;
    
    setIsGeneratingScene(true);
    try {
      const messageIds = Array.from(selectedMessageIds);
      // 画像生成（バックエンドでメッセージとして保存される）
      await api.generateSceneImage(threadId, messageIds);
      // 画像メッセージがチャットに追加されるので、メッセージを再取得
      const messagesData = await api.getMessages(threadId, 'desc');
      setMessages([...messagesData.data].reverse());
      setNextCursor(messagesData.pagination.next_cursor);
      setHasMore(messagesData.pagination.has_more);
      // 選択モードを終了
      setIsSelectMode(false);
      setSelectedMessageIds(new Set());
      // 最下部へスクロール
      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error('Failed to generate scene image:', error);
      alert('シーン画像の生成に失敗しました');
    } finally {
      setIsGeneratingScene(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-8rem)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">会話が見つかりませんでした</p>
        <Button variant="link" onClick={() => navigate('/marketplace')}>
          マーケットに戻る
        </Button>
      </div>
    );
  }

  const characterImageUrl = getCharacterImageUrl(thread.character.avatar_url);

  return (
    <div className="-mx-4 -my-6 relative">
      {/* Background with partner image */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-10"
          style={{ backgroundImage: `url(${characterImageUrl})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-purple-50/80 via-pink-50/60 to-white/90 dark:from-gray-900/90 dark:via-purple-900/30 dark:to-gray-900/95" />
      </div>

      {/* Header - 上部固定 */}
      <div className="fixed top-[3.5rem] left-0 right-0 z-20 flex items-center gap-3 p-4 border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <img
          src={getCharacterImageUrl(thread.character.avatar_url)}
          alt={thread.character.name}
          className="h-10 w-10 rounded-full object-cover bg-gradient-to-br from-purple-100 to-pink-100"
        />
        <div className="flex-1">
          <h2 className="font-semibold">{thread.character.name}</h2>
        </div>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5" />
        </Button>
      </div>

      {/* Messages - スクロール可能エリア */}
      <div className="pt-[4.5rem] pb-[8rem]">
        <div 
          ref={scrollRef} 
          className="h-[calc(100vh-16rem)] overflow-y-auto p-4"
        >
          {/* 上部ローディングインジケーター */}
          {isLoadingMore && (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-purple-600" />
            </div>
          )}
          {/* もっと読み込めることを示す表示 */}
          {hasMore && !isLoadingMore && (
            <div className="flex justify-center py-2">
              <span className="text-xs text-gray-400">↑ 上にスクロールして過去のメッセージを読み込む</span>
            </div>
          )}
          <div className="space-y-4 max-w-2xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="mb-2">会話を始めましょう！</p>
                <p className="text-sm">{thread.character.name}にメッセージを送ってみてください</p>
              </div>
            ) : (
              messages.map((message) => {
                // 画像メッセージの場合
                if (message.content_type === 'image' && message.image_url) {
                  const imageFullUrl = message.image_url.startsWith('/static/')
                    ? `http://localhost:8080${message.image_url}`
                    : message.image_url;
                  const daysLeft = message.expires_at
                    ? Math.max(0, Math.ceil((new Date(message.expires_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
                    : null;

                  return (
                    <div key={message.id} className="flex justify-center my-4">
                      <div className="bg-white/95 dark:bg-gray-800/95 rounded-xl p-3 shadow-lg max-w-[80%]">
                        <p className="text-xs text-gray-500 mb-2 text-center">{message.content}</p>
                        <img
                          src={imageFullUrl}
                          alt="シーン画像"
                          className="rounded-lg max-w-full max-h-[300px] object-contain"
                        />
                        <div className="flex items-center justify-between mt-2 gap-2">
                          {daysLeft !== null && (
                            <span className="text-xs text-gray-400 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              あと{daysLeft}日で削除
                            </span>
                          )}
                          <a
                            href={imageFullUrl}
                            download={`scene_${message.id}.png`}
                            className="text-xs text-purple-600 hover:text-purple-800 flex items-center gap-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Download className="h-3 w-3" />
                            ダウンロード
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                }

                // 通常のテキストメッセージ
                return (
                  <div
                    key={message.id}
                    className={`flex gap-3 items-start ${
                      message.role === 'user' ? 'flex-row-reverse' : ''
                    }`}
                  >
                    {/* 選択モード時のチェックボックス（画像メッセージ以外） */}
                    {isSelectMode && message.content_type !== 'image' && (
                      <div className={`flex items-center ${message.role === 'user' ? 'order-first' : ''}`}>
                        <Checkbox
                          checked={selectedMessageIds.has(message.id)}
                          onCheckedChange={() => toggleMessageSelection(message.id)}
                          className="h-5 w-5 border-2 border-purple-400 data-[state=checked]:bg-purple-600 data-[state=checked]:border-purple-600"
                        />
                      </div>
                    )}
                    {message.role === 'character' && (
                      <img
                        src={getCharacterImageUrl(thread.character.avatar_url)}
                        alt={thread.character.name}
                        className="h-8 w-8 rounded-full object-cover bg-gradient-to-br from-purple-100 to-pink-100 flex-shrink-0"
                      />
                    )}
                    <div
                      className={`max-w-[70%] rounded-2xl px-4 py-2 backdrop-blur-sm cursor-pointer transition-all ${
                        message.role === 'user'
                          ? 'bg-purple-600/95 text-white rounded-tr-sm shadow-md'
                          : 'bg-white/90 dark:bg-gray-800/90 rounded-tl-sm shadow-sm'
                      } ${isSelectMode && selectedMessageIds.has(message.id) ? 'ring-2 ring-purple-500 ring-offset-2' : ''}`}
                      onClick={isSelectMode && message.content_type !== 'image' ? () => toggleMessageSelection(message.id) : undefined}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      {message.role === 'character' && !isSelectMode && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            playMessageAudio(message.id);
                          }}
                          className="mt-1 flex items-center gap-1 text-xs text-gray-500 hover:text-purple-600 transition-colors"
                          disabled={loadingAudioId === message.id}
                        >
                          {loadingAudioId === message.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : playingMessageId === message.id ? (
                            <VolumeX className="h-3 w-3" />
                          ) : (
                            <Volume2 className="h-3 w-3" />
                          )}
                          <span>
                            {loadingAudioId === message.id 
                              ? '読み込み中...' 
                              : playingMessageId === message.id 
                                ? '停止' 
                                : '再生'}
                          </span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
            {isSending && (
              <div className="flex gap-3">
                <img
                  src={getCharacterImageUrl(thread.character.avatar_url)}
                  alt={thread.character.name}
                  className="h-8 w-8 rounded-full object-cover bg-gradient-to-br from-purple-100 to-pink-100 flex-shrink-0"
                />
                <div className="bg-gray-100/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Input - 下部固定（ナビゲーションバーの上） */}
      <div className="fixed bottom-[4rem] left-0 right-0 z-20 border-t bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm">
        {isSelectMode ? (
          /* 選択モード時のUI */
          <div className="max-w-2xl mx-auto p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">
                {selectedMessageIds.size}件のメッセージを選択中
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={cancelSelectMode}
                className="text-xs"
              >
                <X className="h-3 w-3 mr-1" />
                キャンセル
              </Button>
            </div>
            <div className="flex gap-2 justify-center">
              <Button
                variant="default"
                size="sm"
                onClick={handleGenerateSceneImage}
                disabled={isGeneratingScene || selectedMessageIds.size === 0}
                className="text-xs"
              >
                {isGeneratingScene ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <ImageIcon className="h-3 w-3 mr-1" />
                    シーン画像生成
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled
                className="text-xs opacity-50"
              >
                <Video className="h-3 w-3 mr-1" />
                シーン動画生成
              </Button>
            </div>
          </div>
        ) : (
          /* 通常モード時のUI */
          <>
            {/* 生成ボタンエリア */}
            <div className="max-w-2xl mx-auto px-4 pt-2 flex gap-2 justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={startSelectMode}
                disabled={messages.length === 0}
                className="text-xs"
              >
                <Check className="h-3 w-3 mr-1" />
                シーン画像生成
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled
                className="text-xs opacity-50"
              >
                <Video className="h-3 w-3 mr-1" />
                シーン動画生成
              </Button>
            </div>
            {/* メッセージ入力欄 */}
            <div className="max-w-2xl mx-auto p-4 flex gap-2">
              <Input
                ref={inputRef}
                placeholder="メッセージを入力..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isSending}
                className="flex-1"
              />
              <Button
                onClick={handleSend}
                disabled={!inputValue.trim() || isSending}
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </>
        )}
      </div>

    </div>
  );
}
