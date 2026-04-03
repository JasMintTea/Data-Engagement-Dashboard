import io
from datetime import date

import pytest
from App.main import create_app
from App.database import db
from App.models import Season, Event, SeasonEvent, Stage, Participant, Registration, Scorer, Result


@pytest.fixture(scope='module')
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'scorer-test-secret',
        'JWT_TOKEN_LOCATION': ['headers'],
        'JWT_COOKIE_CSRF_PROTECT': False,
    })
    with app.app_context():
        db.create_all()

        season = Season(year=2025, status='active')
        db.session.add(season)
        db.session.flush()

        event = Event(name='Urban Challenge', event_type='run')
        db.session.add(event)
        db.session.flush()

        se = SeasonEvent(season_id=season.id, event_id=event.id, start_date=date(2025, 3, 1), end_date=date(2025, 11, 30))
        db.session.add(se)
        db.session.flush()

        stage = Stage(season_event_id=se.id, stage_number=1, distance='5K', location='Test Track', stage_date=date(2025, 3, 1))
        db.session.add(stage)

        # Participant must belong to an institution per model constraint
        from App.models import Institution
        institution = Institution(name='Test Institution', code='TEST')
        db.session.add(institution)
        db.session.flush()

        participant = Participant(first_name='Jane', last_name='Doe', institution_id=institution.id)
        db.session.add(participant)
        db.session.flush()

        registration = Registration(participant_id=participant.id, season_event_id=se.id)
        db.session.add(registration)

        scorer = Scorer(firstname='Scorer', lastname='User', username='scorer', email='scorer@test.com', password='Scorer123!')
        db.session.add(scorer)

        db.session.commit()

        yield app

        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def scorer_headers(client):
    resp = client.post('/api/login', json={'email': 'scorer@test.com', 'password': 'Scorer123!'})
    assert resp.status_code == 200
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_scorer_dashboard_upload_and_flag(client):
    headers = scorer_headers(client)

    # Dashboard accessible
    resp = client.get('/scorer/dashboard', headers=headers)
    assert resp.status_code == 200
    assert b'Master Score Log' in resp.data

    # Upload results page includes the season event
    resp = client.get('/scorer/upload-results', headers=headers)
    assert resp.status_code == 200
    assert b'Urban Challenge' in resp.data

    # Add results through CSV upload
    with client.application.app_context():
        se = SeasonEvent.query.first()
        registration = Registration.query.first()
        stage = Stage.query.first()

    csv_file = io.BytesIO(b'participant_id,finish_time,placement\n' + str(registration.participant_id).encode() + b',00:12:34,1\n')
    data = {
        'season_event_id': str(se.id),
        'csv_file': (csv_file, 'results.csv')
    }

    resp = client.post('/scorer/upload-results', headers=headers, data=data, content_type='multipart/form-data', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Successfully imported 1 results!' in resp.data

    # The imported result is in DB
    with client.application.app_context():
        result = Result.query.filter_by(registration_id=registration.id, stage_id=stage.id).first()
        assert result is not None
        assert result.finish_time == '00:12:34'
        assert result.placement == 1
        assert result.is_error is False

    # Toggle error flag
    resp = client.post(f'/scorer/flag-result/{result.id}', headers=headers, follow_redirects=True)
    assert resp.status_code == 200
    with client.application.app_context():
        result = Result.query.get(result.id)
        assert result.is_error is True

    # Toggle back
    resp = client.post(f'/scorer/flag-result/{result.id}', headers=headers, follow_redirects=True)
    assert resp.status_code == 200
    with client.application.app_context():
        result = Result.query.get(result.id)
        assert result.is_error is False
