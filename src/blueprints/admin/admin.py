from flask import Blueprint, render_template, request, jsonify, url_for

from flask_login import login_required


from src.localization import get_locale

admin_bp = Blueprint('admin', __name__)




@admin_bp.route('/admin')
@login_required
def admin():
    return render_template('pages/admin/dashboard.html', locale=get_locale())