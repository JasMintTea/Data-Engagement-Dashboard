from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
from flask_jwt_extended import (
    jwt_required,
    current_user,
    unset_jwt_cookies,
    set_access_cookies,
    create_access_token,
)
from App.database import db
from App.models import User
from datetime import datetime, timedelta
import secrets

auth_views = Blueprint("auth_views", __name__, template_folder="../templates")


# -------------------- Page Routes --------------------


@auth_views.route("/identify", methods=["GET"])
@jwt_required()
def identify_page():
    return render_template(
        "message.html",
        title="Identify",
        message=f"You are logged in as {current_user.firstname} {current_user.lastname} ({current_user.email}) - Role: {current_user.role}",
    )


@auth_views.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            user = User.query.filter_by(email=email).first()
        except Exception as e:
            flash(
                "Database error — the app may not be initialised yet. Contact the administrator.",
                "danger",
            )
            return render_template("login.html")
        if not user:
            flash("User not found", "danger")
            return redirect(url_for("auth_views.login"))

        if not user.check_password(password):
            flash("Invalid password", "danger")
            return redirect(url_for("auth_views.login"))

        if not user.is_active:
            flash("Account deactivated", "danger")
            return redirect(url_for("auth_views.login"))

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.add(user)
        db.session.commit()

        # Create JWT token
        token = create_access_token(identity=str(user.id))

        # CHECK PASSWORD RESET FIRST - before creating response
        if user.must_change_password:
            session["reset_user_id"] = user.id
            flash("You must reset your password before continuing", "warning")
            # CHANGED: redirect to change_password (not reset_password)
            response = redirect(url_for("auth_views.change_password"))
            set_access_cookies(response, token)
            return response

        # If no reset needed, proceed to dashboard
        if user.role == "admin":
            response = redirect(url_for("admin_views.dashboard"))
        elif user.role == "hr":
            response = redirect(url_for("hr_views.dashboard"))
        elif user.role == "scorer":
            response = redirect(url_for("scorer_views.dashboard"))
        elif user.role == "pulse_leader":
            response = redirect(url_for("pulse.dashboard"))
        else:
            response = redirect(url_for("index_views.index_page"))

        set_access_cookies(response, token)
        flash("Login successful!", "success")
        return response

    return render_template("login.html")


# ========== RENAMED: was reset_password, now change_password ==========
@auth_views.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "reset_user_id" not in session:
        flash("No password reset required", "danger")
        return redirect(url_for("auth_views.login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("New passwords do not match", "danger")
            return redirect(url_for("auth_views.change_password"))

        user = User.query.get(session["reset_user_id"])

        if not user or not user.check_password(current_password):
            flash("Invalid current password", "danger")
            return redirect(url_for("auth_views.change_password"))

        user.set_password(new_password)
        user.must_change_password = False
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        session.pop("reset_user_id")

        session["user_id"] = user.id
        session["user_role"] = user.role
        session["institution_id"] = user.institution_id

        if user.role == "admin":
            response = redirect(url_for("admin_views.dashboard"))
        elif user.role == "hr":
            response = redirect(url_for("hr_views.dashboard"))
        else:
            response = redirect(url_for("scorer_views.dashboard"))

        set_access_cookies(response, token)
        flash("Password reset successful!", "success")
        return response

    # NEW TEMPLATE NAME (was reset_password.html, now change_password.html)
    return render_template("change_password.html")


# ========== Forgot password (email entry) ==========
@auth_views.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            reset_link = url_for("auth_views.reset_password", token=token, _external=True)
            print(f"Reset link for {email}: {reset_link}")  # For demo; send email in production
            flash("A password reset link has been sent to your email (check console).", "info")
        else:
            flash("Email not found.", "danger")
        return redirect(url_for("auth_views.login"))
    return render_template("forgot_password.html")


# ========== Token‑based password reset ==========
@auth_views.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth_views.login"))

    if request.method == "POST":
        new_password = request.form.get("password")
        confirm = request.form.get("confirm_password")
        if new_password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth_views.reset_password", token=token))
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        flash("Password reset successfully. Please log in.", "success")
        return redirect(url_for("auth_views.login"))

    return render_template("reset_password_form.html", token=token)


@auth_views.route("/toggle-sidebar", methods=["POST"])
def toggle_sidebar():
    if "sidebar_collapsed" in session:
        session.pop("sidebar_collapsed")
    else:
        session["sidebar_collapsed"] = True
    return "", 200


@auth_views.route("/logout", methods=["GET"])
def logout():
    response = redirect(url_for("auth_views.login"))
    unset_jwt_cookies(response)
    flash("Logged out successfully", "success")
    return response


# -------------------- API Routes --------------------


@auth_views.route("/api/login", methods=["POST"])
def user_login_api():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(message="Invalid credentials"), 401

    token = create_access_token(identity=str(user.id))
    response = jsonify(
        access_token=token, user={"id": user.id, "email": user.email, "role": user.role}
    )
    set_access_cookies(response, token)
    return response


@auth_views.route("/api/identify", methods=["GET"])
@jwt_required()
def identify_user():
    return jsonify(
        {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
        }
    )


@auth_views.route("/api/logout", methods=["GET"])
def logout_api():
    response = jsonify(message="Logged out")
    unset_jwt_cookies(response)
    return response