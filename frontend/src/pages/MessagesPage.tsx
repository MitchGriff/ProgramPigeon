/**
 * MessagesPage: shows a conversation thread between the current user and another user.
 * If no `userId` param is given, shows the inbox (list of recent conversations).
 */

import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getConversation, getRecentConversations, sendMessage } from '@/api/messages'
import { useAuth } from '@/context/AuthContext'
import type { Message } from '@/types/message'
import styles from './MessagesPage.module.css'

export default function MessagesPage() {
  const { userId } = useParams<{ userId?: string }>()
  const { user } = useAuth()

  const [messages, setMessages] = useState<Message[]>([])
  const [inbox, setInbox] = useState<Message[]>([])
  const [content, setContent] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Load conversation or inbox
  useEffect(() => {
    async function load() {
      setLoading(true)
      if (userId) {
        const data = await getConversation(userId)
        setMessages(data)
      } else {
        const data = await getRecentConversations()
        setInbox(data)
      }
      setLoading(false)
    }
    load()
  }, [userId])

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!content.trim() || !userId) return
    setSending(true)
    try {
      const message = await sendMessage({ recipient_id: userId, content: content.trim() })
      setMessages((prev) => [...prev, message])
      setContent('')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <div className={styles.loading}>Loading...</div>

  // Inbox view — no userId in URL
  if (!userId) {
    return (
      <div className={styles.page}>
        <h1 className={styles.pageTitle}>Messages</h1>
        {inbox.length === 0 ? (
          <p className={styles.empty}>No conversations yet.</p>
        ) : (
          <ul className={styles.inboxList}>
            {inbox.map((msg) => {
              const otherId =
                msg.sender_id === user?.id ? msg.recipient_id : msg.sender_id
              return (
                <li key={msg.id}>
                  <Link to={`/messages/${otherId}`} className={styles.inboxItem}>
                    <div className={styles.inboxMeta}>
                      <span className={styles.inboxId}>{otherId.slice(0, 8)}...</span>
                      <span className={styles.inboxTime}>
                        {new Date(msg.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className={styles.inboxPreview}>{msg.content}</p>
                    {!msg.read_at && msg.recipient_id === user?.id && (
                      <span className={styles.unreadDot} />
                    )}
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    )
  }

  // Conversation thread view
  return (
    <div className={styles.thread}>
      <div className={styles.threadHeader}>
        <Link to="/messages" className={styles.back}>
          ← Back
        </Link>
        <span className={styles.threadTitle}>Conversation</span>
      </div>

      <div className={styles.messageList}>
        {messages.length === 0 && (
          <p className={styles.empty}>No messages yet. Say hello!</p>
        )}
        {messages.map((msg) => {
          const isOwn = msg.sender_id === user?.id
          return (
            <div
              key={msg.id}
              className={`${styles.bubble} ${isOwn ? styles.bubbleOwn : styles.bubbleOther}`}
            >
              <p className={styles.bubbleContent}>{msg.content}</p>
              <span className={styles.bubbleTime}>
                {new Date(msg.created_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className={styles.composeBar}>
        <input
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Type a message..."
          className={styles.composeInput}
          disabled={sending}
        />
        <button type="submit" className={styles.sendButton} disabled={sending || !content.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
