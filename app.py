import streamlit as st
import json
import logging
import time
from logging.handlers import RotatingFileHandler
from main import process_pdf, final_summary,generate_quiz_json,solve_question,extract_image_text,final_summary_custom,extract_web_text

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
st.set_page_config(
    page_title="StudyMate",
    page_icon="📚",
    layout="wide"
)
st.title("📚 StudyMate - AI Learning Assistant")
st.markdown(custom_css, unsafe_allow_html=True)
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


logger.info("App started")
def reset_session():
    keys_to_reset = [
        "process_pdf",
        "uploaded_file_names",
        "final_summary",
        "quiz_data",
        "last_signature"
    ]
    logger.info("call reset session!!!")
    web_url =''
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
    logger.info("call radio_change_callback!!!")
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


if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
    
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


left_column,middle_column, right_column = st.columns([0.2,0.2, 0.6])

# subject select
with left_column:
    selected_subjectoption = st.selectbox(
    "What subject you like to study?", # The label for the dropdown
    options_list,                         # The list of available options
    index=None,                         # No initial selection
    placeholder=default_sel,
    key="subject_select",
    on_change=reset_session
)

# mode select
with middle_column:
    mode = st.selectbox(
    "Learning Mode",
    [
        "Standard Study",
        "Exam Preparation",
        "Quick Summary",
        "Deep Understanding",
        "Custom"
    ],
    index=None,                         # No initial selection
    placeholder=default_sel,
    key="mode_select"
)

#custom prompt select
if mode == 'Custom':
    with right_column:
        user_prompt = st.text_area(
        "Custom Learning Instruction (optional)",
        placeholder="Example: Focus on key definitions and generate exam-style questions"
    )

#get subject value from json data and use it as key to prompt json obj
try:     
    index_position = options_list.index(selected_subjectoption)
    subject = options_values[index_position]
  
    #when subject changes, file upload reset, also other session obj
    if subject != st.session_state.subject:
        st.session_state.subject = subject

        # Reset uploader
        st.session_state.uploader_key += 1
        
        # Clear other states
        st.session_state.pop("process_pdf", None)
        st.session_state.pop("final_summary", None)
        st.session_state.pop("quiz_data", None)
except ValueError:
    print(f"'{selected_subjectoption}' is not found in the list.")
        

rowtwo_column1,rowtwo_column2,row32 = st.columns([0.2, 0.4,0.4],vertical_alignment="center")

with rowtwo_column1:
    input_type = st.radio(
        "Choose input source",
        ["Upload Files", "Web URL"],
        on_change=radio_change_callback # Specify the callback function
    )
#file upload 
with rowtwo_column2:
    if input_type == "Upload Files":
        web_url=''
        uploaded_files = st.file_uploader(
            "Upload learning material (1 PDF file or miltiple image files)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.uploader_key}"
        )
        if uploaded_files:
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
    print("session changed")
    reset_session()
    if input_type == "Upload Files" and uploaded_files:

        st.session_state.last_signature = signature
        print (f"check uploaded_files {uploaded_files}")
        full_text = ""
        if "process_pdf" not in st.session_state:

            logger.debug(f"inside  uploaded_files {filetype} and subject: {st.session_state.subject}")
            with st.spinner("Processing upload and generating learning materials..."):
                start = time.time()
                if filetype == "pdf":
                    full_text = process_pdf(uploaded_files[0],st.session_state.subject)
                elif filetype == "image":
                    full_text = "\n".join(all_pages_img)
            logger.info(f"process_pdf time take in {time.time()-start:.2f}s")
            print(f"process_pdf time take in {time.time()-start:.2f}s")
            st.session_state.process_pdf = full_text
    if input_type == "Web URL" and web_url:

        logger.debug(f"web url entered: {web_url}")
        print(f"web url entered: {web_url}")
        full_text = extract_web_text(web_url)
        print(f"web url extract text : {full_text}")
        if full_text:
            st.session_state.process_pdf = full_text
        else:
            st.session_state.process_pdf = "can't  extract from web page."
            
if  st.session_state.get('subject') and "process_pdf" in st.session_state and ((input_type == "Upload Files" and uploaded_files) or (input_type == "Web URL" and web_url)):
    logger.debug(f"pipeline process: {st.session_state.subject}")
    print(f"pipeline process: {st.session_state.subject}")
    if input_type == "Web URL" and st.session_state.process_pdf == "can't  extract from web page.":
        st.session_state.final_summary = "can't extract from this url,please use other web data."
        st.session_state.mode = mode
        st.session_state.quiz_data = []
    else:
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
        quiz_data = generate_quiz_json(st.session_state.subject,st.session_state.process_pdf)
        st.session_state.quiz_data = quiz_data
def render_quiz(quiz_data):

    for i, q in enumerate(quiz_data):

        st.write(f"### Question {i+1}")
        st.write(q["question"])
        for opt in q["options"]:
            st.write(opt)

        with st.expander("👁 Reveal Answer"):
            st.write(f"Correct Answer: {q['answer']}")
            st.write(q["explanation"])
        st.divider()
                   
   
tab1, tab2, tab3 = st.tabs(["Summary", "Quiz", "Solve a Question"])   

with tab1:
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

with tab2:
    st.subheader("Generated Quiz") 
      
    if st.button("Regenerate Quiz"):
        if st.session_state.process_pdf:
           
            quiz_data = generate_quiz_json(st.session_state.subject,st.session_state.process_pdf)
            st.session_state.quiz_data = quiz_data
            logger.debug(f"Regenerate quiz data: {quiz_data}")
            render_quiz(st.session_state.quiz_data)
    elif st.session_state.get('quiz_data'):
        render_quiz(st.session_state.quiz_data) 


with tab3:
    st.subheader("Ask a Question")
    user_question = st.text_area("Enter your question")

    if st.button("Get Answer"):
        if user_question.strip() != "":
            with st.spinner("Thinking..."):
                answer = solve_question(st.session_state.subject,st.session_state.process_pdf, user_question)
            st.write(answer)
        else:
            st.warning("Please enter a question.")



