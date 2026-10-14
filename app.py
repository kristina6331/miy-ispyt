import json
import random
import re
from datetime import date
from pathlib import Path
import streamlit as st

st.set_page_config(page_title='Мій іспит 💛',page_icon='🌿',layout='centered')
st.markdown('''<style>
.block-container{max-width:830px;padding-top:1.1rem;padding-bottom:4rem}
h1{font-size:2rem!important}h2{font-size:1.42rem!important;line-height:1.4!important}
div.stButton>button{border-radius:14px;min-height:48px;font-weight:550}
[data-testid="stSidebar"]{background:#f5f6fa}
.lesson-box{border:1px solid #e4e8ed;border-radius:16px;padding:14px 17px;margin:9px 0;background:rgba(130,150,170,.045)}
.lesson-head{font-weight:750;font-size:1.06rem;margin-bottom:7px}
.lesson-body{font-size:1rem;line-height:1.65}
.anchor{font-weight:800;color:inherit;background:rgba(250,204,21,.23);border-radius:4px;padding:0 2px}
.small-note{color:#667085;font-size:.88rem}
@media(max-width:600px){.block-container{padding-left:1rem;padding-right:1rem}h1{font-size:1.75rem!important}div[data-testid="stHorizontalBlock"]{gap:.35rem}}
</style>''',unsafe_allow_html=True)
Q=json.loads(Path(__file__).with_name('questions.json').read_text(encoding='utf-8'))
QMAP={q['id']:q for q in Q}

# URL is a portable save state. Save/bookmark it after each session, or download a backup.
def read_progress():
    try:
        data=json.loads(st.query_params.get('progress','{}'))
        return {int(k):int(v) for k,v in data.items() if int(k) in QMAP and int(v) in (0,1,2)}
    except (ValueError,TypeError,AttributeError):return {}
def store_progress(p):
    st.query_params['progress']=json.dumps(p,ensure_ascii=False,separators=(',',':'))
def next_card():
    st.session_state.cursor+=1
    st.session_state.show_plan=False
    st.session_state.show_answer=False
    st.session_state.show_original=False
def assess(qid,level):
    p=read_progress();p[qid]=level;store_progress(p);next_card()
for key,value in [('cursor',0),('show_plan',False),('show_answer',False),('show_original',False),('ticket',[]),('ticket_reveal',set()),('last_mode',None)]:
    if key not in st.session_state:st.session_state[key]=value

# Important terms are emphasized in the concise answer, but the words are never changed.
ANCHOR_WORDS=r'''BPS|Bunge|Near Miss|Stop Work|LOTO|HACCP|OPRP|PRP|CCP|Stop Ship|BEUSS|Н-1|ЗІЗ|СЛР|Пенсійний фонд|профспілк\w*|робітник\w*|службовц\w*|працівник\w*|роботодавц\w*|нещасн\w*|комісі\w*|інструктаж\w*|наряд\w*|допуск\w*|відсторон\w*|випробуван\w*|строк\w*|огляд\w*|штраф\w*|відповідальн\w*|безпек\w*|небезпек\w*|ризик\w*|заземлен\w*|ізоляці\w*|вимкнут\w*|зупин\w*|повідом\w*|перевір\w*|контрол\w*|реєстраці\w*|профілактик\w*|захис\w*|пожеж\w*|вогнегасник\w*|евакуаці\w*|відход\w*|маркуван\w*|продукці\w*|шкідник\w*|місяц\w*|рок\w*|годин\w*|відсотк\w*|[0-9]+(?:[,.][0-9]+)?\s*(?:%|м|В|рок\w*|місяц\w*|годин\w*|хвилин\w*)?'''
anchor_re=re.compile(r'(?<!\w)(?:'+ANCHOR_WORDS+r')(?!\w)',re.I)

def mark(text):
    import html
    chunks=[];last=0
    for m in anchor_re.finditer(text):
        chunks.append(html.escape(text[last:m.start()]));chunks.append('<span class="anchor">'+html.escape(m.group())+'</span>');last=m.end()
    chunks.append(html.escape(text[last:]))
    return ''.join(chunks).replace('\n','<br>')

def manual_mark(text):
    import html
    return re.sub(r'\*\*(.+?)\*\*',lambda m:'<span class="anchor">'+html.escape(m.group(1))+'</span>',html.escape(text))

def lesson(q):
    st.markdown('#### 📖 Вивчаємо маленькими частинами')
    st.caption('Не треба вчити все одразу. Прочитай кожну частину й запам’ятай слова, виділені жовтим.')
    if q['missing']:
        st.warning('У наданому документі немає відповіді. Потрібен офіційний перелік ПНВ від служби охорони праці.')
        return
    for i,(prompt,block) in enumerate(zip(q['guide_questions'],q['learning_blocks']),1):
        st.markdown('<div class="lesson-box"><div class="lesson-head">'+str(i)+'. '+prompt+'</div><div class="lesson-body">'+manual_mark(block)+'</div></div>',unsafe_allow_html=True)
    st.markdown('#### 🧠 Згадуємо за планом')
    st.caption('Спробуй відповісти на ці маленькі запитання без тексту вище.')
    for i,prompt in enumerate(q['guide_questions'],1):
        st.markdown(f'**{i}. {prompt}**')
    with st.expander('🔑 Якщо забула — підказати опорні слова'):
        for prompt,cue in zip(q['guide_questions'],q['cues']):
            st.markdown(f'**{prompt}** — {cue}')
    st.markdown('#### 🗣 Коротка відповідь для іспиту')
    st.caption('Це приклад, як можна відповісти зв’язно своїми словами. Жовті слова — опори для пам’яті.')
    st.markdown('<div class="lesson-box"><div class="lesson-body">'+mark(q['study_answer'])+'</div></div>',unsafe_allow_html=True)

def memory_plan(q,answers=False):
    st.markdown('#### 🧠 Спробуй пригадати')
    st.caption('Подивись лише на запитання-підказки та розкажи відповідь уголос.')
    for i,(prompt,cue) in enumerate(zip(q['guide_questions'],q['cues']),1):
        st.markdown(f'**{i}. {prompt}**' + (f'  \n💡 **{cue}**' if answers else ''))

def original(q):
    with st.expander('📄 Повний текст із документа — перевірити подробиці'):
        st.text(q['answer'] or 'У документі немає відповіді.')

p=read_progress();known=sum(v==2 for v in p.values());started=len(p)
ENCOURAGEMENT=['Ти вже робиш важливу справу. Я в тебе вірю! ✨','Не треба знати все одразу. Маленькі кроки теж ведуть до мети. 🌷','Якщо сьогодні важко — це не означає, що не вийде. 💛','Ти молодець, що не здаєшся. 🌼','Можна хвилюватися і все одно добре відповісти. 💛','Своїми словами — це теж правильна відповідь, якщо зміст збережено. 🌿','Кожне повторення робить відповідь знайомішою. ⭐','Ти маєш право подумати, перш ніж відповісти. 🌸','Я пишаюся тим, як ти стараєшся. ❤️']
with st.sidebar:
    st.markdown('### 💛 Трошки підтримки')
    st.info(ENCOURAGEMENT[(date.today().toordinal()+st.session_state.cursor//3)%len(ENCOURAGEMENT)])
    st.caption('Вчися у своєму темпі. Перерва — теж частина підготовки.')
st.title('🌿 Мій іспит')
st.caption('69 запитань · короткі пояснення · підказки для пам’яті · білет із 5 запитань')
st.caption('💛 Ти молодець. Крок за кроком — і все вийде!')
st.info('💾 Після заняття збережи поточне посилання в закладки: саме в ньому зберігаються твої позначки. Або скачай резервну копію внизу сторінки.', icon='💛')
st.progress(known/69,text=f'Впевнено знаю: {known}/69 · уже спробувала: {started}/69')
mode=st.radio('Що робимо зараз?', ['📖 Вчу нове','🧠 Повторюю без підказок','🎫 Треную білет із 5 запитань','📚 Шукаю запитання'])
if st.session_state.last_mode!=mode:
    st.session_state.cursor=0;st.session_state.show_plan=False;st.session_state.show_answer=False;st.session_state.last_mode=mode

if mode=='📖 Вчу нове':
    day=st.select_slider('Який день навчання?',options=list(range(1,8)),value=min(7,max(1,(date.today()-date(2026,10,14)).days+1)))
    new=Q[(day-1)*10:day*10] if day<7 else Q[60:]
    st.caption(f'День {day}: {len(new)} запитань. Спочатку читай, потім розповідай уголос.')
    candidates=new
elif mode=='🧠 Повторюю без підказок':
    f=st.selectbox('Які запитання повторити?',['Ті, які ще складні','Уже вивчені','Усі 69'])
    candidates=([q for q in Q if p.get(q['id']) in (0,1)] if f=='Ті, які ще складні' else [q for q in Q if q['id'] in p] if f=='Уже вивчені' else Q)
elif mode=='🎫 Треную білет із 5 запитань':
    if st.button('🎲 Новий білет',use_container_width=True) or not st.session_state.ticket:
        st.session_state.ticket=random.sample(list(QMAP),5);st.session_state.ticket_reveal=set()
    st.caption('П’ять випадкових запитань, як на іспиті. Спробуй відповісти, а потім перевір себе.')
    for i,qid in enumerate(st.session_state.ticket,1):
        q=QMAP[qid]
        st.markdown(f'### {i}. {q["question"]}')
        with st.expander('🔍 Перевірити відповідь'):
            memory_plan(q,answers=True)
            st.markdown('**Коротка усна відповідь:**')
            st.markdown('<div class="lesson-box"><div class="lesson-body">'+mark(q['study_answer'])+'</div></div>',unsafe_allow_html=True)
            if q['missing']:st.warning('У документі немає затвердженої відповіді.')
            original(q)
        st.divider()
    st.stop()
else:
    term=st.text_input('Знайти слово в запитанні')
    candidates=[q for q in Q if term.casefold() in q['question'].casefold()]

if not candidates:
    st.info('Поки немає запитань для цього вибору. Спробуй інший розділ.')
    st.stop()
if mode=='📚 Шукаю запитання':
    qid=st.selectbox('Обери запитання',[q['id'] for q in candidates],format_func=lambda i:f'{i}. {QMAP[i]["question"]}')
    q=QMAP[qid]
else:
    q=candidates[st.session_state.cursor%len(candidates)]
    st.caption(f'Запитання {st.session_state.cursor%len(candidates)+1} із {len(candidates)}')
st.subheader(f'{q["id"]}. {q["question"]}')

if mode in ('📖 Вчу нове','📚 Шукаю запитання'):
    lesson(q)
else:
    st.caption('Спочатку відповідай уголос, не відкриваючи підказок.')
    if st.button('🧠 Потрібен план',use_container_width=True):st.session_state.show_plan=not st.session_state.show_plan
    if st.session_state.show_plan:memory_plan(q,answers=False)
    if st.button('🔑 Потрібні опорні слова',use_container_width=True):st.session_state.show_answer=not st.session_state.show_answer
    if st.session_state.show_answer:memory_plan(q,answers=True)
    with st.expander('📖 Перевірити коротку відповідь'):
        st.markdown('<div class="lesson-box"><div class="lesson-body">'+mark(q['study_answer'])+'</div></div>',unsafe_allow_html=True)
if mode!='📚 Шукаю запитання':
    original(q)
    st.markdown('#### 💛 Як вийшло?')
    st.caption('Це не оцінка. Вибери чесно, щоб знати, що повторити.')
    a,b,c=st.columns(3)
    if a.button('🌱 Ще вчу',use_container_width=True):assess(q['id'],0);st.rerun()
    if b.button('💡 З підказкою',use_container_width=True):assess(q['id'],1);st.rerun()
    if c.button('🌟 Сама!',use_container_width=True):assess(q['id'],2);st.rerun()
    if st.button('Далі →',use_container_width=True):next_card();st.rerun()
else:original(q)

st.divider()
with st.expander('💾 Як зберегти результати навчання'):
    st.caption('Прогрес записаний у поточному посиланні. Збережи його в закладках після занять або скачай резервну копію. Якщо відкривати початкову адресу, позначки не відновляться автоматично.')
    st.download_button('⬇️ Зберегти резервну копію',data=json.dumps(p,ensure_ascii=False,indent=2),file_name='miy_ispyt_progress.json',mime='application/json')
    up=st.file_uploader('Відновити з файлу',type=['json'])
    if up:
        try:
            restored=json.load(up);restored={int(k):int(v) for k,v in restored.items() if int(k) in QMAP and int(v) in (0,1,2)}
            if st.button('Відновити'):store_progress(restored);st.rerun()
        except (ValueError,TypeError,AttributeError):st.error('Неправильний файл.')
st.caption('Стислі відповіді створені на основі наданого документа. Це навчальний переказ, а не незалежна перевірка норм чи корпоративних процедур.')
