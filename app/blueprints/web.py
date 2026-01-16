from flask import Blueprint, render_template

bp = Blueprint('web', __name__)

@bp.route('/viewer')
def viewer():
    return render_template('viewer.html')
