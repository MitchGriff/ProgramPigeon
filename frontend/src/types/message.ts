/** A direct message between a coach and a client. */
export interface Message {
  id: string
  sender_id: string
  recipient_id: string
  content: string
  created_at: string
  read_at: string | null
}

/** Request body for POST /api/v1/messages */
export interface SendMessagePayload {
  recipient_id: string
  content: string
}
