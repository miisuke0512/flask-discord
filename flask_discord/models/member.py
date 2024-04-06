from .base import DiscordModelsBase
from flask import current_app

from .. import types
from .. import configs


class GuildMember(DiscordModelsBase):
    """Class representing discord Guild member objuect of the user.

    Operations
    ----------
    x == y
        Checks if two guild members's are the same.
    x != y
        Checks if two guild members's are not the same.
    str(x)
        Returns the guild members's name.

    Attributes
    ----------
    user : dict
        User object of the guild member.
    nick : str
        Nickname of the guild member.
    avatar_hash : str
        Hash of guild member's avatar.
    roles : list
        List of role object ids.
    joined_at : str
        ISO8601 timestamp when the user joined the guild.
    premium_since : str
        ISO8601 timestamp when the user started boosting the guild.
    deaf : bool
        Boolean determining if the user is deafened in voice channels.
    mute : bool
        Boolean determining if the user is muted in voice channels.
    flags : int
        Guild member flags represented as a bit set, defaults to 0.
    pending : bool
        Boolean determining if the user has not yet passed the guild's Membership Screening requirements.
    permissions : str
        Total permissions of the member in the channel, including overwrites, returned when in the interaction object.
    communication_disabled_until : str
        ISO8601 timestamp when the timeout will expire and the user will be able to communicate in the guild again.
    guild_id : int
        ID of the guild to which this member belongs.

    """
    MANY = False
    ROUTE = "/users/@me/guilds/{guild_id}/member"

    def __init__(self, payload, guild_id):
        super().__init__(payload, guild_id=guild_id)
        self.user = self._payload.get("user")
        self.nick = self._payload.get("nick", None)
        self.avatar_hash = self._payload.get("avatar", None)
        self.roles = self._payload.get("roles")
        self.joined_at = self._payload.get("joined_at", None)
        self.premium_since = self._payload.get("premium_since", None)
        self.deaf = self._payload.get("deaf")
        self.mute = self._payload.get("mute")
        self.flags = self._payload.get("flags")
        self.pending = self._payload.get("pending", False)
        self.permissions = self._payload.get("permissions", 0)
        self.communication_disabled_until = self._payload.get("communication_disabled_until", None)
        self.guild_id = guild_id
        self.id = int(self.user.get("id"))

    @staticmethod
    def __get_permissions(permissions_value):
        if permissions_value is None:
            return
        return types.Permissions(int(permissions_value))

    def __str__(self):
        return self.nick or self.user.get("global_name") or self.user.get("username")

    def __eq__(self, member):
        return isinstance(member, GuildMember) and member.id == self.id

    def __ne__(self, member):
        return not self.__eq__(member)

    @property
    def icon_url(self):
        """A property returning direct URL to the members's guild avatar. Returns None if member has no avatar set."""
        if not self.avatar_hash:
            return
        image_format = configs.DISCORD_ANIMATED_IMAGE_FORMAT \
            if self.is_avatar_animated else configs.DISCORD_IMAGE_FORMAT
        return configs.DISCORD_GUILD_MEMBER_AVATAR_BASE_URL.format(
            guild_id=self._guild_id, user_id=self.id, avatar_hash=self.avatar_hash, format=image_format)

    @property
    def is_avatar_animated(self):
        """A boolean representing if avatar of user is animated. Meaning user has GIF avatar."""
        try:
            return self.avatar_hash.startswith("a_")
        except AttributeError:
            return False

    @classmethod
    def fetch_from_api(cls, guild_id=0, cache=True):
        """A class method which returns an instance or list of instances of this model by implicitly making an API
        call to Discord. If an instance of :py:class:`flask_discord.User` exists in the users internal cache who
        belongs to these guild members then, the cached property :py:attr:`flask_discord.User.guild_members` is updated.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        cache : bool
            Determines if the :py:attr:`flask_discord.User.guild_members` cache should be updated with the new member.

        Returns
        -------
        list[flask_discord.GuildMember, ...]
            List of instances of :py:class:`flask_discord.GuildMember` to which this user belongs.

        """
        member = super().fetch_from_api(guild_id=guild_id)
        if cache:
            user = current_app.discord.users_cache.get(current_app.discord.user_id)
            try:
                user.guild_members = member
            except AttributeError:
                pass
        return member
