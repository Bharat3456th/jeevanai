class PermissionEngine:
    """Maps a stored permission value to a decision. Anything unknown fails closed (blocked)."""

    def decide(self, permission: str):
        permission = (permission or "").upper()
        if permission == "ALLOW":
            return {"status": "allowed", "message": "Action is allowed."}
        if permission == "ASK":
            return {"status": "approval_required", "message": "User approval is required."}
        return {"status": "blocked", "message": "This action is blocked by policy."}
