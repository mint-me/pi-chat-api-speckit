# Data Model: LLM Chat API

## User

Represents a registered account.

Fields:

- `id`: UUID primary key.
- `email`: normalized email, unique, indexed.
- `password_hash`: Argon2 hash, never returned.
- `created_at`: timezone-aware creation timestamp.

Relationships:

- One user owns many conversations.
- Deleting a user cascades to conversations and messages.

Validation:

- Email must be syntactically valid and normalized to lowercase.
- Password must meet minimum length at request validation.

## Conversation

Represents one chat thread owned by a user.

Fields:

- `id`: UUID primary key.
- `user_id`: foreign key to `users.id` with cascade delete.
- `title`: short display title derived from first user message.
- `created_at`: timezone-aware creation timestamp.
- `updated_at`: timezone-aware timestamp used for newest-first listing.

Relationships:

- Belongs to exactly one user.
- Contains many messages.

Indexes:

- `(user_id, updated_at DESC)` for authenticated history listing.

## Message

Represents one user or assistant message in a conversation.

Fields:

- `id`: UUID primary key.
- `conversation_id`: foreign key to `conversations.id` with cascade delete.
- `role`: `user` or `assistant`.
- `content`: message body.
- `provider_metadata`: nullable JSON for provider/model details.
- `created_at`: timezone-aware creation timestamp.

Relationships:

- Belongs to exactly one conversation.
- User ownership is derived through `conversation.user_id`; no duplicated
  `user_id` belongs on messages.

Constraints and indexes:

- Check constraint restricts `role` to `user` or `assistant`.
- `(conversation_id, created_at)` supports ordered transcript loading.

## LLM Provider

Runtime interface rather than persisted entity.

Fields/attributes:

- `name`: provider identifier such as `mock` or `openrouter`.
- `model`: model identifier used for metadata and logs.
- `stream(messages)`: async iterator yielding text chunks.

State transitions:

1. User message is persisted before stream starts.
2. Provider chunks are streamed to the client.
3. Assistant message is persisted only after stream success.
4. Provider failure emits an SSE error event and leaves no completed assistant
   message.
