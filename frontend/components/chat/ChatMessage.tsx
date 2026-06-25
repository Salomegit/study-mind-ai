// components/chat/ChatMessage.tsx

import { BookOpen } from 'lucide-react'
import type { Message } from '@/hooks/useAsk'

interface Props {
  message: Message
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-sm font-bold
          ${isUser
            ? 'bg-primary text-white'
            : 'bg-secondary/20 text-secondary'
          }`}
      >
        {isUser ? 'You' : '✦'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] space-y-3 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? 'bg-primary text-white rounded-tr-sm'
              : 'bg-white border border-border text-text rounded-tl-sm shadow-sm'
            }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="w-full space-y-2">
            <div className="flex items-center gap-1.5 text-xs text-text-muted font-medium">
              <BookOpen size={12} />
              <span>References</span>
            </div>
            {message.sources.map((src) => (
              <div
                key={src.chunk_id}
                className="bg-white border border-border rounded-xl p-3 hover:border-primary/40 transition-colors"
              >
                {src.metadata?.filename && (
                  <p className="text-xs font-semibold text-accent mb-1">
                    📄 {src.metadata.filename.split('/').pop() || src.metadata.filename}
                    {src.metadata.page_number && (
                      <span className="text-text-muted font-normal">
                        {' · '}Page {src.metadata.page_number}
                      </span>
                    )}
                  </p>
                )}
                <p className="text-xs text-text-muted leading-relaxed line-clamp-3">
                  {src.text_preview}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-text-muted px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}