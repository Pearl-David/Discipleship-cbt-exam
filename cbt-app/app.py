from flask import send_file
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security options
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Change to True in production
app.config['SESSION_PERMANENT'] = False

# Ensure instance directory exists
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    attempted = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    option_a = db.Column(db.String(100))
    option_b = db.Column(db.String(100))
    option_c = db.Column(db.String(100))
    correct_answer = db.Column(db.String(1))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, username):
            session['user_id'] = user.id
            return redirect(url_for('exam'))
        return render_template('login.html', error='Invalid username')
    return render_template('login.html')

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.attempted:
        return "You have already attempted the exam."

    questions = Question.query.all()
    if request.method == 'POST':
        score = 0
        submission = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Username': user.username
        }

        for q in questions:
            selected = request.form.get(str(q.id))
            if selected == q.correct_answer:
                score += 1
            submission[f"Q{q.id}"] = selected

        submission['Score'] = score
        submission['Total'] = len(questions)

        user.score = score
        user.attempted = True
        db.session.commit()

        save_to_excel(submission)

        return render_template('result.html', score=score, total=len(questions))

    return render_template('exam.html', questions=questions)

def save_to_excel(submission):
    file = 'submissions.xlsx'
    if not os.path.exists(file):
        df = pd.DataFrame([submission])
        df.to_excel(file, index=False)
    else:
        df_existing = pd.read_excel(file)
        df_new = pd.concat([df_existing, pd.DataFrame([submission])], ignore_index=True)
        df_new.to_excel(file, index=False)

@app.route('/admin/download-submissions')
def download_submissions():
    file_path = 'submissions.xlsx'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "No submissions file found yet.", 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.first():
            default_users = [
                "Alao Victor Oluwatayemise", "John Doe", "Jane Smith", "Peter Johnson", "Mary Adams", "Samuel Oladele",
                "Grace Adebayo", "Daniel Okonkwo", "Mercy Omotola", "Emmanuel Adeola", "Deborah Oke", "David Benson",
                "Esther Akande", "OLAOYE Oluwadarasimi", "OYATUNDE DAMILOLA IREMIDE", "Oyedemi Emmanuel Oyeleke",
                "AKHIGBE Prevail Caleb", "Olanrewaju Isaiah", "OLATUNJI Emmanuel Oladeji", "ADELEKE PETER INIOLUWA",
                "PAUL", "AKINOlA Faith Testimony", "Israel Temiloluwa OGUNSOLA", "Adikwu John",
                "Adebayo Victor Oluwabori", "ADENIRAN TEMIDAYO PRAISE", "AFOLABI john ayomide",
                "Ojo Rebecca Oluwafunmilola", "AJALA Caleb", "ADEWALE Jerry Ayomide", "AYOOLA BLESSING TITILADE",
                "Oyebade Blessing Oluwapelumi", "OYEBOLA Ireoluwa Jeremiah", "MATTHEW Faith",
                "ERONMOSELE SHALOM OSETOKHAME", "ABIMBOLA GOODNESS OLUDAMOLA", "AKINWUMI Blessing Olajumoke",
                "OYEDEMI Favour Ayomikun", "ADISA STEPHEN BABAFEMI", "KILANKO Oluwatobiloba .D.", "AYOOLA Bolanle",
                "OLAGOKE DANIEL OLORUNFEMI", "ABIMBOLA Hismercy Toluwani", "OKEDI FAVOUR OGHENETEGA",
                "Awodele Elizabeth praise", "SANUSI Kehinde johanah", "OLUWANIMBE Faithful Oluwadara",
                "OYEBOLA Oreoluwa James", "BABALOLA Jeremiah Iniolu", "OLALEYE OLOLADE DEBORAH", "AJALA JERRY OLUWASEUN",
                "OWOLABI OLAMIDE PEACE", "OLUFEMI Joel Seyi", "AJAYI Goodness Paul", "Adetunji Promise Ayomikun",
                "OWOLAWASE Simeon Olajide", "AJAYI ELIJAH OLUWASEGUN", "AYANTUNDE Patience Omowumi",
                "ALAGBE ABIGEAL ADEBOLA", "OLADIPUPO Paul Segun", "AREMU KEMI TAIWO",
                "ADEJUMO Joshua Oluwadamilare", "Aderanti Adesewa Grace", "Olugbade ComFort",
                "AJIBADE TOLUWALASE PRAISE", "GODWIN PRAISE OBOR", "OJOELE Oluwaseun Ruth",
                "Olajide David Oluwaferanmi", "OLAMOYEGUN Oluwadamilola Dolapo", "ADEWUMI Deborah Ayomide",
                "JOEL Favour", "OYEKUNLE Marcus Timileyin", "OYADIRAN Dorcas oluwadamisi",
                "OLAYANJU Archippus Oladayo", "ADEGOKE, Praise Moyinoluwa", "AGBOOLA FAVOUR ADEKEMI",
                "ADEBISI Feranmi Eunice", "ISHOLA Emmanuel Iseoluwa", "KOLAWOLE VICTORY ATINUKE",
                "ALABI DEBORAH INIOLUWA", "ISAIAH Adebayo Adeeyo", "MATTHEW Precious Ibukunoluwa",
                "OYELEYE Gladys Oluwajuwonlo", "ODEBOWALE", "ANWO HERITAGE OLUWADAMILOLA",
                "ABOLADE MARVELLOUS OLAYEMI", "Bamigboye Joshua boluwatife", "OCHIMANA Elijah Iko-Ojo",
                "OKE FAVOUR OLUWASEYI", "ADEGOKE", "OLANREWAJU MAYOWA JOHN", "OLADOJA GOD'SGLORY AYANFE",
                "Olaniran dorcas omolara", "OLADELE Abosede", "Bolarinwa Janet",
                "SHALOM GBADEBO OLUWAFEYISARA", "Raphael Temitope Good luck", "ADEBUNMI SUCCESS ADEOLA",
                "OGUNLADE Excellence", "AKERELE Ifedayo David", "Pearl David", "Ogundele Eunice",
                "Adebayo Enoch", "Ireoluwa Oyebola Jeremiah", "Aderibigbe, Marvellous Aduragbemi",
                "Adediran Victoria Oluwatobi", "Ajibade Toluwalase", "Samuel Bamikole", "Lilian", "Olatunji Oluwaferanmi", "Michael Ogundele", "Makinde Ayomide", "Praise", "Promise", "Blessing Fakolujo", "Adewuyi Deborah", "Aderogba Oluwadamilare", "Oladeye Ololade", "Adeyeye Precious", "Owolawase Simeon", "Popoola Joy", "Adebowale Segun"

            ]  # Shortened list for readability
            for username in default_users:
                hashed_pw = generate_password_hash(username)
                db.session.add(User(username=username, password=hashed_pw))
            db.session.commit()

        if not Question.query.first():
            db.session.add_all([
                Question(text="God's infallible WORD teaches & we believe:", option_a="Bible doctrines", option_b="Discipleship teachings", option_c="Repentance only", correct_answer="A"),
                Question(text="What is Bible doctrine 5?", option_a="The Godhead", option_b="Repentance", option_c="Justification", correct_answer="A"),
                Question(text="The Bible is _____", option_a="God's will", option_b="God's word", option_c="God's own", correct_answer="B"),
                Question(text="____ will occur after the rapture.", option_a="Justification", option_b="The Great tribulation", option_c="Peace & Joy in the world", correct_answer="B"),
                Question(text="What is Bible doctrine 8?", option_a="The Lord's supper", option_b="Water baptism", option_c="The Holy Bible", correct_answer="B"),
                Question(text="Is Bible doctrine 3 known to be 'The Virgin birth of Jesus'?", option_a="False", option_b="True", option_c="None of the above", correct_answer="B"),
                Question(text="The redeemed shall dwell with _____ forever.", option_a="satan", option_b="spirit", option_c="God", correct_answer="C"),
                Question(text="_____ was prepared for the devil & his angels.", option_a="Punishment", option_b="evils", option_c="hell fire", correct_answer="C"),
                Question(text="The Bible teaches that man is totally depraved.", option_a="Yes", option_b="No", option_c="Yes & no", correct_answer="A"),
                Question(text="Where is God expecting you to spend eternity with HIM?", option_a="Heaven", option_b="Hell", option_c="the world", correct_answer="A"),
                Question(text="The last session of the Bible doctrine is known as", option_a="Revelations", option_b="Eschatology", option_c="Eternity", correct_answer="B"),
                Question(text="What is Bible doctrine 1?", option_a="The Godhead", option_b="The Holy Bible", option_c="Restitution", correct_answer="B"),
                Question(text="______ is the act of God's grace whereby one's sins are forgiven...", option_a="Restitution", option_b="Righteousness", option_c="Justification", correct_answer="C"),
                Question(text="The Bible teaches that Jesus Christ was born of a virgin.", option_a="False", option_b="True", option_c="partially correct", correct_answer="B"),
                Question(text="What is Bible doctrine 15?", option_a="The rapture", option_b="Repentance", option_c="Restitution", correct_answer="A"),
                Question(text="What is the last Bible doctrine focused on?", option_a="Hell fire", option_b="Rapture", option_c="Heaven", correct_answer="C"),
                Question(text="How many Bible doctrines have we?", option_a="24", option_b="20", option_c="22", correct_answer="C"),
                Question(text="What is Bible doctrine 12?", option_a="Redemption healing and health", option_b="Entire sanctification", option_c="Prayer", correct_answer="A"),
                Question(text="The Holy Bible consists of_____ books of the New Testament.", option_a="39", option_b="37", option_c="27", correct_answer="C"),
                Question(text="Bible doctrine 9 is", option_a="The Lord's supper", option_b="Heaven", option_c="Eternity", correct_answer="A"),
                Question(text="Fasting is an optional activity for a Christian.", option_a="True", option_b="False", option_c="None", correct_answer="B"),
                Question(text="The first account of the disciples receiving the Holy Ghost baptism...", option_a="Acts 1:8", option_b="Acts 2:1–4", option_c="Mark 16:15", correct_answer="B"),
                Question(text="'Love not the world...' can be found where?", option_a="John 15:1", option_b="1 John 3:1", option_c="1 John 2:15", correct_answer="C"),
                Question(text="All but one of the following hinders an effective quiet time:", option_a="Dancing", option_b="Gluttony", option_c="Fatigue", correct_answer="A"),
                Question(text="The following are hindrances to benefiting from the Bible except:", option_a="Unbelief", option_b="Double-mindedness", option_c="Reading", correct_answer="C"),
                Question(text="'Fishers of men' is a figurative expression meaning:", option_a="Catching fishes", option_b="Soul winning", option_c="Quiet time", correct_answer="B"),
                Question(text="One of these is not a definition of sanctification:", option_a="Removal of sin", option_b="Holiness", option_c="The third work of grace", correct_answer="C"),
                Question(text="Justification comes after:", option_a="Sinning", option_b="Salvation", option_c="Sanctification", correct_answer="B"),
                Question(text="Which of these should we give less priority to?", option_a="Spiritual life", option_b="Skill acquisition", option_c="Social media", correct_answer="C"),
                Question(text="The property in church should be treated as our own.", option_a="True", option_b="False", option_c="None", correct_answer="A"),
                Question(text="Which is not a gift of the Spirit?", option_a="Gentleness", option_b="Faith", option_c="Working of miracles", correct_answer="A"),
                Question(text="Way God can speak to us in knowing His will in marriage:", option_a="Cohabitating", option_b="Deep love", option_c="Through a prophet", correct_answer="B"),
                Question(text="Another name for pseudo-Christianity is:", option_a="Sudden Christianity", option_b="False Christianity", option_c="Imperfect Christianity", correct_answer="B"),
                Question(text="The knowledge of homiletics is needed for every Christian.", option_a="True", option_b="False", option_c="None", correct_answer="A"),
                Question(text="God is interested in our finances as our spiritual life.", option_a="No", option_b="Sometimes", option_c="Yes", correct_answer="C"),
                Question(text="All but one is a gesture to avoid with opposite gender:", option_a="Hugging", option_b="Isolated places", option_c="Sitting close", correct_answer="C"),
                Question(text="Fasting must be accompanied by one of these:", option_a="Shouting", option_b="Praying", option_c="Listening", correct_answer="B"),
                Question(text="Not a prerequisite for receiving Holy Ghost baptism:", option_a="Salvation", option_b="Sanctification", option_c="Gymnastics", correct_answer="C"),
                Question(text="Worldliness is okay for me:", option_a="No", option_b="Yes", option_c="Sometimes", correct_answer="A"),
                Question(text="An example of Christian dressing:", option_a="Tight trousers", option_b="Jewelry", option_c="Moderate trousers", correct_answer="C"),
                Question(text="Who replaced Judas Iscariot as a disciple?", option_a="Matthias", option_b="Barnabas", option_c="Stephen", correct_answer="A"),
                Question(text="Where did the Holy Spirit descend on the apostles?", option_a="Upper Room", option_b="Synagogue", option_c="Temple", correct_answer="A"),
                Question(text="What appeared over the apostles' heads on Pentecost?", option_a="Smoke", option_b="Flames", option_c="Water", correct_answer="B"),
                Question(text="What was Paul's original name?", option_a="Simon", option_b="Saul", option_c="Silas", correct_answer="B"),
                Question(text="Who was stoned while Paul watched?", option_a="Stephen", option_b="Barnabas", option_c="Peter", correct_answer="A"),
                Question(text="Where was Paul when he encountered Jesus?", option_a="Damascus", option_b="Jerusalem", option_c="Rome", correct_answer="A"),
                Question(text="Who healed the lame man at the temple gate?", option_a="Peter & John", option_b="Paul", option_c="Stephen", correct_answer="A"),
                Question(text="How many people were added to the church on Pentecost?", option_a="3000", option_b="120", option_c="5000", correct_answer="A"),
                Question(text="What was the name of the sorcerer in Acts 8?", option_a="Simon", option_b="Elymas", option_c="Bar-Jesus", correct_answer="A"),
                Question(text="What was Paul's profession?", option_a="Fisherman", option_b="Tentmaker", option_c="Carpenter", correct_answer="B"),
                Question(text="Why does Ravenhill say revival tarries?", option_a="Because people don't pray", option_b="Because God delays", option_c="Because of politics", correct_answer="A"),
                Question(text="What does Ravenhill call the missing element in modern preaching?", option_a="Humor", option_b="Anointing", option_c="Fire", correct_answer="C"),
                Question(text="What must a man do before God will use him mightily?", option_a="Be educated", option_b="Be broken", option_c="Be famous", correct_answer="B"),
                Question(text="What did Ravenhill say the church lacks today?", option_a="Strategy", option_b="Power", option_c="Money", correct_answer="B"),
                Question(text="What kind of men does God use?", option_a="Gifted men", option_b="Smart men", option_c="Broken men", correct_answer="C"),
                Question(text="What did Ravenhill say we need more than revival meetings?", option_a="Prayer meetings", option_b="Miracles", option_c="Money", correct_answer="A"),
                Question(text="What is the devil not afraid of?", option_a="Programs", option_b="Holy men", option_c="Fasting", correct_answer="A"),
                Question(text="Where did Ravenhill say true revival starts?", option_a="In churches", option_b="In seminars", option_c="In hearts", correct_answer="C"),
                Question(text="What makes a sermon powerful, according to Ravenhill?", option_a="Length", option_b="Delivery", option_c="Burden", correct_answer="C"),
                Question(text="Ravenhill said, 'The church used to be a lifeboat, now it’s a...'", option_a="Cruise ship", option_b="Battleship", option_c="Fishing boat", correct_answer="A"),
            ])
            db.session.commit()

    app.run(host='0.0.0.0', port=10000)
