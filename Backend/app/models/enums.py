import enum


class RequestStatus(str, enum.Enum):
    OPEN = "open"
    MATCHING = "matching"
    MATCHED = "matched"
    PROVIDER_RESPONDED = "provider_responded"
    CONNECTED = "connected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    VIEWED = "viewed"
    INTERESTED = "interested"
    DECLINED = "declined"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


class ConnectionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationType(str, enum.Enum):
    NEW_MATCH = "new_match"
    PROVIDER_RESPONSE = "provider_response"
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_ACCEPTED = "connection_accepted"
    REVIEW_REMINDER = "review_reminder"
    REQUEST_COMPLETED = "request_completed"
    SYSTEM = "system"
