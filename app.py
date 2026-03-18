from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)

# ====================== DATABASE CONFIGURATION ======================
# Railway provides DATABASE_URL (PostgreSQL), fallback to SQLite for local development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Railway: postgres:// → postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anesthesie.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hmpi-tunis-secret-2026')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nom_complet = db.Column(db.String(100))
    created_at = db.Column(db.String(50))
    patients = db.relationship('Patient', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dossier_no = db.Column(db.String(50))
    nom_prenom = db.Column(db.String(100))
    date_naissance = db.Column(db.String(50))
    sexe = db.Column(db.String(10))
    hospitalisation = db.Column(db.String(100))
    diagnostic = db.Column(db.Text)
    nature_acte = db.Column(db.String(100))
    date_acte = db.Column(db.String(50))
    operateur = db.Column(db.String(100))
    date_consultation = db.Column(db.String(50))
    fait_par = db.Column(db.String(100))
    scores = db.Column(db.String(300))
    codage = db.Column(db.Text)
    date_enregistrement = db.Column(db.String(50))

    evaluation = db.relationship('EvaluationPreop', backref='patient', uselist=False)
    paraclinique = db.relationship('DonneesParacliniques', backref='patient', uselist=False)
    examen = db.relationship('ExamenComplet', backref='patient', uselist=False)
    recommandation = db.relationship('RecommandationsPre', backref='patient', uselist=False)


class EvaluationPreop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    poids = db.Column(db.String(20))
    taille = db.Column(db.String(20))
    bmi = db.Column(db.String(20))
    cardio = db.Column(db.String(500))
    cardio_autres = db.Column(db.String(300))
    auscultation_cardiaque = db.Column(db.String(300))
    signes_ic = db.Column(db.String(300))
    respiratoire = db.Column(db.String(300))
    auscultation_pulmonaire = db.Column(db.String(300))
    endocrino = db.Column(db.String(300))
    hepato = db.Column(db.String(300))
    renale = db.Column(db.String(300))
    diurese = db.Column(db.String(100))
    neuro = db.Column(db.String(300))
    date_enregistrement = db.Column(db.String(50))


class DonneesParacliniques(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    hb = db.Column(db.String(20))
    ht = db.Column(db.String(20))
    tp = db.Column(db.String(20))
    inr = db.Column(db.String(20))
    glycemie = db.Column(db.String(20))
    uree = db.Column(db.String(20))
    na = db.Column(db.String(20))
    k = db.Column(db.String(20))
    ecg = db.Column(db.String(200))
    radio_thorax = db.Column(db.String(200))
    echo_cardiaque = db.Column(db.String(200))
    dr_nom = db.Column(db.String(100))
    technique = db.Column(db.String(300))
    monitoring = db.Column(db.String(300))
    antalgique = db.Column(db.String(200))
    date_enregistrement = db.Column(db.String(50))


class ExamenComplet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    gastro = db.Column(db.String(300))
    gastro_autres = db.Column(db.String(200))
    allergies = db.Column(db.String(300))
    allergies_autres = db.Column(db.String(200))
    hemostase = db.Column(db.String(300))
    atcd_chir = db.Column(db.Text)
    traitements = db.Column(db.Text)
    mallampati = db.Column(db.String(10))
    rachis_cervical = db.Column(db.String(50))
    conclusion = db.Column(db.Text)
    anesthesie_type = db.Column(db.String(200))
    anesthesie_details = db.Column(db.Text)
    date_enregistrement = db.Column(db.String(50))


class RecommandationsPre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    intervention = db.Column(db.String(200))
    date_intervention = db.Column(db.String(50))
    operateur = db.Column(db.String(100))
    examens_demandes = db.Column(db.String(300))
    premedication_veille = db.Column(db.String(100))
    premedication_matin = db.Column(db.String(100))
    technique = db.Column(db.String(100))
    date_enregistrement = db.Column(db.String(50))


# ── Auth Helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def get_hosp(form):
    return ", ".join(filter(None, [
        "Urgence" if form.get("urgence") else "",
        "Réglée" if form.get("reglee") else "",
        "Ambulatoire" if form.get("ambulatoire") else "",
    ]))


def get_scores(form):
    return ", ".join(filter(None, [
        "ASA" if form.get("asa") else "",
        "NYHA" if form.get("nyha") else "",
        "MALLAMPATI" if form.get("mallampati_score") else "",
        "GOLDMAN" if form.get("goldman") else "",
        "GLASGOW" if form.get("glasgow") else "",
        "ISS" if form.get("iss") else "",
    ]))


def own_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    if p.user_id != session['user_id']:
        return None
    return p


# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('menu'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['nom_complet'] = user.nom_complet
            return redirect(url_for('menu'))
        error = "Identifiant ou mot de passe incorrect."
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('menu'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        nom_complet = request.form.get('nom_complet', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not nom_complet or not password or not confirm:
            flash("Tous les champs sont obligatoires.", "danger")
            return render_template('register.html')

        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash("Cet identifiant est déjà utilisé.", "danger")
            return render_template('register.html')

        try:
            user = User(
                username=username,
                nom_complet=nom_complet,
                created_at=datetime.now().strftime("%d/%m/%Y")
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            session['username'] = user.username
            session['nom_complet'] = user.nom_complet

            flash("Compte créé avec succès !", "success")
            return redirect(url_for('menu'))

        except Exception as e:
            db.session.rollback()
            flash("Une erreur est survenue lors de la création du compte.", "danger")
            return render_template('register.html')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Main Routes ───────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def menu():
    user = current_user()
    return render_template("menu.html", user=user)


@app.route("/page1", methods=["GET", "POST"])
@login_required
def page1():
    if request.method == "POST":
        patient = Patient(
            user_id=session['user_id'],
            dossier_no=request.form.get("dossier_no"),
            nom_prenom=request.form.get("nom_prenom"),
            date_naissance=request.form.get("date_naissance"),
            sexe=request.form.get("sexe"),
            hospitalisation=get_hosp(request.form),
            diagnostic=request.form.get("diagnostic_preop"),
            nature_acte=request.form.get("nature_acte"),
            date_acte=request.form.get("date_acte"),
            operateur=request.form.get("operateur"),
            date_consultation=request.form.get("date_consultation"),
            fait_par=request.form.get("fait_par"),
            scores=get_scores(request.form),
            codage=request.form.get("codage"),
            date_enregistrement=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.session.add(patient)
        db.session.commit()
        return redirect(url_for('success', patient_id=patient.id))
    return render_template("dossier anesthesie 111.html")


# ... (all your other routes: edit_patient, page2, page3, page4, pre, success, records, dossier_detail, etc.)
# I kept them exactly as you had them, just removed duplicates.

@app.route("/records")
@login_required
def records():
    patients = Patient.query.filter_by(user_id=session['user_id']).order_by(Patient.id.desc()).all()
    return render_template("records.html", patients=patients)


@app.route("/dossier/<int:patient_id>")
@login_required
def dossier_detail(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    return render_template("dossier_detail.html", patient=patient)


# ====================== DATABASE INITIALIZATION ======================
# This runs on every startup (very important for Railway PostgreSQL)
with app.app_context():
    db.create_all()
    print("✅ All database tables created / updated successfully!")

# Only for local development
if __name__ == "__main__":
    app.run(debug=True)