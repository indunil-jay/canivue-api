from app.features.messaging.domain.enums.message_sender import MessageSender


def other_side(side: MessageSender) -> MessageSender:
    return MessageSender.VET if side == MessageSender.OWNER else MessageSender.OWNER
