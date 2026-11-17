"""Auth0 for the JSON API, following the Identity and Access Management course.

The browser logs in with the Auth0 SPA SDK and sends the access token in
`Authorization: Bearer <token>`. Flask only verifies it:

AuthError                -> error with its HTTP status code
get_token_auth_header    -> the token from the Authorization header
verify_decode_jwt        -> RS256 signature with Auth0's public keys,
                            plus expiry, audience and issuer
check_permissions        -> 403 when the permission is missing
requires_auth            -> decorator that chains the three checks
optional_payload         -> the payload if there is a token, None otherwise
"""

from .decorators import check_permissions, get_token_auth_header, optional_payload, requires_auth
from .errors import AuthError
from .tokens import verify_decode_jwt

__all__ = [
    "AuthError",
    "check_permissions",
    "get_token_auth_header",
    "optional_payload",
    "requires_auth",
    "verify_decode_jwt",
]
