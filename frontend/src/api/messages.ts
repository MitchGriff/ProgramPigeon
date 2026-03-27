/**
 * Messaging API functions: send messages and retrieve conversation threads.
 */

import apiClient from './client'
import type { Message, SendMessagePayload } from '@/types/message'

/**
 * Send a direct message to another user.
 */
export async function sendMessage(payload: SendMessagePayload): Promise<Message> {
  const { data } = await apiClient.post<Message>('/messages', payload)
  return data
}

/**
 * Fetch the full message thread between the current user and another user.
 * Also marks incoming unread messages as read.
 *
 * @param otherUserId - The ID of the other participant in the conversation.
 */
export async function getConversation(otherUserId: string): Promise<Message[]> {
  const { data } = await apiClient.get<Message[]>(`/messages/${otherUserId}`)
  return data
}

/**
 * Fetch a list of recent conversations (one message per conversation partner).
 * Used to render the inbox/conversation list.
 */
export async function getRecentConversations(): Promise<Message[]> {
  const { data } = await apiClient.get<Message[]>('/messages')
  return data
}
