import streamlit as st
import json
import logging
import time

from logging.handlers import RotatingFileHandler
from main import process_pdf, final_summary,generate_quiz_json,solve_question,extract_image_text,final_summary_custom,extract_web_text,explain_question,generate_flashcards

# Custom CSS for Tabs
custom_css = """
<style>
    /* Style the tab container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }

    /* Style individual tabs */
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }

    /* Style the active tab */
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        color: #ff4b4b; /* Streamlit red */
        font-weight: bold;
    }
       
</style>
"""


row_column1,row_column2 = st.columns([0.4, 0.6],vertical_alignment="center")
st.set_page_config(
    page_title="AI StudySense",
    page_icon="📚",
    layout="wide"
)
with row_column1:
    st.title("📚 AI StudySense")
    #st.caption("Your AI-powered learning assistant, turn your study materials into **summaries, quizzes, and AI tutoring**.")
    st.markdown("""Turn your learning materials into:
    
• 📄 Smart summaries  &nbsp;• 🧠 Interactive quizzes  
• 🤖 &nbsp; &nbsp; AI tutoring  &nbsp; &nbsp;  &nbsp;&nbsp; &nbsp; &nbsp;&nbsp; &nbsp; &nbsp;   • 📖  Flashcards  
""")   
     

st.markdown(custom_css, unsafe_allow_html=True)
with row_column2:
    st.markdown("""
1️⃣ Select your subject  
2️⃣ Upload a PDF or images  
3️⃣ Choose learning mode  
4️⃣ Study using summaries, quizzes, or ask questions
""")
logger = logging.getLogger()


if not logger.handlers:

    handler = RotatingFileHandler(
        "study_app.log",
        maxBytes=1_000_000,
        backupCount=3
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

# Silence noisy libraries
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfminer.psparser").setLevel(logging.WARNING)

def reset_session():
    keys_to_reset = [
        "process_pdf",
        "uploaded_file_names",
        "final_summary",
        "quiz_data",
        "last_signature",
        "flashcards"
    ]
    web_url =''
    st.session_state.text_area_content = ""
    st.session_state.regenerate_counter = 0
    st.session_state["expander_state"] = False
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

def get_input_signature(files, subject, url):
    logger.info("call get_input_signature!!!")
    file_names = sorted([f.name for f in files]) if files else []

    return str({
        "files": file_names,
        "subject": subject,
        "url": url
    })
    

def radio_change_callback():
    #st.session_state.radio_value_changed = True
    #st.write(f"Callback triggered. New value: {st.session_state.my_radio}")
    #logger.info("call radio_change_callback!!!")
    reset_session()
    
# Initialize session state variables if they don't exist
if "process_pdf" not in st.session_state:
    st.session_state.process_pdf = []

if "final_summary" not in st.session_state:
    st.session_state.final_summary = ""

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []

if "subject" not in st.session_state:
    st.session_state.subject = None
    
if "mode" not in st.session_state:
    st.session_state.mode = None

if "text_area_content" not in st.session_state:
    st.session_state.text_area_content = ""

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "flashcards" not in st.session_state:
    st.session_state.flashcards = []


# 1. Initialize session state
if "expander_state" not in st.session_state:
    st.session_state["expander_state"] = False  # Starts Close
    
with open('subjectoptiondata.json', 'r') as file:
    subject_data_list = json.load(file)

options_values = [d.get('value') for d in subject_data_list]
options_list = [d.get('name') for d in subject_data_list]
default_sel = "Select..."
#mode=''
#user_prompt=''
filetype = None
subject=''
web_url=''




with st.sidebar:

    st.header("Study Setup")

    selected_subjectoption = st.selectbox(
        "Subject",
        options_list,
        index=None,
        placeholder=default_sel,
        key="subject_select",
        on_change=reset_session
    )
    mode = st.radio(
    "Choose Learning Mode",
    [
        "📘 Standard Study",
        "🎯 Exam Preparation",
        "⚡ Quick Summary",
        "🧠 Deep Understanding",
        "✏️ Custom"
    ]
)


    if mode == "Custom":
        user_prompt = st.text_area(
            "Custom Instruction",
            placeholder="Example: Focus on key definitions and generate exam-style questions"
        )



    input_type = st.radio(
        "Choose input source",
        ["Upload Files", "Web URL"],
        on_change=radio_change_callback # Specify the callback function
    )
    print(f"mode used: {mode} ") 
    if input_type == "Upload Files":
        web_url=''
        uploaded_files = st.file_uploader(
            "Upload learning material (1 PDF file or miltiple image files)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            #key=f"uploader_{st.session_state.uploader_key}"
        )
        if uploaded_files:
            #print(f"uploaded_files called ")
            for file in uploaded_files:
                current_files = sorted([f.name for f in uploaded_files])
                if "uploaded_file_names" not in st.session_state:
                    st.session_state.uploaded_file_names = current_files

                elif current_files != st.session_state.uploaded_file_names:
                    reset_session()
                    st.session_state.uploaded_file_names = current_files
            pdf_files = [f for f in uploaded_files if f.name.endswith(".pdf")]
            if len(pdf_files) > 1:
                logger.error("Only ONE PDF file is allowed.")
                st.stop()
            else:
                filetype = "pdf"

            all_pages_img=[]
            for file in uploaded_files:
                if file.name.endswith((".png", ".jpg", ".jpeg")):
                    filetype = "image"
                    textimg = extract_image_text(file)
                    all_pages_img.append(textimg)
                    
    elif input_type == "Web URL":
        web_url = st.text_input("Enter webpage URL")
        uploaded_files =[]




#get subject value from json data and use it as key to prompt json obj
try:     
    index_position = options_list.index(selected_subjectoption)
    subject = options_values[index_position]
  
    #when subject changes, file upload reset, also other session obj
    if subject != st.session_state.subject:
        st.session_state.subject = subject

        # Reset uploader
        #st.session_state.uploader_key += 1
        
        # Clear other states
        st.session_state.pop("process_pdf", None)
        st.session_state.pop("final_summary", None)
        st.session_state.pop("quiz_data", None)
except ValueError:
    print(f"'{selected_subjectoption}' is not found in the list.")
        


progress = st.progress(0)
 

# 2. Define the callback function
def close_expander():
    st.session_state["expander_state"] = False
    
logger.debug(f"st.session_state.subject  :{st.session_state.subject}")
signature = get_input_signature(uploaded_files, st.session_state.subject,web_url)
logger.debug(f"call to get_input_signature  :{signature}")
if "last_signature" not in st.session_state:
    st.session_state.last_signature = None

#mysubject = st.session_state.subject
logger.debug(f"st.session_state.subject :{st.session_state.subject}")
print(f"web_url used: {web_url} and input_type :{input_type}")

if st.session_state.subject !=None and st.session_state.get('subject') and signature != st.session_state.last_signature :
    logger.debug(f"call reset only subject is provieded {input_type}")
    #print(f"session changed ? subject :{st.session_state.subject} , session signature: {st.session_state.last_signature},signature {signature}")
    reset_session()
    if input_type == "Upload Files" and uploaded_files:

        st.session_state.last_signature = signature
        print (f"check uploaded_files {uploaded_files}")
        full_text = ""
        if "process_pdf" not in st.session_state:

            logger.debug(f"inside  uploaded_files {filetype} and subject: {st.session_state.subject}")
            with st.spinner("📄 Reading and analyzing document..."):
                start = time.time()
                if filetype == "pdf":
                    full_text = process_pdf(uploaded_files[0],st.session_state.subject)
                elif filetype == "image":
                    full_text = "\n".join(all_pages_img)
            logger.info(f"process_pdf time take in {time.time()-start:.2f}s")
            print(f"process_pdf time take in {time.time()-start:.2f}s")
            st.session_state.process_pdf = full_text
    if input_type == "Web URL" and web_url:
        st.session_state.last_signature = signature
        logger.info(f"web url entered: {web_url}")
        print(f"web url entered: {web_url}")
        full_text = extract_web_text(web_url)
        #print(f"web url extract text : {full_text}")
        if full_text:
            st.session_state.process_pdf = full_text
        else:
            st.session_state.process_pdf = "can't  extract from web page."
progress.progress(60)
          
if  st.session_state.get('subject') and "process_pdf" in st.session_state and ((input_type == "Upload Files" and uploaded_files) or (input_type == "Web URL" and web_url)):
    logger.debug(f"pipeline process: {st.session_state.subject}")
    print(f"pipeline process: {st.session_state.subject}")
    if input_type == "Web URL" and st.session_state.process_pdf == "can't  extract from web page.":
        st.session_state.final_summary = "can't extract from this url,please use other web data."
        st.session_state.mode = mode
        st.session_state.quiz_data = []
    if not st.session_state.get('final_summary'):
        print(f"need to call? final summary in session: {st.session_state.get('final_summary')}")
        start = time.time()
        if mode == 'Custom':
            #print (f"Custom :{mode} with user prompt :{user_prompt}")
            user_prompt = user_prompt if mode == "Custom" else ""
            summary = final_summary_custom(user_prompt,st.session_state.process_pdf)
        else:
            logger.debug(f"template {mode}")
            summary = final_summary(st.session_state.subject,st.session_state.process_pdf,mode) 
        logger.info(f"final_summary time take in {time.time()-start:.2f}s")
        print(f"final_summary time take in {time.time()-start:.2f}s")
        st.session_state.final_summary = summary
        st.session_state.mode = mode
        start = time.time()
        quiz_data = generate_quiz_json(st.session_state.subject,st.session_state.process_pdf,5)
        logger.info(f"generate_quiz_json_set in {time.time()-start:.2f}s")
        print(f"generate_quiz_json_set take in {time.time()-start:.2f}s")
        st.session_state.quiz_data = quiz_data
        flashcards = generate_flashcards(st.session_state.subject,st.session_state.process_pdf)
        st.session_state.flashcards = flashcards
        progress.progress(60)
    else:
        print("DONt need to call final summary, use existing one ")


 
def render_quiz(quiz_data):
    print (f"render_quiz expanded:  {st.session_state["expander_state"]}")
    for i, q in enumerate(quiz_data):

        st.write(f"### Question {i+1}")
        st.write(q["question"])
        for opt in q["options"]:
            st.write(opt)

        with st.expander("👁 Reveal Answer",expanded=st.session_state["expander_state"]):
            st.write(f"Correct Answer: {q['answer']}")
            st.write(q["explanation"])
        st.divider()
                   
   
 
tab1, tab2, tab3 , tab4 = st.tabs([
    "📄 Summary",
    "🧠 Quiz",
    "🤖 AI Tutor",
    "📖 Flashcards"
])
with tab1:
    if st.session_state.get('process_pdf'):
        st.subheader("Key Summary")
        if st.session_state.get('final_summary'):
            st.write(st.session_state.final_summary)
            st.download_button(
    label="Download",
    data=st.session_state.final_summary,
    file_name="summary.txt",
    mime="text",
    on_click="ignore", # This prevents the page refresh
    icon=":material/download:"
    )
        explain_text = st.text_area(
        "Paste text you want explained")

        if st.button("Explain this"):

            explanation = explain_question(
                st.session_state.subject,st.session_state.process_pdf,
                explain_text,
                "Explain this clearly for a student"
            )

            st.info(explanation)
with tab2:

    if st.session_state.get('process_pdf'):
        st.subheader("Generated Quiz") 
        #button_column,difficult_column,dummy_column = st.columns([2, 1,7], vertical_alignment="bottom") 
        #with button_column:      
        regbutton = st.button("Regenerate Quiz", on_click=close_expander)
        # difficult_column:   
        #    difficulty = st.selectbox("select quize difficulty level",["Easy","Medium","Hard"],label_visibility="hidden")
        if regbutton:
            start = time.time()
            quiz_data = generate_quiz_json(st.session_state.subject,st.session_state.process_pdf,60)
            st.session_state.quiz_data = quiz_data
            print(f"generate_quiz_json_set take in {time.time()-start:.2f}s")
            #logger.debug(f"Regenerate quiz data: {quiz_data}")
            #st.session_state["expander_state"]= False
            #render_quiz(st.session_state.quiz_data)
        if st.session_state.get('quiz_data'):
            render_quiz(st.session_state.quiz_data) 
    progress.progress(90)     
              
with tab3:
    if st.session_state.get('process_pdf'):
        st.subheader("Ask a Question")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        user_input = st.chat_input("Ask a question about the material")

        if user_input:
            st.session_state.messages.append({"role":"user","content":user_input})

            with st.chat_message("assistant"):
                answer = solve_question(st.session_state.subject,st.session_state.process_pdf, user_input,st.session_state.mode)
                st.write(answer)

            st.session_state.messages.append({"role":"assistant","content":answer})
        
    
with tab4:
    if st.session_state.get('process_pdf'):
       # if st.button("Generate Flashcards"):
        if "flashcards" in st.session_state:
         
            for card in st.session_state.flashcards:

                with st.expander(card["front"]):
                    st.write(card["back"])
progress.progress(100)    



