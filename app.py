import json
import random
from datetime import date
from pathlib import Path
from urllib.parse import quote
import streamlit as st

st.set_page_config(page_title='Мій іспит', page_icon='🌿', layout='centered')
st.markdown('''<style>.block-container{max-width:780px;padding-top:1.4rem}div.stButton>button{border-radius:13px;min-height:44px}h1{font-size:2rem} .stAlert{border-radius:12px}</style>''',unsafe_allow_html=True)
Q=json.loads(Path(__file__).with_name('questions.json').read_text(encoding='utf-8'))
QMAP={q['id']:q for q in Q}

def read_progress():
    try:
        data=json.loads(st.query_params.get('progress','{}'))
        return {int(k):int(v) for k,v in data.items() if int(k) in QMAP and int(v) in (0,1,2)}
    except (ValueError,TypeError):
        return {}

def store_progress(p):
    st.query_params['progress']=json.dumps(p,ensure_ascii=False,separators=(',',':'))

def advance():
    st.session_state.cursor+=1
    st.session_state.reveal=0

def assess(qid,level):
    p=read_progress();p[qid]=level;store_progress(p);advance()

for k,v in [('cursor',0),('reveal',0),('ticket',[]),('ticket_answers',set())]:
    if k not in st.session_state: st.session_state[k]=v
p=read_progress()
known=sum(v==2 for v in p.values())
started=len(p)
# Підтримка поза навчальними відповідями: не змішуємо мотивацію з матеріалом іспиту.
ENCOURAGEMENT = [
    'Ти молодець, що вчишся. Кожне запитання — ще один крок уперед. 💛',
    'Не треба знати все одразу. Головне — рухатися маленькими кроками. 🌷',
    'Помилки під час навчання — це нормально. Саме так ми запам’ятовуємо. 🌿',
    'Ти вже робиш важливу справу. Я в тебе вірю! ✨',
    'Сьогодні достатньо стати трішечки впевненішою, ніж учора. 💪',
    'Можна хвилюватися й водночас добре скласти іспит. Ти впораєшся! 💛',
    'Кожна відповідь, яку ти пригадала сама, — твоя маленька перемога. 🌼',
    'Не поспішай. Ти маєш право подумати й відповісти своїми словами. 🌸',
    'Твоя наполегливість уже заслуговує на похвалу. Молодець! ⭐',
    'Я пишаюся тим, як старанно ти готуєшся. У тебе все вийде! ❤️',
]
with st.sidebar:
    st.markdown('### 💛 Трошки підтримки')
    st.info(ENCOURAGEMENT[(date.today().toordinal() + st.session_state.cursor // 3) % len(ENCOURAGEMENT)])
    st.caption('Ти можеш вчитися у своєму темпі. Перерва — теж частина підготовки.')

st.title('🌿 Мій іспит')
st.caption('69 запитань українською · 7 днів навчання + 7 днів повторення · білет із 5 запитань')
st.caption('💛 Ти молодець, що готуєшся. Крок за кроком — і все вийде!')
st.progress(known/69,text=f'Впевнено знаю: {known}/69 · уже пробувала: {started}/69')
mode=st.radio('Оберіть режим', ['📖 Навчання','🔁 Повторення','🎫 Білет: 5 запитань','📚 Довідник'],horizontal=False)

if mode=='📖 Навчання':
    day=st.select_slider('День навчання',options=list(range(1,8)),value=min(7,max(1,(date.today()-date(2026,10,14)).days+1)))
    new=Q[(day-1)*10:day*10] if day<7 else Q[60:]
    prev=[q for q in Q[:(day-1)*10] if p.get(q['id'],2)<2]
    st.caption(f'День {day}: {len(new)} нових запитань'+(f' · {len(prev)} складних із попередніх днів' if prev else ''))
    candidates=prev+new
elif mode=='🔁 Повторення':
    filter_=st.selectbox('Що повторюємо?', ['Не знаю / з підказкою','Усе пройдене','Усі 69'])
    candidates=([q for q in Q if p.get(q['id']) in (0,1)] if filter_.startswith('Не знаю') else [q for q in Q if q['id'] in p] if filter_=='Усе пройдене' else Q)
elif mode=='🎫 Білет: 5 запитань':
    if st.button('🎲 Згенерувати новий білет',use_container_width=True) or not st.session_state.ticket:
        st.session_state.ticket=random.sample(list(QMAP),5)
        st.session_state.ticket_answers=set()
    st.info('Спочатку дайте усну відповідь на всі п’ять запитань. Підказки відкривайте лише після спроби.')
    for i,qid in enumerate(st.session_state.ticket,1):
        q=QMAP[qid]
        st.markdown(f'**{i}. {q["question"]}**')
        with st.expander('Перевірити відповідь'):
            st.markdown('**Опорна схема:** '+' → '.join(q['cues']))
            st.markdown('**Відповідь для усного іспиту:**')
            st.write(q['study_answer'])
            if q['missing']:st.warning('В оригінальному документі немає відповіді. Уточніть її у відповідальної особи.')
            with st.expander('Повна відповідь із документа'):
                st.write(q['answer'] or 'Відповідь відсутня в документі.')
    st.stop()
else:
    term=st.text_input('Пошук у запитаннях')
    candidates=[q for q in Q if term.casefold() in q['question'].casefold()]

if not candidates:
    st.info('Тут поки немає запитань. Спробуйте інший режим або фільтр.')
    st.stop()
if mode=='📚 Довідник':
    qid=st.selectbox('Запитання',options=[q['id'] for q in candidates],format_func=lambda i:f'{i}. {QMAP[i]["question"]}')
    q=QMAP[qid]
else:
    q=candidates[st.session_state.cursor%len(candidates)]
    st.caption(f'Картка {st.session_state.cursor%len(candidates)+1} із {len(candidates)}')
st.subheader(f'{q["id"]}. {q["question"]}')
if q['missing']:st.warning('У вихідному документі немає відповіді. Потрібно уточнити у службі охорони праці.')

if mode=='📚 Довідник':
    reveal=3
else:
    st.markdown('**Етап 1.** Спробуйте пригадати відповідь уголос. Якщо важко — відкрийте підказку.')
    c1,c2,c3=st.columns(3)
    if c1.button('🔑 Ключові слова',use_container_width=True):st.session_state.reveal=max(1,st.session_state.reveal)
    if c2.button('🗣️ Відповідь',use_container_width=True):st.session_state.reveal=max(2,st.session_state.reveal)
    if c3.button('🙈 Сховати',use_container_width=True):st.session_state.reveal=0
    reveal=st.session_state.reveal
if reveal>=1:
    st.markdown('**Етап 2. Опорна схема — назвіть кожен пункт своїми словами:**')
    st.markdown(' → '.join(f'**{x}**' for x in q['cues']))
if reveal>=2:
    st.markdown('**Етап 3. Зразок усної відповіді:**')
    st.write(q['study_answer'])
if reveal>=3 or reveal>=2:
    with st.expander('📄 Повна відповідь із документа (для перевірки деталей)'):
        st.write(q['answer'] or 'В оригінальному документі відповіді немає.')
if mode!='📚 Довідник':
    st.markdown('**Етап 4. Оцініть, як вдалося розповісти вголос:**')
    a,b,c=st.columns(3)
    if a.button('😕 Не знаю',use_container_width=True):assess(q['id'],0);st.rerun()
    if b.button('💡 З підказкою',use_container_width=True):assess(q['id'],1);st.rerun()
    if c.button('✅ Знаю',use_container_width=True):assess(q['id'],2);st.rerun()
    if st.button('Пропустити →',use_container_width=True):advance();st.rerun()

st.divider()
st.markdown('**Збереження прогресу**')
st.caption('Результати закодовані в адресі сторінки. Після оцінювання збережіть нову адресу в закладках, щоб продовжити з того самого місця. Якщо відкрити початкове посилання, прогрес не відновиться. Не надсилайте посилання з прогресом стороннім.')
st.download_button('⬇️ Резервна копія прогресу',data=json.dumps(p,ensure_ascii=False,indent=2),file_name='miy_ispyt_progress.json',mime='application/json')
up=st.file_uploader('Відновити прогрес із резервної копії',type=['json'])
if up is not None:
    try:
        restored=json.load(up)
        restored={int(k):int(v) for k,v in restored.items() if int(k) in QMAP and int(v) in (0,1,2)}
        if st.button('Відновити з файлу'):
            store_progress(restored);st.rerun()
    except (ValueError,TypeError,AttributeError):st.error('Неправильний формат файлу.')
st.caption('Навчальні відповіді стисло переказують наданий документ. Вони не є незалежною перевіркою законодавства чи корпоративних правил.')
