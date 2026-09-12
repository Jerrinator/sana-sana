from functools import wraps

from flask import redirect, request, session, url_for


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_user"):
            return redirect(url_for("auth.login"))
        if session.get("admin_profile", {}).get("must_change_password") and request.endpoint != "auth.change_password":
            return redirect(url_for("auth.change_password"))
        return view_func(*args, **kwargs)

    return wrapped_view
