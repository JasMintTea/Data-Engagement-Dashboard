from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user
from App.controllers.scorer_controller import get_recent_results
from App.controllers.hr_controller import get_available_events
from App.models import Registration, Result, Stage, Participant, SeasonEvent, Event
from App.database import db
import csv
import io


def _parse_int(value):
    if value is None:
        return None
    value = str(value).strip()
    return int(value) if value.isdigit() else None


def _get_csv_field(row, *names):
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value != '':
                return value
    return None


scorer_views = Blueprint('scorer_views', __name__, template_folder='../templates')

@scorer_views.route('/scorer/dashboard')
@jwt_required()
def dashboard():
    if current_user.role not in ['admin', 'scorer']:
        return "Access Denied", 403
    results = get_recent_results()
    return render_template('scorer/scorer.html', results=results)


@scorer_views.route('/scorer/enter-results', methods=['GET', 'POST'])
@jwt_required()
def enter_results():
    if current_user.role not in ['admin', 'scorer']:
        return "Access Denied", 403

    if request.method == 'POST':
        season_event_id = request.form.get('season_event_id')
        if not season_event_id:
            flash('Please select an event.', 'danger')
            return redirect(url_for('scorer_views.enter_results'))

        registrations = Registration.query.filter_by(season_event_id=season_event_id).all()
        stage = Stage.query.filter_by(season_event_id=season_event_id).first()
        if not stage:
            flash('No stage found for this event.', 'danger')
            return redirect(url_for('scorer_views.enter_results'))

        for reg in registrations:
            pid = reg.participant_id
            time_key = f'time_{pid}'
            place_key = f'placement_{pid}'
            if time_key in request.form and request.form[time_key]:
                finish_time = request.form[time_key]
                placement = request.form.get(place_key) or None
                existing = Result.query.filter_by(registration_id=reg.id).first()
                if existing:
                    existing.finish_time = finish_time
                    existing.placement = placement
                else:
                    result = Result(
                        registration_id=reg.id,
                        stage_id=stage.id,
                        finish_time=finish_time,
                        placement=placement
                    )
                    db.session.add(result)
        db.session.commit()
        flash('Results saved successfully!', 'success')
        return redirect(url_for('scorer_views.dashboard'))

    # GET request – show event selection form
    events = get_available_events(current_user.institution_id)   # scorers have no institution, but the function works
    return render_template('scorer/select_event.html', events=events)


@scorer_views.route('/scorer/enter-results/event/<int:season_event_id>')
@jwt_required()
def show_participants_for_event(season_event_id):
    if current_user.role not in ['admin', 'scorer']:
        return "Access Denied", 403
    registrations = Registration.query.filter_by(season_event_id=season_event_id).all()
    participants = [reg.participant for reg in registrations]
    return render_template('scorer/enter_results_form.html',
                           participants=participants,
                           season_event_id=season_event_id)

@scorer_views.route('/scorer/upload-results', methods=['GET', 'POST'])
@jwt_required()
def upload_results():
    if current_user.role not in ['admin', 'scorer']:
        return "Access Denied", 403

    if request.method == 'POST':
        file = request.files.get('csv_file')
        selected_season_event_id = request.form.get('season_event_id')

        if not file or not file.filename.lower().endswith('.csv'):
            flash('Please upload a valid CSV file.', 'danger')
            return redirect(request.url)

        content = file.read()
        try:
            text = content.decode('utf-8-sig')
        except AttributeError:
            text = str(content)
        stream = io.StringIO(text)
        csv_input = csv.DictReader(stream, skipinitialspace=True)

        count = 0
        skipped = 0
        errors = []

        for row_number, row in enumerate(csv_input, start=1):
            pid = _get_csv_field(row, 'participant_id', 'participantid', 'participant')
            finish_time = _get_csv_field(row, 'finish_time', 'finish time', 'time')
            placement = _parse_int(_get_csv_field(row, 'placement', 'place'))
            row_season_event_id = _get_csv_field(row, 'season_event_id', 'season_event', 'event_id', 'event')
            row_stage_id = _parse_int(_get_csv_field(row, 'stage_id'))

            if not pid or not finish_time:
                skipped += 1
                errors.append(f'Row {row_number}: missing participant_id or finish_time')
                continue

            try:
                pid = int(pid)
            except ValueError:
                skipped += 1
                errors.append(f'Row {row_number}: invalid participant_id "{pid}"')
                continue

            season_event_id = None
            if row_season_event_id:
                if row_season_event_id.isdigit():
                    season_event_id = int(row_season_event_id)
                else:
                    # Allow a row to specify an event name instead of ID
                    season_event = SeasonEvent.query.join(Event).filter(Event.name.ilike(row_season_event_id)).first()
                    if season_event:
                        season_event_id = season_event.id
                    else:
                        skipped += 1
                        errors.append(f'Row {row_number}: unknown event "{row_season_event_id}"')
                        continue
            elif selected_season_event_id:
                try:
                    season_event_id = int(selected_season_event_id)
                except ValueError:
                    season_event_id = None

            if not season_event_id:
                skipped += 1
                errors.append(f'Row {row_number}: no season_event_id provided')
                continue

            stage = None
            if row_stage_id:
                stage = Stage.query.get(row_stage_id)
                if not stage or stage.season_event_id != season_event_id:
                    skipped += 1
                    errors.append(f'Row {row_number}: invalid stage_id "{row_stage_id}"')
                    continue
            else:
                stage = Stage.query.filter_by(season_event_id=season_event_id).first()

            if not stage:
                skipped += 1
                errors.append(f'Row {row_number}: no stage found for event {season_event_id}')
                continue

            reg = Registration.query.filter_by(
                participant_id=pid,
                season_event_id=season_event_id
            ).first()
            if not reg:
                skipped += 1
                errors.append(f'Row {row_number}: participant {pid} not registered for event {season_event_id}')
                continue

            result = Result.query.filter_by(registration_id=reg.id, stage_id=stage.id).first()
            if not result:
                result = Result(registration_id=reg.id, stage_id=stage.id)
            result.finish_time = finish_time
            result.placement = placement
            result.approved = False
            result.is_error = False
            db.session.add(result)
            count += 1

        db.session.commit()

        if skipped > 0:
            flash(f'Successfully imported {count} results, skipped {skipped} invalid rows.', 'warning')
            for msg in errors[:5]:
                flash(msg, 'danger')
        else:
            flash(f'Successfully imported {count} results!', 'success')

        return redirect(url_for('scorer_views.dashboard'))

    # GET request – show form
    from App.controllers.hr_controller import get_available_events
    events = get_available_events(current_user.institution_id)   # scorers have no institution, but the function works
    return render_template('scorer/upload_results.html', events=events)

@scorer_views.route('/scorer/flag-result/<int:result_id>', methods=['POST'])
@jwt_required()
def flag_result(result_id):
    if current_user.role not in ['admin', 'scorer']:
        return "Access Denied", 403
    
    result = Result.query.get_or_404(result_id)
    result.is_error = not result.is_error  # Toggle the flag
    db.session.commit()
    flash('Result flag updated!', 'success')
    return redirect(url_for('scorer_views.dashboard'))
