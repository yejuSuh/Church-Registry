class Session:
    """Global singleton holding the currently logged-in user's identity and role."""

    username     = ""
    name         = ""
    baptism_name = ""
    user_level   = ""

session = Session()
