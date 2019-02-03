.. _configuration:

Configuration
=========================================

When initializing a session interface, you have a number of optional arguments for configuring your session. 

**domain** (str, optional):
    Optional domain which will be attached to the cookie. Defaults to None.
**expiry** (int, optional):
    Seconds until the session should expire. Defaults to *2592000* (30 days). Setting this to 0 or None will set the session as permanent.
**httponly** (bool, optional):
    Adds the `httponly` flag to the session cookie. Defaults to True.
**cookie_name** (str, optional):
    Name used for the client cookie. Defaults to "session".
**prefix** (str, optional):
    Storage keys will take the format of `prefix+<session_id>`. Specify the prefix here.
**sessioncookie** (bool, optional):
    If enabled the browser will be instructed to delete the cookie when the browser is closed. This is done by omitting the `max-age` and `expires` headers when sending the cookie. The `expiry` configuration option will still be honored on the server side. This is option is disabled by default.
**samesite** (str, optional):
    One of 'strict' or 'lax'. Defaults to None  https://www.owasp.org/index.php/SameSite
**session_name** (str, optional):
    | Name of the session that will be accessible through the request.
    | e.g. If ``session_name`` is ``alt_session``, it should be accessed like that: ``request['alt_session']``
    | e.g. And if ``session_name`` is left to default, it should be accessed like that: ``request['session']``

    .. note::

        If you choose to build your application using more than one session object, make sure that they have different:

            1. ``cookie_name``
            2. ``prefix`` (Only if the two cookies share the same store)
            3. And obviously, different: ``session_name``
**secure** (bool, optional):
    Whether or not the cookie should be secure (HTTP(S) only)
**warn_lock** (bool, optional):
    Set to False to turn off session_dict lock warning (Not recommended)
    Default: True


**Example 1:**

.. code-block:: python

    session_interface = InMemorySessionInterface(
        domain='.example.com', expiry=0,
        httponly=False, cookie_name="cookie", prefix="sessionprefix:",  samesite="strict")

Will result in a session that:

- Will be valid only on *example.com*.
- Will never expire. 
- Will be accessible by Javascript.
- Will be named "cookie" on the client.
- Will be named "sessionprefix:<sid>" in the session store.
- Will prevent the cookie from being sent by the browser to the target site in all cross-site browsing context, even when following a regular link.

**Example 2:**

.. code-block:: python

    session_interface = InMemorySessionInterface(
        domain='.example.com', expiry=3600, sessioncookie=True,
        httponly=True, cookie_name="myapp", prefix="session:")

Will result in a session that:

- Will be valid only on *example.com*.
- Will expire on the server side after 1 hour.
- Will be deleted on the client when the user closes the browser.
- Will *not* be accessible by Javascript.
- Will be named "myapp" on the client.
- Will be named "session:<sid>" in the session store.
