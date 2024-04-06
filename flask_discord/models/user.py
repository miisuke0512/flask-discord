from .. import configs

from .guild import Guild
from .member import GuildMember
from .. import exceptions
from .base import DiscordModelsBase
from .connections import UserConnection

from flask import current_app, session


class User(DiscordModelsBase):
    """Class representing Discord User.


    Operations
    ----------
    x == y
        Checks if two user's are the same.
    x != y
        Checks if two user's are not the same.
    str(x)
        Returns the user's name with discriminator.

    Attributes
    ----------
    id : int
        The discord ID of the user.
    username : str
        The discord username of the user.
    discriminator : str
        4 length string representing discord tag of the user.
    is_migrated : bool
        A boolean representing if the user has migrated to the new username system.
    global_name : str
        The global name of the user.
    avatar_hash : str
        Hash of users avatar.
    bot : bool
        A boolean representing whether the user belongs to an OAuth2 application.
    mfa_enabled : bool
        A boolean representing whether the user has two factor enabled on their account.
    locale : str
        The user's chosen language option.
    verified : bool
        A boolean representing whether the email on this account has been verified.
    email : str
        User's email ID.
    flags : int
        An integer representing the
        `user flags <https://discord.com/developers/docs/resources/user#user-object-user-flags>`_.
    premium_type : int
        An integer representing the
        `type of nitro subscription <https://discord.com/developers/docs/resources/user#user-object-premium-types>`_.
    connections : list
        A list of :py:class:`flask_discord.UserConnection` instances. These are cached and this list might be empty.

    """

    ROUTE = "/users/@me"

    def __init__(self, payload):
        super().__init__(payload)
        self.id = int(self._payload["id"])
        self.username = self._payload["username"]
        self.discriminator = self._payload["discriminator"]
        self.avatar_hash = self._payload.get("avatar", self.discriminator)
        self.bot = self._payload.get("bot", False)
        self.mfa_enabled = self._payload.get("mfa_enabled")
        self.locale = self._payload.get("locale")
        self.verified = self._payload.get("verified")
        self.email = self._payload.get("email")
        self.flags = self._payload.get("flags")
        self.premium_type = self._payload.get("premium_type")
        self.is_migrated = self._payload.get("discriminator") == "0"
        self.global_name = (self._payload.get("global_name", None)
                            or self._payload.get("username")) if self.is_migrated else None

        # Few properties which are intended to be cached.
        self._guilds = None         # Mapping of guild ID to flask_discord.models.Guild(...).
        self._guild_members: dict[int, GuildMember] = dict()  # Mapping of guild ID to flask_discord.models.GuildMember(...).
        self.connections = None     # List of flask_discord.models.UserConnection(...).

    @property
    def guilds(self):
        """A cached mapping of user's guild ID to :py:class:`flask_discord.Guild`. The guilds are cached when the first
        API call for guilds is requested so it might be an empty dict.

        """
        try:
            return list(self._guilds.values())
        except AttributeError:
            pass

    @guilds.setter
    def guilds(self, value):
        self._guilds = value

    @property
    def guild_members(self):
        """A property returning dict of :py:class:`flask_discord.GuildMember` instances of the user."""
        try:
            return self._guild_members
        except AttributeError:
            pass

    @guild_members.setter
    def guild_members(self, value):
        self._guild_members[value.guild_id] = value

    def __str__(self):
        if self.is_migrated and self.global_name:
            return f"{self.global_name} (@{self.name})"
        elif self.is_migrated:
            return f"@{self.name}"
        else:
            return f"{self.name}#{self.discriminator}"

    def __eq__(self, user):
        return isinstance(user, User) and user.id == self.id

    def __ne__(self, user):
        return not self.__eq__(user)

    @property
    def name(self):
        """An alias to the username attribute."""
        return self.username

    @property
    def avatar_url(self):
        """A property returning direct URL to user's avatar."""
        if not self.avatar_hash:
            return self.default_avatar_url
        image_format = configs.DISCORD_ANIMATED_IMAGE_FORMAT \
            if self.is_avatar_animated else configs.DISCORD_IMAGE_FORMAT
        return configs.DISCORD_USER_AVATAR_BASE_URL.format(
            user_id=self.id, avatar_hash=self.avatar_hash, format=image_format)

    @property
    def default_avatar_url(self):
        """A property which returns the default avatar URL as when user doesn't has any avatar set."""
        return configs.DISCORD_DEFAULT_USER_AVATAR_BASE_URL.format((self.id >> 22) % 6)

    @property
    def is_avatar_animated(self):
        """A boolean representing if avatar of user is animated. Meaning user has GIF avatar."""
        try:
            return self.avatar_hash.startswith("a_")
        except AttributeError:
            return False

    @classmethod
    def fetch_from_api(cls, guilds=False, connections=False, members=False):
        """A class method which returns an instance of this model by implicitly making an
        API call to Discord. The user returned from API will always be cached and update in internal cache.

        Parameters
        ----------
        guilds : bool
            A boolean indicating if user's guilds should be cached or not. Defaults to ``False``. If chose to not
            cache, user's guilds can always be obtained from :py:func:`flask_discord.Guilds.fetch_from_api()`.
        connections : bool
            A boolean indicating if user's connections should be cached or not. Defaults to ``False``. If chose to not
            cache, user's connections can always be obtained from :py:func:`flask_discord.Connections.fetch_from_api()`.
        members : bool
            A boolean indicating if user's guild members should be cached or not. Defaults to ``False``. If chose to not
            cache, user's guild member objects can always be obtained from :py:func:`flask_discord.GuildMember.fetch_from_api()`.

        Returns
        -------
        cls
            An instance of this model itself.
        [cls, ...]
            List of instances of this model when many of these models exist."""
        self = super().fetch_from_api()
        current_app.discord.users_cache.update({self.id: self})
        session["DISCORD_USER_ID"] = self.id

        if guilds:
            self.fetch_guilds()
        if connections:
            self.fetch_connections()
        if guilds and members:
            for guild in self.guilds:
                self.fetch_guild_members(guild.id)

        return self

    @classmethod
    def get_from_cache(cls):
        """A class method which returns an instance of this model if it exists in internal cache.

        Returns
        -------
        flask_discord.User
            An user instance if it exists in internal cache.
        None
            If the current doesn't exists in internal cache.

        """
        return current_app.discord.users_cache.get(current_app.discord.user_id)

    def add_to_guild(self, guild_id) -> dict:
        """Method to add user to the guild, provided OAuth2 session has already been created with ``guilds.join`` scope.

        Parameters
        ----------
        guild_id : int
            The ID of the guild you want this user to be added.
            
        Returns
        -------
        dict
            A dict of guild member object. Returns an empty dict if user is already present in the guild.

        Raises
        ------
        flask_discord.Unauthorized
            Raises :py:class:`flask_discord.Unauthorized` if current user is not authorized.

        """
        try:
            data = {"access_token": current_app.discord.get_authorization_token()["access_token"]}
        except KeyError:
            raise exceptions.Unauthorized
        return self._bot_request(f"/guilds/{guild_id}/members/{self.id}", method="PUT", json=data) or dict()

    def fetch_guilds(self) -> list:
        """A method which makes an API call to Discord to get user's guilds. It prepares the internal guilds cache
        and returns list of all guilds the user is member of.

        Returns
        -------
        list
            List of :py:class:`flask_discord.Guilds` instances.

        """
        self._guilds = {guild.id: guild for guild in Guild.fetch_from_api(cache=False)}
        return self.guilds

    def fetch_connections(self) -> list:
        """A method which makes an API call to Discord to get user's connections. It prepares the internal connection
        cache and returns list of all connection instances.

        Returns
        -------
        list
            A list of :py:class:`flask_discord.UserConnection` instances.

        """
        self.connections = UserConnection.fetch_from_api(cache=False)
        return self.connections

    def fetch_guild_member(self, guild_id) -> GuildMember:
        """A method which makes an API call to Discord to get user's guild member.
        It returns the guild member object for the guild the user is member of.

        Parameters
        ----------
        guild_id : int
            The ID of the guild you want to get the member from.

        Returns
        -------
        flask_discord.GuildMember
            An instance of :py:class:`flask_discord.GuildMember` for given guild_id.

        """
        member = GuildMember.fetch_from_api(guild_id, cache=False)
        self.guild_members = member
        return member

    def fetch_guild_members(self) -> dict[int, GuildMember]:
        """A method which makes an API call to Discord to get user's guild members. It prepares the internal guild
        members cache and returns list of all guild member object for all guilds the user is member of.

        Returns
        -------
        list
            List of :py:class:`flask_discord.GuildMember` instances.

        """
        for guild in self.guilds:
            self.guild_members = GuildMember.fetch_from_api(guild.id, cache=False)
        return self.guild_members


class Bot(User):
    """Class representing the client user itself."""
    # TODO: What is this?
