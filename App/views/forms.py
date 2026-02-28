from flask import Blueprint, render_template

forms_views = Blueprint('forms_views', __name__)

@forms_views.route('/eventform')
def event_form():
    return render_template('Forms/eventform.html')

@forms_views.route('/institutionform')
def institution_form():
    return render_template('Forms/InstitutionForm.html')

@forms_views.route('/seasonform')
def season_form():
    return render_template('Forms/SeasonForm.html')
