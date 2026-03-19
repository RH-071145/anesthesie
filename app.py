from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///anesthesie.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hmpi-tunis-secret-2026')
db = SQLAlchemy(app)

# ── Models ─────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nom_complet = db.Column(db.String(100))
    created_at = db.Column(db.String(50))

    # Fixed relationship
    patients = db.relationship('Patient', backref='doctor', lazy=True)   # changed backref


class Patient(db.Model):
    __tablename__ = 'patient'          # Optional but recommended

    id = db.Column(db.Integer, primary_key=True)
    
    # FIXED: ForeignKey must point to the real table name 'doctors'
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    
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

    # Relationships to other tables (these were already correct)
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


# ── Helpers ─────────────────────────────────────────────────────────────────

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


# ── Auth Routes ──────────────────────────────────────────────────────────────

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
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        nom_complet = request.form.get('nom_complet', '').strip()
        if not username or not password or not nom_complet:
            error = "Tous les champs sont obligatoires."
        elif password != confirm:
            error = "Les mots de passe ne correspondent pas."
        elif len(password) < 6:
            error = "Le mot de passe doit contenir au moins 6 caractères."
        elif User.query.filter_by(username=username).first():
            error = "Cet identifiant est déjà utilisé."
        else:
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
            return redirect(url_for('menu'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Main Routes ──────────────────────────────────────────────────────────────

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
        return redirect(url_for('page1_success', patient_id=patient.id))
    return render_template("dossier anesthesie 111.html")


@app.route("/success/<int:patient_id>")
@login_required
def page1_success(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    return render_template("success.html", patient=patient)


@app.route("/edit/patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    if request.method == "POST":
        patient.dossier_no = request.form.get("dossier_no")
        patient.nom_prenom = request.form.get("nom_prenom")
        patient.date_naissance = request.form.get("date_naissance")
        patient.sexe = request.form.get("sexe")
        patient.hospitalisation = get_hosp(request.form)
        patient.diagnostic = request.form.get("diagnostic_preop")
        patient.nature_acte = request.form.get("nature_acte")
        patient.date_acte = request.form.get("date_acte")
        patient.operateur = request.form.get("operateur")
        patient.date_consultation = request.form.get("date_consultation")
        patient.fait_par = request.form.get("fait_par")
        patient.scores = get_scores(request.form)
        patient.codage = request.form.get("codage")
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=patient_id))
    return render_template("dossier anesthesie 111.html", patient=patient, edit=True)


@app.route("/page2", methods=["GET", "POST"])
@login_required
def page2():
    patients = Patient.query.filter_by(user_id=session['user_id']).order_by(Patient.id.desc()).all()
    if request.method == "POST":
        pid = request.form.get("patient_id")
        record = EvaluationPreop(
            patient_id=pid,
            poids=request.form.get("poids"),
            taille=request.form.get("taille"),
            bmi=request.form.get("bmi"),
            cardio=", ".join(request.form.getlist("cardio[]")),
            cardio_autres=request.form.get("cardio_autres"),
            auscultation_cardiaque=request.form.get("auscultation_cardiaque"),
            signes_ic=request.form.get("signes_ic"),
            respiratoire=", ".join(filter(None, [
                "Tuberculose" if request.form.get("tuberculose") else "",
                "Asthme" if request.form.get("asthme") else "",
                "BPCO" if request.form.get("bpco") else "",
                "Emphysème" if request.form.get("emphyseme") else "",
                "Tabac" if request.form.get("tabac") else "",
            ])),
            auscultation_pulmonaire=request.form.get("auscultation_pulmonaire"),
            endocrino=", ".join(filter(None, [
                "Diabète" if request.form.get("diabete") else "",
                "Hyperthyroïdie" if request.form.get("hyperthyroidie") else "",
                "Hypothyroïdie" if request.form.get("hypothyroidie") else "",
                "Spasmophilie" if request.form.get("spasmophilie") else "",
            ])),
            hepato=", ".join(filter(None, [
                "Hépatite" if request.form.get("hepatite") else "",
                "Cirrhose" if request.form.get("cirrhose") else "",
                "Alcoolisme" if request.form.get("alcoolisme") else "",
            ])),
            renale=", ".join(filter(None, [
                "EER" if request.form.get("eer") else "",
                "FAV" if request.form.get("fav") else "",
                "Terminale" if request.form.get("terminale") else "",
            ])),
            diurese=request.form.get("diurese_details"),
            neuro=", ".join(request.form.getlist("neuro[]")),
            date_enregistrement=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=pid))
    return render_template("dossier d'anesthesie 222.html", patients=patients)


@app.route("/edit/evaluation/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_evaluation(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    record = patient.evaluation
    if request.method == "POST":
        if not record:
            record = EvaluationPreop(patient_id=patient_id)
            db.session.add(record)
        record.poids = request.form.get("poids")
        record.taille = request.form.get("taille")
        record.bmi = request.form.get("bmi")
        record.cardio = ", ".join(request.form.getlist("cardio[]"))
        record.cardio_autres = request.form.get("cardio_autres")
        record.auscultation_cardiaque = request.form.get("auscultation_cardiaque")
        record.signes_ic = request.form.get("signes_ic")
        record.respiratoire = ", ".join(filter(None, [
            "Tuberculose" if request.form.get("tuberculose") else "",
            "Asthme" if request.form.get("asthme") else "",
            "BPCO" if request.form.get("bpco") else "",
            "Emphysème" if request.form.get("emphyseme") else "",
            "Tabac" if request.form.get("tabac") else "",
        ]))
        record.auscultation_pulmonaire = request.form.get("auscultation_pulmonaire")
        record.endocrino = ", ".join(filter(None, [
            "Diabète" if request.form.get("diabete") else "",
            "Hyperthyroïdie" if request.form.get("hyperthyroidie") else "",
            "Hypothyroïdie" if request.form.get("hypothyroidie") else "",
            "Spasmophilie" if request.form.get("spasmophilie") else "",
        ]))
        record.hepato = ", ".join(filter(None, [
            "Hépatite" if request.form.get("hepatite") else "",
            "Cirrhose" if request.form.get("cirrhose") else "",
            "Alcoolisme" if request.form.get("alcoolisme") else "",
        ]))
        record.renale = ", ".join(filter(None, [
            "EER" if request.form.get("eer") else "",
            "FAV" if request.form.get("fav") else "",
            "Terminale" if request.form.get("terminale") else "",
        ]))
        record.diurese = request.form.get("diurese_details")
        record.neuro = ", ".join(request.form.getlist("neuro[]"))
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=patient_id))
    return render_template("dossier d'anesthesie 222.html", patients=[], record=record, patient=patient, edit=True)


@app.route("/page3", methods=["GET", "POST"])
@login_required
def page3():
    patients = Patient.query.filter_by(user_id=session['user_id']).order_by(Patient.id.desc()).all()
    if request.method == "POST":
        pid = request.form.get("patient_id")
        record = DonneesParacliniques(
            patient_id=pid,
            hb=request.form.get("hb"),
            ht=request.form.get("ht"),
            tp=request.form.get("tp"),
            inr=request.form.get("inr"),
            glycemie=request.form.get("glycemie"),
            uree=request.form.get("uree"),
            na=request.form.get("na"),
            k=request.form.get("k"),
            ecg=request.form.get("ecg"),
            radio_thorax=request.form.get("radio_thorax"),
            echo_cardiaque=request.form.get("echo_cardiaque"),
            dr_nom=request.form.get("dr_nom"),
            technique=", ".join(request.form.getlist("technique[]")),
            monitoring=", ".join(request.form.getlist("monitoring[]")),
            antalgique=request.form.get("antalgique"),
            date_enregistrement=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=pid))
    return render_template("dossier anesthesie 3333.html", patients=patients)


@app.route("/edit/paraclinique/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_paraclinique(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    record = patient.paraclinique
    if request.method == "POST":
        if not record:
            record = DonneesParacliniques(patient_id=patient_id)
            db.session.add(record)
        record.hb = request.form.get("hb")
        record.ht = request.form.get("ht")
        record.tp = request.form.get("tp")
        record.inr = request.form.get("inr")
        record.glycemie = request.form.get("glycemie")
        record.uree = request.form.get("uree")
        record.na = request.form.get("na")
        record.k = request.form.get("k")
        record.ecg = request.form.get("ecg")
        record.radio_thorax = request.form.get("radio_thorax")
        record.echo_cardiaque = request.form.get("echo_cardiaque")
        record.dr_nom = request.form.get("dr_nom")
        record.technique = ", ".join(request.form.getlist("technique[]"))
        record.monitoring = ", ".join(request.form.getlist("monitoring[]"))
        record.antalgique = request.form.get("antalgique")
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=patient_id))
    return render_template("dossier anesthesie 3333.html", patients=[], record=record, patient=patient, edit=True)


@app.route("/page4", methods=["GET", "POST"])
@login_required
def page4():
    patients = Patient.query.filter_by(user_id=session['user_id']).order_by(Patient.id.desc()).all()
    if request.method == "POST":
        pid = request.form.get("patient_id")
        record = ExamenComplet(
            patient_id=pid,
            gastro=", ".join(request.form.getlist("gastro[]")),
            gastro_autres=request.form.get("gastro_autres"),
            allergies=", ".join(request.form.getlist("allergies[]")),
            allergies_autres=request.form.get("allergies_autres"),
            hemostase=", ".join(request.form.getlist("hemostase[]")),
            atcd_chir=request.form.get("atcd_chir"),
            traitements=request.form.get("traitements"),
            mallampati=request.form.get("mallampati"),
            rachis_cervical=request.form.get("rachis_cervical"),
            conclusion=request.form.get("conclusion"),
            anesthesie_type=request.form.get("anesthesie_type"),
            anesthesie_details=request.form.get("anesthesie_details"),
            date_enregistrement=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=pid))
    return render_template("dossier anesthesie 444.html", patients=patients)


@app.route("/edit/examen/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_examen(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    record = patient.examen
    if request.method == "POST":
        if not record:
            record = ExamenComplet(patient_id=patient_id)
            db.session.add(record)
        record.gastro = ", ".join(request.form.getlist("gastro[]"))
        record.gastro_autres = request.form.get("gastro_autres")
        record.allergies = ", ".join(request.form.getlist("allergies[]"))
        record.allergies_autres = request.form.get("allergies_autres")
        record.hemostase = ", ".join(request.form.getlist("hemostase[]"))
        record.atcd_chir = request.form.get("atcd_chir")
        record.traitements = request.form.get("traitements")
        record.mallampati = request.form.get("mallampati")
        record.rachis_cervical = request.form.get("rachis_cervical")
        record.conclusion = request.form.get("conclusion")
        record.anesthesie_type = request.form.get("anesthesie_type")
        record.anesthesie_details = request.form.get("anesthesie_details")
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=patient_id))
    return render_template("dossier anesthesie 444.html", patients=[], record=record, patient=patient, edit=True)


@app.route("/pre", methods=["GET", "POST"])
@login_required
def pre():
    patients = Patient.query.filter_by(user_id=session['user_id']).order_by(Patient.id.desc()).all()
    if request.method == "POST":
        pid = request.form.get("patient_id")
        record = RecommandationsPre(
            patient_id=pid,
            intervention=request.form.get("intervention"),
            date_intervention=request.form.get("date_intervention"),
            operateur=request.form.get("operateur"),
            examens_demandes=request.form.get("examens_demandes"),
            premedication_veille=request.form.get("premedication_veille"),
            premedication_matin=request.form.get("premedication_matin"),
            technique=request.form.get("technique"),
            date_enregistrement=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=pid))
    return render_template("pre insthesie.html", patients=patients)


@app.route("/edit/recommandation/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_recommandation(patient_id):
    patient = own_patient(patient_id)
    if not patient:
        return redirect(url_for('records'))
    record = patient.recommandation
    if request.method == "POST":
        if not record:
            record = RecommandationsPre(patient_id=patient_id)
            db.session.add(record)
        record.intervention = request.form.get("intervention")
        record.date_intervention = request.form.get("date_intervention")
        record.operateur = request.form.get("operateur")
        record.examens_demandes = request.form.get("examens_demandes")
        record.premedication_veille = request.form.get("premedication_veille")
        record.premedication_matin = request.form.get("premedication_matin")
        record.technique = request.form.get("technique")
        db.session.commit()
        return redirect(url_for('dossier_detail', patient_id=patient_id))
    return render_template("pre insthesie.html", patients=[], record=record, patient=patient, edit=True)


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)