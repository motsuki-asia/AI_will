import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import * as api from '@/lib/api';
import { ArrowLeft, Send, MoreVertical, Volume2, VolumeX, Loader2 } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'character';
  content: string;
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
      return `http://localhost:8000${avatarUrl}`;
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
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

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

  useEffect(() => {
    const fetchData = async () => {
      if (!threadId) return;
      try {
        const [threadData, messagesData] = await Promise.all([
          api.getThread(threadId),
          api.getMessages(threadId, 'asc'),
        ]);
        setThread(threadData.thread);
        setMessages(messagesData.data);
      } catch (error) {
        console.error('Failed to fetch conversation:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [threadId]);

  useEffect(() => {
    // Scroll to bottom when messages change
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
    <div className="flex flex-col h-[calc(100vh-8rem)] -mx-4 -my-6 relative">
      {/* Background with partner image */}
      <div className="absolute inset-0 overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-10"
          style={{ backgroundImage: `url(${characterImageUrl})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-purple-50/80 via-pink-50/60 to-white/90 dark:from-gray-900/90 dark:via-purple-900/30 dark:to-gray-900/95" />
      </div>

      {/* Header */}
      <div className="relative flex items-center gap-3 p-4 border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
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

      {/* Messages */}
      <ScrollArea ref={scrollRef} className="relative flex-1 p-4">
        <div className="space-y-4 max-w-2xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p className="mb-2">会話を始めましょう！</p>
              <p className="text-sm">{thread.character.name}にメッセージを送ってみてください</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                {message.role === 'character' && (
                  <img
                    src={getCharacterImageUrl(thread.character.avatar_url)}
                    alt={thread.character.name}
                    className="h-8 w-8 rounded-full object-cover bg-gradient-to-br from-purple-100 to-pink-100 flex-shrink-0"
                  />
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2 backdrop-blur-sm ${
                    message.role === 'user'
                      ? 'bg-purple-600/95 text-white rounded-tr-sm shadow-md'
                      : 'bg-white/90 dark:bg-gray-800/90 rounded-tl-sm shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.role === 'character' && (
                    <button
                      onClick={() => playMessageAudio(message.id)}
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
            ))
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
      </ScrollArea>

      {/* Input */}
      <div className="relative p-4 border-t bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <div className="max-w-2xl mx-auto flex gap-2">
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
      </div>
    </div>
  );
}
