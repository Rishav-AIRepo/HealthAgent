import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { sendChat } from '../services/api'
import { useStore } from '../store'
import Spinner from '../components/Spinner'
import { Send, Bot, User } from 'lucide-react'

export default function ChatPage() {
  const { userId, sessionId, chatMessages, addChatMessage } = useStore()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleSend = async () => {
    const query = input.trim()
    if (!query || loading) return
    setInput('')
    addChatMessage({ role: 'user', content: query })
    setLoading(true)
    try {
      const res = await sendChat(userId, sessionId, query)
      addChatMessage({ role: 'assistant', content: res.answer, disclaimer: res.disclaimer })
    } catch {
      addChatMessage({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col h-[calc(100vh-4rem)]">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Health AI Chat</h1>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-4 bg-gray-50 rounded-xl border border-gray-200 p-4 mb-4">
        {chatMessages.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-10">
            Ask a question about your health records (upload a PDF first).
          </p>
        )}
        {chatMessages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center shrink-0 mt-1">
                <Bot size={14} className="text-primary-600" />
              </div>
            )}
            <div className={`max-w-[75%] text-sm rounded-xl px-4 py-2.5 leading-relaxed
              ${msg.role === 'user'
                ? 'bg-primary-600 text-white rounded-tr-sm'
                : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'}`}
            >
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <div className="prose prose-sm max-w-none
                  prose-headings:font-semibold prose-headings:text-gray-900 prose-headings:mt-3 prose-headings:mb-1
                  prose-p:my-1 prose-p:leading-relaxed
                  prose-ul:my-1 prose-ul:pl-4 prose-ol:my-1 prose-ol:pl-4
                  prose-li:my-0.5
                  prose-strong:font-semibold prose-strong:text-gray-900
                  prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded prose-code:text-xs
                  prose-blockquote:border-l-2 prose-blockquote:border-gray-300 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:text-gray-600
                  prose-hr:my-2">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              )}
              {msg.disclaimer && (
                <p className="text-[10px] text-gray-400 mt-1 border-t border-gray-100 pt-1">{msg.disclaimer}</p>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center shrink-0 mt-1">
                <User size={14} className="text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-2 justify-start">
            <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center">
              <Bot size={14} className="text-primary-600" />
            </div>
            <div className="bg-white border border-gray-200 rounded-xl rounded-tl-sm px-4 py-2.5">
              <Spinner size={16} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your lab results…"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
