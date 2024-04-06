class Integration(object):
    """"Class representing discord server integrations.

    Attributes
    ----------
    id : int
        Integration ID.
    name : str
        Name of integration.
    type : str
        Integration type (twitch, youtube, etc).
    enabled : bool
        A boolean representing if this integration is enabled.
    syncing : bool
        A boolean representing if this integration is syncing.
    role_id : int
        ID that this integration uses for subscribers.
    expire_behaviour : int
        An integer representing the behaviour of expiring subscribers.
    expire_grace_period : int
        An integer representing the grace period before expiring subscribers.
    account : dict
        A dictionary representing raw
        `account <https://discord.com/developers/docs/resources/guild#integration-account-object>`_ object.
    synced_at : ISO8601 timestamp
        Representing when this integration was last synced.
    enable_emoticons : bool
        A boolean representing if emoticons should be synced for this integration (twitch only currently)
    subscriber_count : int
        Number of subscribers.
    revoked : bool
        A boolean representing if this integration is revoked.
    application : dict
        A dictionary representing raw
        `application <https://discord.com/developers/docs/resources/application>`_ object.
    scopes : str
        The bot's OAuth2 scopes.

    """

    def __init__(self, payload):
        self._payload = payload
        self.id = int(self._payload.get("id", 0))
        self.name = self._payload.get("name")
        self.type = self._payload.get("type")
        self.enabled = self._payload.get("enabled")
        self.syncing = self._payload.get("syncing")
        self.role_id = int(self._payload.get("role_id", 0))
        self.expire_behaviour = self._payload.get("expire_behaviour")
        self.expire_grace_period = self._payload.get("expire_grace_period")
        # self.user = User(self._payload.get("user", dict()))
        self.account = self._payload.get("account")
        self.synced_at = self._payload.get("synced_at")
        self.enable_emoticons = self._payload.get("enable_emoticons", False)
        self.subscriber_count = self._payload.get("subscriber_count", None)
        self.revoked = self._payload.get("revoked", False)
        self.application = self._payload.get("application")
        self.scopes = self._payload.get("scopes")

