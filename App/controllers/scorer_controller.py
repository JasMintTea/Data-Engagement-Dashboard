from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from App.models import db, Participant, Result

scorer_bp = Blueprint('scorer', __name__)

@scorer_bp.route('/enter-results', methods=['GET', 'POST'])
@login_required
def enter_results():
    if request.method == 'POST':
        participant_id = request.form.get('participant_id')
        event_time = request.form.get('finish_time')

        new_result = Result(participant_id=participant_id, finish_time=event_time)

        db.session.add(new_result)
        db.session.commit()

        flash(f"Result recorderd for Participant ID: {participant_id}")
        return redirect(url_for('scorer.enter_results'))

    participants = Participant.query.filter_by(institution_id=current_user.institution_id).all()
    return render_template('enter_results.html', participants=participants)

def get_recent_results(limit=10):
    return Result.query.order_by(Result.id.desc()).limit(limit).all()
